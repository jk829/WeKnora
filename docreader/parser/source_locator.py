"""来源定位：将解析后的 Markdown 范围映射回原始文件。

来源块格式为 {"start": int, "end": int, "locator": {...}}；
start/end 是正文中的 Unicode 码点偏移，end 不包含在范围内。
PDF 定位信息为 {"type": "pdf", "page": n}，可选 bbox: [x0, y0, x1, y1]，
坐标以页面左上角为原点、按显示页面尺寸归一化，便于任意缩放下绘制。
"""

from __future__ import annotations

import re
from collections import Counter
import statistics
import unicodedata
from typing import Iterable, List, Optional, Sequence, Tuple

# How far past the cursor a line is searched for, in normalized characters.
_SEARCH_WINDOW = 6000
# Lines shorter than this (normalized) are too ambiguous to place.
_MIN_KEY_CHARS = 2
# Lines shorter than this are placed only when their text is unique on the
# page: labels inside figures ("LLM", "EBAE") otherwise steal body offsets.
# Wide (CJK) characters count as four, since each carries about a word.
_SHORT_KEY_WEIGHT = 16

_LIST_START_RE = re.compile(
    r"^\s*(?:"
    r"\d{1,3}(?:\.\d{1,3}){0,4}[\.、．)）]?\s"  # 1  1.  8.14.11  2)
    r"|[（(]\d{1,3}[)）]"  # (1) （1）
    r"|[一二三四五六七八九十百]+[、．.]"  # 一、
    r"|[•·●○■□◆◇▪\-–*]\s"  # bullets
    r"|第[一二三四五六七八九十百零\d]+[章节条款部分篇]"  # 第三章
    r")"
)
_SENTENCE_END = tuple("。．.!?！？：:；;」』”)）")


def _fold(ch: str) -> str:
    """仅保留字母和数字，转为小写并折叠全角字符。"""
    if not ch.isalnum():
        return ""
    return unicodedata.normalize("NFKC", ch).lower()


def normalize_with_positions(text: str) -> Tuple[str, List[int]]:
    """将文本投影为仅含字母和数字的字符串。

    返回投影结果，以及其中每个字符在原 text 中的偏移。
    """
    out: List[str] = []
    pos: List[int] = []
    for i, ch in enumerate(text):
        value = unicodedata.normalize("NFKC", ch)
        folded = _fold(ch)
        if value in ".,:/+−-%‰<>=≤≥≠":
            before, after = i - 1, i + 1
            while before >= 0 and text[before] in " \t":
                before -= 1
            while after < len(text) and text[after] in " \t":
                after += 1
            prev = before >= 0 and text[before].isdigit()
            next_digit = after < len(text) and text[after].isdigit()
            semantic = ((value in ".,/:" and prev and next_digit)
                        or (value in "+-−" and next_digit)
                        or (value in "%‰" and prev)
                        or value in "<>=≤≥≠")
            if semantic:
                folded = value.replace("−", "-")
        for f in folded:
            out.append(f)
            pos.append(i)
    return "".join(out), pos


def normalize(text: str) -> str:
    return normalize_with_positions(text)[0]


def _key_weight(key: str) -> int:
    return sum(4 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in key)


def _column_cursor(boxes, idx: int, ends: List[Optional[int]]) -> Optional[int]:
    """返回 boxes[idx] 同一栏上方最近已定位文本行的结束偏移。"""
    x0, y0, x1, _ = boxes[idx]
    for j in range(idx - 1, max(-1, idx - 80), -1):
        if ends[j] is None:
            continue
        px0, py0, px1, _ = boxes[j]
        if px0 < x1 and x0 < px1 and py0 > y0:
            return ends[j]
    return None


def _numeric_safe_matches(text: str, key: str) -> List[int]:
    out = []
    if not key:
        return out
    start = 0
    while (at := text.find(key, start)) >= 0:
        before = text[at - 1] if at else ""
        end = at + len(key)
        after = text[end] if end < len(text) else ""
        left = key[0].isdigit() and bool(before) and (before.isdigit() or before in ".,:/+−-")
        right = key[-1].isdigit() and bool(after) and (after.isdigit() or after in ".,:/%‰")
        if not left and not right:
            out.append(at)
        start = at + 1
    return out


