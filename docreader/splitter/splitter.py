"""文本分块模块。

支持配置分块长度和重叠、通过正则保护公式/图片/链接/表格等内容，
跟踪标题以保留上下文，并在合并时处理重叠。
"""

import itertools
import logging
import re
from typing import Callable, Generic, List, Pattern, Tuple, TypeVar

from pydantic import BaseModel, Field, PrivateAttr

from docreader.splitter.header_hook import (
    HeaderTracker,
    header_column_mismatch,
)
from docreader.utils.split import split_by_char, split_by_sep

# 文本分块的默认配置。
# 与 internal/infrastructure/chunker/splitter.go 对齐：DefaultChunkOverlap = 80，
# DefaultChunkSize = 512。生产环境使用 Go 分块器；
# 此 Python 实现保留供仍依赖它的 docreader 边车使用。
DEFAULT_CHUNK_OVERLAP = 80  # 相邻分块的重叠字符数，约为分块长度的 15%。
DEFAULT_CHUNK_SIZE = 512  # 每个分块的最大字符数。

T = TypeVar("T")

logger = logging.getLogger(__name__)


class TextSplitter(BaseModel, Generic[T]):
    """支持保护模式和标题跟踪的文本分块器。

    在遵守块大小与重叠约束的同时，尽量保留公式、表格、代码块等结构，
    通过跟踪标题和合并片段保持上下文与文本完整性。
    """

    chunk_size: int = Field(description="The token chunk size for each chunk.")
    chunk_overlap: int = Field(
        description="The token overlap of each chunk when splitting."
    )
    separators: List[str] = Field(
        description="Default separators for splitting into words"
    )

    # 尽量保持正则匹配的内容完整。
    # 内容过长时仍会进一步切分。
    # 尝试将匹配的字符作为整体保留，如果太长则进一步分段
    protected_regex: List[str] = Field(
        description="Protected regex for splitting into words"
    )
    len_function: Callable[[str], int] = Field(description="The length function.")
    # 标题跟踪钩子的相关属性。
    # 标题跟踪钩子相关属性
    header_hook: HeaderTracker = Field(default_factory=HeaderTracker, exclude=True)

    # 用于保护特殊内容的预编译正则模式。
    _protected_fns: List[Pattern] = PrivateAttr()
    # 针对不同分隔符的切分函数。
    _split_fns: List[Callable] = PrivateAttr()

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = ["\n", "。", " "],
        protected_regex: List[str] = [
            # 数学公式：由 $$ 包围的 LaTeX 公式。
            r"\$\$[\s\S]*?\$\$",
            # 图片：Markdown 图片语法 ![alt](url)。
            r"!\[.*?\]\(.*?\)",
            # 链接：Markdown 链接语法 [text](url)。
            r"\[.*?\]\(.*?\)",
            # 表头：包含分隔行的 Markdown 表头。
            r"[ ]*(?:\|[^|\n]*)+\|[\r\n]+\s*(?:\|\s*:?-{3,}:?\s*)+\|[\r\n]+",
            # 表格正文：Markdown 表格数据行。
            r"[ ]*(?:\|[^|\n]*)+\|[\r\n]+",
            # 代码块头：包含语言标识的代码块起始行。
            r"```(?:\w+)[\r\n]+[^\r\n]*",
        ],
        length_function: Callable[[str], int] = lambda x: len(x),
    ):
        """初始化分块参数。

        参数：
            chunk_size: 每个分块的最大长度。
            chunk_overlap: 相邻分块的重叠长度，单位由 length_function 决定。
            separators: 按优先级排列的分隔符列表。
            protected_regex: 应尽量保持完整的内容正则模式。
            length_function: 长度计算函数，默认按字符数计算。

        异常：
            ValueError: chunk_overlap 大于 chunk_size。
        """
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"Got a larger chunk overlap ({chunk_overlap}) than chunk size "
                f"({chunk_size}), should be smaller."
            )

        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            protected_regex=protected_regex,
            len_function=length_function,
        )
        # 预编译所有保护模式，提高匹配效率。
        self._protected_fns = [re.compile(reg) for reg in protected_regex]
        # 为每个分隔符创建切分函数，最后以逐字符切分兜底。
        self._split_fns = [split_by_sep(sep) for sep in separators] + [split_by_char()]

    def split_text(self, text: str) -> List[Tuple[int, int, str]]:
        """切分文本，处理重叠并保护匹配的结构。

        参数：
            text: 输入文本。

        返回：
            (起始位置, 结束位置, 分块文本) 元组列表。
        """
        if text == "":
            return []

        # 步骤 1：按分隔符递归切分文本。
        splits = self._split(text)
        # 步骤 2：提取受保护内容的位置。
        protect = self._split_protected(text)
        # 步骤 3：调整片段边界，保持受保护内容完整。
        splits = self._join(splits, protect)

        # 确认拼接所有片段后可以重建原文。
        assert "".join(splits) == text

        # 步骤 4：将片段合并为带重叠的最终分块。
        chunks = self._merge(splits)

        # 步骤 5：校验分块并测试原文还原能力。
        # self._validate_chunks(chunks, text)

        return chunks

    def _split(self, text: str) -> List[str]:
        """按分隔符优先级递归切分，使片段小于块长度限制。

        依次尝试分隔符，找到可切分的方式后，递归处理仍然过长的片段。
        切分结果保留分隔符。

        参数：
            text: 待切分文本。

        返回：
            每项长度小于 chunk_size 的片段列表。
        """
        # 文本已足够短时直接返回。
        if self.len_function(text) <= self.chunk_size:
            return [text]

        # 按优先级尝试各切分函数，直到成功切分。
        splits = []
        for split_fn in self._split_fns:
            splits = split_fn(text)
            if len(splits) > 1:
                break

        # 保留足够短的片段，对过长片段递归切分。
        new_splits = []
        for split in splits:
            split_len = self.len_function(split)
            if split_len <= self.chunk_size:
                new_splits.append(split)
            else:
                # 递归切分超过大小限制的片段。
                new_splits.extend(self._split(split))
        return new_splits

    def _merge(self, splits: List[str]) -> List[Tuple[int, int, str]]:
        """将片段合并为带重叠和标题上下文的分块。

        持续添加片段，达到大小限制时开启新块，并保留上一块末尾的重叠。
        通过移除旧块前部片段控制长度，同时跟踪标题并在需要时补到新块开头。

        参数：
            splits: 待合并的文本片段列表。

        返回：
            (起始位置, 结束位置, 分块文本) 元组列表。
        """
        # 记录最终分块及其位置。
        chunks: List[Tuple[int, int, str]] = []

        # 当前正在构建的分块，由 (起始位置, 结束位置, 文本) 元组组成。
        cur_chunk: List[Tuple[int, int, str]] = []

        # 跟踪当前标题及分块长度。
        cur_headers, cur_len = "", 0
        # 跟踪在原文中的位置。
        cur_start, cur_end = 0, 0

        for split in splits:
            # 计算当前片段在原文中的位置。
            cur_end = cur_start + len(split)
            split_len = self.len_function(split)

            # 单个片段仍超限时记录警告，正常情况下 _split 后不应出现。
            if split_len > self.chunk_size:
                logger.error(
                    f"Got a split of size {split_len}, ",
                    f"larger than chunk size {self.chunk_size}.",
                )

            # 使用当前片段更新标题跟踪状态。
            self.header_hook.update(split)
            if self.header_hook.header_ended_this_unit and len(cur_chunk) > 0:
                chunks.append(
                    (
                        cur_chunk[0][0],
                        cur_chunk[-1][1],
                        "".join([c[2] for c in cur_chunk]),
                    )
                )
                cur_chunk = []
                cur_len = 0
            cur_headers = self.header_hook.get_headers()
            cur_headers_len = self.len_function(cur_headers)

            # 标题自身过长时跳过，避免分块超过限制。
            if cur_headers_len > self.chunk_size:
                logger.error(
                    f"Got headers of size {cur_headers_len}, ",
                    f"larger than chunk size {self.chunk_size}.",
                )
                cur_headers, cur_headers_len = "", 0

            # 检查加入当前片段后是否超过块大小限制。
            # 若超限，则结束当前块，并保留重叠内容创建新块。
            if cur_len + split_len + cur_headers_len > self.chunk_size:
                # 当前块有内容时，将其加入结果。
                if len(cur_chunk) > 0:
                    chunks.append(
                        (
                            cur_chunk[0][0],  # 首个元素的起始位置。
                            cur_chunk[-1][1],  # 最后一个元素的结束位置。
                            "".join([c[2] for c in cur_chunk]),  # 拼接后的文本。
                        )
                    )

                # 保留上一块末尾的重叠内容，开始新分块。
                # 持续移除旧分块的首元素，直到同时满足：
                # 1. 当前块长度小于重叠长度；
                # 2. 总长度小于块大小限制。
                while cur_chunk and (
                    cur_len > self.chunk_overlap
                    or cur_len + split_len + cur_headers_len > self.chunk_size
                ):
                    # 移除首元素以缩小重叠范围。
                    # 若首元素是补充的标题（start==end），也将其移除。
                    first_chunk = cur_chunk.pop(0)
                    cur_len -= self.len_function(first_chunk[2])

                    # 弹出真实正文后，其后可能紧跟补充的标题，
                    # 具体取决于之前的迭代；确认是标题后才一并弹出。
                    if cur_chunk and first_chunk[0] == first_chunk[1]:
                        first_chunk = cur_chunk.pop(0)
                        cur_len -= self.len_function(first_chunk[2])

                # 满足以下条件时，在新块开头补充标题：
                # 1. 存在标题；
                # 2. 标题和片段总长度不超过块大小限制；
                # 3. 当前片段尚未包含这些标题。
                if (
                    cur_headers
                    and split_len + cur_headers_len < self.chunk_size
                    and cur_headers not in split
                    and not header_column_mismatch(cur_headers, split)
                ):
                    next_start = cur_chunk[0][0] if cur_chunk else cur_start

                    cur_chunk.insert(0, (next_start, next_start, cur_headers))
                    cur_len += cur_headers_len

            # 将当前片段加入分块。
            cur_chunk.append((cur_start, cur_end, split))
            cur_len += split_len
            cur_start = cur_end

        # 处理最后一个分块，正常情况下至少存在一个。
        assert cur_chunk
        chunks.append(
            (
                cur_chunk[0][0],
                cur_chunk[-1][1],
                "".join([c[2] for c in cur_chunk]),
            )
        )

        return chunks

    def _split_protected(self, text: str) -> List[Tuple[int, str]]:
        """按正则模式提取需要保护的文本。

        参数：
            text: 待扫描文本。

        返回：
            各匹配项的 (起始位置, 受保护文本) 元组列表。
        """
        # 查找全部保护模式的匹配项。
        matches = [
            (match.start(), match.end())
            for pattern in self._protected_fns
            for match in pattern.finditer(text)
        ]
        # 先按起点升序、再按长度降序排序，以处理重叠匹配。
        matches.sort(key=lambda x: (x[0], -x[1]))

        res = []

        def fold(initial: int, current: Tuple[int, int]) -> int:
            """供累积计算使用的函数，用于过滤重叠匹配。"""
            # 仅处理起点不早于上一匹配终点的项。
            if current[0] >= initial:
                # 仅保护长度不超过块大小限制的内容。
                if current[1] - current[0] < self.chunk_size:
                    res.append((current[0], text[current[0] : current[1]]))
                else:
                    logger.warning(f"Protected text ignore: {current}")
            # 返回目前匹配到的最远结束位置。
            return max(initial, current[1])

        # 使用 accumulate 过滤重叠匹配。
        list(itertools.accumulate(matches, fold, initial=-1))
        return res

    def _join(self, splits: List[str], protect: List[Tuple[int, str]]) -> List[str]:
        """调整片段边界，确保受保护内容作为完整的独立片段。

        根据受保护子串合并或拆分原片段，将它们与相邻普通文本分离，
        处理部分粘连的情况，同时保持所有内容的原始顺序。

        参数：
            splits: _split() 返回的文本片段列表。
            protect: 受保护内容的 (位置, 文本) 列表。

        返回：
            已隔离受保护内容的片段列表。
        """
        j = 0  # 受保护内容列表的索引。
        point, start = 0, 0  # 跟踪当前在原文中的位置。
        res = []  # 合并后的片段结果列表。

        for split in splits:
            # 计算当前片段的结束位置。
            end = start + len(split)

            # 获取当前片段从游标开始的剩余内容。
            cur = split[point - start :]

            # 处理与当前片段重叠的所有受保护内容。
            while j < len(protect):
                p_start, p_content = protect[j]
                p_end = p_start + len(p_content)

                # 受保护内容位于当前片段之后时，继续下一个片段。
                if end <= p_start:
                    break

                # 添加受保护区域前面的普通内容。
                if point < p_start:
                    local_end = p_start - point
                    res.append(cur[:local_end])
                    cur = cur[local_end:]
                    point = p_start

                # 将受保护内容作为一个完整单元添加。
                res.append(p_content)
                j += 1

                # 跳过已归入受保护区域的内容。
                if point < p_end:
                    local_start = p_end - point
                    cur = cur[local_start:]
                    point = p_end

                # 当前片段已处理完时退出循环。
                if not cur:
                    break

            # 添加当前片段剩余的普通内容。
            if cur:
                res.append(cur)
                point = end

            # 继续处理下一个片段。
            start = end
        return res

    def _validate_chunks(
        self, chunks: List[Tuple[int, int, str]], original_text: str
    ) -> None:
        """校验分块顺序，并测试能否还原原文。

        检查起始位置是否递增，以及能否从分块恢复原文。
        失败时将调试信息保存到 /tmp/chunk_error_<timestamp>.md。

        参数：
            chunks: 待校验的 (起始位置, 结束位置, 文本) 列表。
            original_text: 切分前的原文。
        """
        import datetime

        errors = []

        # 校验 1：检查起始位置是否递增。
        for i in range(1, len(chunks)):
            prev_start = chunks[i - 1][0]
            curr_start = chunks[i][0]
            if curr_start < prev_start:
                error_msg = (
                    f"Chunk order error: chunk[{i}] start position ({curr_start}) "
                    f"is less than chunk[{i - 1}] start position ({prev_start})"
                )
                errors.append(error_msg)
                logger.error(error_msg)

        # 校验 2：测试原文还原。
        try:
            restored_text = self.restore_text(chunks)
            if restored_text != original_text:
                error_msg = (
                    f"Restoration failed: restored text differs from original. "
                    f"Original length: {len(original_text)}, "
                    f"Restored length: {len(restored_text)}"
                )
                errors.append(error_msg)
                logger.error(error_msg)

                # 查找首个差异位置。
                min_len = min(len(original_text), len(restored_text))
                diff_pos = -1
                for i in range(min_len):
                    if original_text[i] != restored_text[i]:
                        diff_pos = i
                        break

                if diff_pos >= 0:
                    context_start = max(0, diff_pos - 50)
                    context_end = min(len(original_text), diff_pos + 50)
                    errors.append(
                        f"First difference at position {diff_pos}:\n"
                        f"Original: {repr(original_text[context_start:context_end])}\n"
                        f"Restored: {repr(restored_text[context_start:context_end])}"
                    )
                elif len(original_text) != len(restored_text):
                    errors.append(
                        f"Texts match up to position {min_len}, but lengths differ"
                    )
        except Exception as e:
            error_msg = f"Restoration exception: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

        # 发现错误时，将调试信息保存到文件。
        if errors:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = f"/tmp/chunk_error_{timestamp}.md"

            with open(error_file, "w", encoding="utf-8") as f:
                f.write("# Chunk Validation Error Report\n\n")
                f.write(f"Timestamp: {timestamp}\n\n")

                f.write("## Errors\n\n")
                for error in errors:
                    f.write(f"- {error}\n\n")

                f.write("\n## Original Text\n\n")
                f.write(f"Length: {len(original_text)}\n\n")
                f.write("```\n")
                f.write(original_text)
                f.write("\n```\n\n")

                f.write("\n## Chunks Information\n\n")
                f.write(f"Total chunks: {len(chunks)}\n\n")
                for i, (start, end, chunk_text) in enumerate(chunks):
                    f.write(f"### Chunk {i}\n\n")
                    f.write(f"- Position: [{start}:{end}]\n")
                    f.write(f"- Length: {len(chunk_text)}\n")
                    f.write(f"- Content:\n\n```\n{chunk_text}\n```\n\n")

                try:
                    restored_text = self.restore_text(chunks)
                    f.write("\n## Restored Text\n\n")
                    f.write(f"Length: {len(restored_text)}\n\n")
                    f.write("```\n")
                    f.write(restored_text)
                    f.write("\n```\n")
                except Exception as e:
                    f.write("\n## Restoration Failed\n\n")
                    f.write(f"Error: {str(e)}\n")

            logger.error(f"Validation errors saved to: {error_file}")

    def restore_text(self, chunks: List[Tuple[int, int, str]]) -> str:
        """处理重叠和补充标题，从分块还原原文。

        按起始位置排序，结束位置用于同起点排序；跟踪已处理的最大结束位置，
        每块只提取尚未出现的正文后拼接。合并阶段补充的标题位置满足 start==end。

        参数：
            chunks: split_text() 返回的 (起始位置, 结束位置, 文本) 列表。

        返回：
            还原后的原文。

        示例：
            >>> splitter = TextSplitter(chunk_size=10, chunk_overlap=3)
            >>> chunks = splitter.split_text("Hello World!")
            >>> restored = splitter.restore_text(chunks)
            >>> assert restored == "Hello World!"
        """
        if not chunks:
            return ""

        # 按起始位置排序，起点相同时再按结束位置排序。
        sorted_chunks = sorted(chunks, key=lambda x: (x[1], x[0]))

        result_parts = []
        last_end = 0

        for start_pos, end_pos, chunk_text in sorted_chunks:
            result_parts.append(chunk_text[last_end - end_pos :])
            last_end = end_pos

        return "".join(result_parts)


if __name__ == "__main__":
    s = """
    这是一些普通文本。

    | 姓名 | 年龄 | 城市 |
    |------|------|------|
    | 张三 | 25   | 北京 |
    | 李四 | 30   | 上海 |
    | 王五 | 28   | 广州 |
    | 张三 | 25   | 北京 |
    | 李四 | 30   | 上海 |
    | 王五 | 28   | 广州 |

    这是文本结束。

"""

    sp = TextSplitter(
        chunk_size=200,
        chunk_overlap=10,
        separators=["\n\n", "\n", "。", "？", "！", "，", "；", "："],
    )
    ck = sp.split_text(s)
    for c in ck:
        print("------", len(c))
        print(c)
    pass
