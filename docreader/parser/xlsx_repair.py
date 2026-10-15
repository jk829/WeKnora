"""在 openpyxl/pandas 读取前修复常见的 XLSX 打包问题。"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from typing import Callable, Dict, Iterable, Set

logger = logging.getLogger(__name__)

SST_PART = "xl/sharedStrings.xml"
_SST_OVERRIDE_RE = re.compile(
    r'<Override[^>]*PartName="[^"]*sharedStrings\.xml"[^>]*/>',
    re.IGNORECASE,
)
_SST_REL_RE = re.compile(
    r'<Relationship[^>]*Type="[^"]*sharedStrings"[^>]*/>',
    re.IGNORECASE,
)


def repair_xlsx_bytes(content: bytes) -> bytes | None:
    """返回修复后的 XLSX 字节；无需修复时返回 None。

    处理元数据引用 xl/sharedStrings.xml、但归档缺少该部件的工作簿。
    某些导出工具会产生这种文件；工作表仅使用内联字符串时，移除清单引用即可读取。
    """
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return None

    with zipfile.ZipFile(io.BytesIO(content), "r") as zin:
        names = _normalized_names(zin.namelist())
        sst_path = _find_shared_strings_path(names)
        if sst_path:
            if sst_path == SST_PART:
                return None
            return _rewrite_zip(
                zin, lambda files: _rename_shared_strings_part(files, sst_path)
            )
        if not _package_references_shared_strings(zin, names):
            return None
        if _worksheets_use_shared_string_cells(zin, names):
            return None
        return _rewrite_zip(zin, _strip_shared_strings_manifest)


# A data validation, or a scenario list, whose ``sqref`` openpyxl cannot parse
# aborts the whole workbook: openpyxl reads that attribute through a converter that
# turns the underlying range-parse ValueError into
# "TypeError: expected <class 'MultiCellRange'>" (#3599). Measured on openpyxl
# 3.1.5, a whole column (``C:C``), a whole row (``1:1``), a comma-separated
# list, ``#REF!`` and an out-of-bounds range all do it, in load_workbook and in
# pandas alike. Conditional formatting goes through the same converter, but
# openpyxl already catches it there and drops the rule with a warning, so it
# is not touched here. For scenarios the range sits on the ``<scenarios>``
# container, not on each ``<scenario>``, so the container is what goes.
_SQREF_ELEMENT_RE = re.compile(
    r"<(?P<tag>(?:\w+:)?(?:dataValidation|scenarios))\b[^>]*?(?:/>|>.*?</(?P=tag)>)",
    re.DOTALL,
)
_SQREF_ATTR_RE = re.compile(r'\bsqref="([^"]*)"')


def strip_unreadable_ranges_xlsx(content: bytes) -> bytes | None:
    """移除 openpyxl 无法解析范围的数据验证和方案列表。

    返回重写后的字节；所有范围均可读取时返回 None，保持原文件不变。
    数据验证只限制输入，方案保存未实际显示的假设值，均不改变当前单元格内容。
    移除这些异常元素不影响文本提取，保留则可能导致整份文档无法解析。
    """
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return None

    with zipfile.ZipFile(io.BytesIO(content), "r") as zin:
        sheets = sorted(
            name
            for name in _normalized_names(zin.namelist())
            if name.startswith("xl/worksheets/") and name.endswith(".xml")
        )
        dropped: Dict[str, int] = {}
        for name in sheets:
            sheet = zin.read(name).decode("utf-8", errors="replace")
            count = sum(1 for m in _SQREF_ELEMENT_RE.finditer(sheet) if _unreadable(m.group(0)))
            if count:
                dropped[name] = count
        if not dropped:
            return None
        logger.warning(
            "Dropping %d data validation/scenario range(s) openpyxl cannot parse: %s",
            sum(dropped.values()),
            ", ".join(f"{name} ({n})" for name, n in dropped.items()),
        )
        return _rewrite_zip(zin, lambda files: _strip_unreadable_ranges(files, dropped))


def _unreadable(element: str) -> bool:
    """判断 openpyxl 是否会在构建该元素的单元格范围时失败。"""
    from openpyxl.worksheet.cell_range import MultiCellRange

    match = _SQREF_ATTR_RE.search(element)
    if match is None:
        return False
    try:
        MultiCellRange(match.group(1))
    except Exception:  # noqa: BLE001 - mirrors openpyxl's own bare except
        return True
    return False


def _strip_unreadable_ranges(files: Dict[str, bytes], sheets: Dict[str, int]) -> Dict[str, bytes]:
    updated = dict(files)
    for name in sheets:
        sheet = updated[name].decode("utf-8")
        sheet = _SQREF_ELEMENT_RE.sub(
            lambda m: "" if _unreadable(m.group(0)) else m.group(0), sheet
        )
        updated[name] = sheet.encode("utf-8")
    return updated

def _normalized_names(namelist: Iterable[str]) -> Set[str]:
    return {name.replace("\\", "/") for name in namelist}


def _find_shared_strings_path(names: Set[str]) -> str | None:
    for name in names:
        if name.lower().endswith("sharedstrings.xml"):
            return name
    return None


def _package_references_shared_strings(
    zin: zipfile.ZipFile, names: Set[str]
) -> bool:
    content_types = "[Content_Types].xml"
    if content_types in names:
        ct = zin.read(content_types).decode("utf-8", errors="replace")
        if "sharedstrings.xml" in ct.lower():
            return True

    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path in names:
        rels = zin.read(rels_path).decode("utf-8", errors="replace")
        if "sharedstrings" in rels.lower():
            return True
    return False


def _worksheets_use_shared_string_cells(
    zin: zipfile.ZipFile, names: Set[str]
) -> bool:
    for name in names:
        if not name.startswith("xl/worksheets/") or not name.endswith(".xml"):
            continue
        sheet = zin.read(name).decode("utf-8", errors="replace")
        if re.search(r'\bt="s"', sheet):
            return True
    return False


def _rename_shared_strings_part(
    files: Dict[str, bytes], source_path: str
) -> Dict[str, bytes]:
    updated = dict(files)
    updated[SST_PART] = updated.pop(source_path)
    return updated


def _strip_shared_strings_manifest(files: Dict[str, bytes]) -> Dict[str, bytes]:
    updated = dict(files)
    ct_path = "[Content_Types].xml"
    if ct_path in updated:
        ct = updated[ct_path].decode("utf-8")
        ct = _SST_OVERRIDE_RE.sub("", ct)
        updated[ct_path] = ct.encode("utf-8")

    rels_path = "xl/_rels/workbook.xml.rels"
    if rels_path in updated:
        rels = updated[rels_path].decode("utf-8")
        rels = _SST_REL_RE.sub("", rels)
        updated[rels_path] = rels.encode("utf-8")
    return updated


def _rewrite_zip(
    zin: zipfile.ZipFile,
    transform: Callable[[Dict[str, bytes]], Dict[str, bytes]],
) -> bytes:
    files: Dict[str, bytes] = {}
    for info in zin.infolist():
        name = info.filename.replace("\\", "/")
        files[name] = zin.read(info.filename)
    files = transform(files)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    return out.getvalue()


# The one stylesheet openpyxl reads (openpyxl.xml.constants.ARC_STYLE). Match
# it exactly: a suffix match also hits xl/richData/richStyles.xml (Excel 365
# in-cell images / data types), which carries no fills.
STYLES_PART = "xl/styles.xml"
_REPLACEMENT_FILL = b'<fill><patternFill patternType="none"/></fill>'
_FILLS_BLOCK_RE = re.compile(rb"<fills\b[^>]*>.*?</fills>", re.S)
# Case-insensitive so wrong-case <Fill>…</Fill> entries are caught too.
_FILL_ELEMENT_RE = re.compile(rb"<fill\s*/>|<fill\s*>.*?</fill\s*>", re.S | re.I)
# A fill openpyxl can deserialize starts (case-sensitively) with a
# patternFill or gradientFill child — everything else, including the
# self-closing <fill/>, is rejected by its sequence descriptor.
_WELL_FORMED_FILL_RE = re.compile(rb"<fill\s*>\s*<(?:patternFill|gradientFill)[\s/>]")


def sanitize_xlsx_styles(content: bytes) -> bytes | None:
    """修复 styles.xml 中 openpyxl 无法反序列化的填充样式。

    部分云文档、LabView、Acumatica ERP 等导出工具生成空 fill 元素，
    或其子元素既非 patternFill 也非 gradientFill，导致 openpyxl 抛出
    TypeError: expected <class 'openpyxl.styles.fills.Fill'>，从而两个解析引擎
    都无法读取 Excel 本身可正常打开的文件（#3637）。原位替换为无效果的
    patternFill，保持列表长度及所有 cellXf 的 fillId 引用稳定。无需修复时返回 None。

    此函数不抛出异常；内部失败时保留原始字节，让调用方保留原错误原因，
    避免被修复过程的新错误覆盖。
    """
    try:
        return _sanitize_xlsx_styles(content)
    except Exception:
        logger.warning(
            "XLSX styles sanitize failed; passing original bytes through",
            exc_info=True,
        )
        return None


def _sanitize_xlsx_styles(content: bytes) -> bytes | None:
    if not zipfile.is_zipfile(io.BytesIO(content)):
        return None

    with zipfile.ZipFile(io.BytesIO(content)) as zin:
        if STYLES_PART not in zin.namelist():
            return None
        styles = zin.read(STYLES_PART)

        block = _FILLS_BLOCK_RE.search(styles)
        if block is None:
            return None

        fixed_count = 0

        def _fix(match: "re.Match[bytes]") -> bytes:
            nonlocal fixed_count
            if _WELL_FORMED_FILL_RE.match(match.group(0)):
                return match.group(0)
            fixed_count += 1
            return _REPLACEMENT_FILL

        patched_block = _FILL_ELEMENT_RE.sub(_fix, block.group(0))
        if fixed_count == 0:
            return None

        # Doubles as the recurrence meter for #3637: how often real uploads
        # carry non-conforming fills, and how many per file.
        logger.info(
            "Sanitized %d non-conforming fill(s) in XLSX styles.xml before parse",
            fixed_count,
        )

        patched = styles[: block.start()] + patched_block + styles[block.end():]
        return _rewrite_zip(zin, lambda files: {**files, STYLES_PART: patched})