def locate_lines(
    page_text: str,
    line_texts: Sequence[str],
    boxes: Optional[Sequence[Tuple[float, float, float, float]]] = None,
) -> List[Optional[int]]:
    """查找各视觉行在页面文本中的起始偏移。

    依次从上次命中之后搜索，确保重复短语匹配到正确位置。提供 boxes
    （PDF 点坐标、左下角原点）时，优先从同栏上一行继续，因为左右栏的字形行
    可能交错到达。两种游标均未命中时从页首搜索，以容忍文本提取器与字形分组
    采用不同的分栏顺序。每行返回一个偏移，未找到时为 None。
    """
    norm, pos = normalize_with_positions(page_text)
    hits: List[Optional[int]] = []
    ends: List[Optional[int]] = []
    cursor = 0
    counts = Counter(normalize(line) for line in line_texts)
    occurrences = {key: _numeric_safe_matches(norm, key) for key in counts}
    for idx, line in enumerate(line_texts):
        key = normalize(line)
        if len(key) < _MIN_KEY_CHARS or len(occurrences[key]) != counts[key] or (
            _key_weight(key) < _SHORT_KEY_WEIGHT and len(occurrences[key]) > 1
        ):
            hits.append(None)
            ends.append(None)
            continue
        cursors = [cursor]
        if boxes is not None:
            column = _column_cursor(boxes, idx, ends)
            if column is not None:
                cursors.insert(0, column)
        at = -1
        for start_at in cursors:
            at = next((hit for hit in occurrences[key] if start_at <= hit <= start_at + _SEARCH_WINDOW), -1)
            if at >= 0:
                break
        if at < 0:
            at = occurrences[key][0] if len(occurrences[key]) == 1 else -1
            if at < 0:
                hits.append(None)
                ends.append(None)
                continue
        else:
            cursor = at + len(key)
        ends.append(at + len(key))
        start = pos[at]
        # Pull in leading punctuation or markup on the same text line
        # (brackets, "## ", list bullets) that normalization skipped.
        while start > 0 and page_text[start - 1] != "\n" and not page_text[start - 1].isalnum():
            start -= 1
        hits.append(start)
    return hits


class PageGeometry:
    """将 PDF 用户空间点坐标转换为显示页面的归一化坐标。"""

    def __init__(self, cropbox: Tuple[float, float, float, float], rotation: int = 0):
        left, bottom, right, top = cropbox
        self.left, self.bottom = min(left, right), min(bottom, top)
        self.width = abs(right - left) or 1.0
        self.height = abs(top - bottom) or 1.0
        self.rotation = int(rotation or 0) % 360

    def bbox(self, box: Tuple[float, float, float, float]) -> List[float]:
        x0, y0, x1, y1 = box
        # Unrotated, top-left origin.
        ux0 = (x0 - self.left) / self.width
        ux1 = (x1 - self.left) / self.width
        uy0 = 1.0 - (y1 - self.bottom) / self.height
        uy1 = 1.0 - (y0 - self.bottom) / self.height
        corners = [self._rotate(ux0, uy0), self._rotate(ux1, uy1)]
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        return [
            round(_clamp(min(xs)), 4),
            round(_clamp(min(ys)), 4),
            round(_clamp(max(xs)), 4),
            round(_clamp(max(ys)), 4),
        ]

    def _rotate(self, x: float, y: float) -> Tuple[float, float]:
        # Viewers display /Rotate clockwise.
        if self.rotation == 90:
            return 1.0 - y, x
        if self.rotation == 180:
            return 1.0 - x, 1.0 - y
        if self.rotation == 270:
            return y, 1.0 - x
        return x, y


def _clamp(v: float) -> float:
    return 0.0 if v < 0 else 1.0 if v > 1 else v


def _union(boxes: Iterable[Tuple[float, float, float, float]]):
    boxes = list(boxes)
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _line_gap(prev: dict, cur: dict) -> Optional[float]:
    """计算同栏内从 prev 向下到 cur 的垂直间距。"""
    px0, py0, px1, _ = prev["bbox"]
    cx0, _, cx1, cy1 = cur["bbox"]
    if cx1 < px0 or cx0 > px1 or cy1 > py0:
        return None
    return py0 - cy1


def _starts_paragraph(
    prev: dict, cur: dict, line_h: float, usual_gap: float, col_right: float
) -> bool:
    """判断 cur 是否在 prev 之后开启新的视觉段落。

    边界框使用左下角原点的 PDF 点坐标，向下阅读时 y 递减。
    usual_gap 为页面段内相邻行的典型间距，可适应双倍行距布局。
    """
    px0, py0, px1, _ = prev["bbox"]
    cx0, _, cx1, cy1 = cur["bbox"]
    if cx1 < px0 or cx0 > px1:
        return True  # moved to another column
    if cy1 > py0 + line_h * 0.5:
        return True  # went back up the page: a new column or region
    if py0 - cy1 > usual_gap * 1.5 + line_h * 0.3:
        return True  # vertical gap wider than the usual line spacing
    if _LIST_START_RE.match(cur["text"]):
        return True
    ends_sentence = prev["text"].rstrip().endswith(_SENTENCE_END)
    short = col_right - px1 > line_h * 2
    return ends_sentence and short


def page_blocks(
    page_text: str,
    offset: int,
    page_number: int,
    lines: Sequence[dict],
    geometry: Optional[PageGeometry],
) -> List[dict]:
    """生成正文中位于 offset 的单个文本页来源块。

    lines 为包含 text、bbox 的视觉行，bbox 使用 PDF 点坐标。
    先在 page_text 中定位文本行，再根据几何关系分段。每段仅覆盖已匹配的行，
    边界框取这些行的并集。未匹配间隙仅保留页码来源，不继承前一段的几何信息。
    """
    end = offset + len(page_text)
    page_only = {"type": "pdf", "page": page_number, "mapping": "exact"}
    if not page_text:
        return []
    placed = []
    if lines and geometry is not None:
        starts = locate_lines(
            page_text, [ln["text"] for ln in lines], [ln["bbox"] for ln in lines]
        )
        placed = sorted(
            (
                (at, ln)
                for at, ln in zip(starts, lines)
                if at is not None
            ),
            key=lambda item: item[0],
        )
    if not placed:
        return [{"start": offset, "end": end, "locator": dict(page_only)}]

    heights = [ln["bbox"][3] - ln["bbox"][1] for _, ln in placed if ln["bbox"][3] > ln["bbox"][1]]
    line_h = statistics.median(heights) if heights else 10.0
    gaps = [
        g
        for g in (_line_gap(a[1], b[1]) for a, b in zip(placed, placed[1:]))
        if g is not None and g >= 0
    ]
    usual_gap = min(statistics.median(gaps), line_h * 1.5) if gaps else line_h * 0.5

    norm, positions = normalize_with_positions(page_text)
    def line_end(at, line):
        key = normalize(line["text"])
        norm_start = next((i for i, p in enumerate(positions) if p >= at), len(norm))
        hit = norm.find(key, norm_start)
        if hit < 0:
            return at
        end_at = positions[hit + len(key) - 1] + 1
        while end_at < len(page_text) and not page_text[end_at].isalnum():
            if page_text[end_at] == "\n":
                return end_at + 1
            end_at += 1
        return end_at

    paragraphs: List[Tuple[int, List[dict]]] = []
    for at, ln in placed:
        ln = {**ln, "_source_end": line_end(at, ln)}
        if paragraphs:
            prev = paragraphs[-1][1][-1]
            col_right = max(p["bbox"][2] for p in paragraphs[-1][1])
            col_right = max(col_right, ln["bbox"][2])
            previous_end = prev["_source_end"]
            gap_is_empty = not normalize(page_text[previous_end:at])
            if gap_is_empty and not _starts_paragraph(prev, ln, line_h, usual_gap, col_right):
                paragraphs[-1][1].append(ln)
                continue
        paragraphs.append((at, [ln]))

    blocks: List[dict] = []
    cursor = 0
    for at, members in paragraphs:
        stop = members[-1]["_source_end"]
        if stop <= at:
            continue
        if at > cursor and page_text[cursor:at].strip():
            blocks.append({"start": offset + cursor, "end": offset + at, "locator": dict(page_only)})
        locator = dict(page_only)
        locator["bbox"] = geometry.bbox(_union(m["bbox"] for m in members))
        locator["source_id"] = f"pdf:{page_number}:{at}:{stop}"
        blocks.append({"start": offset + at, "end": offset + stop, "locator": locator})
        cursor = stop
    if cursor < len(page_text) and page_text[cursor:].strip():
        blocks.append({"start": offset + cursor, "end": end, "locator": dict(page_only)})
    return blocks
