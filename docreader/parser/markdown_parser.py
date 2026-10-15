"""Markdown 解析模块。

提供表格格式规范化、Base64 图片提取与转换、图片路径替换等功能。
采用流水线依次处理表格和图片。
"""

import base64
import logging
import os
import re
import uuid
from typing import Dict, List, Match, Optional, Tuple

from docreader.models.document import Document
from docreader.parser.base_parser import BaseParser
from docreader.parser.chain_parser import PipelineParser
from docreader.utils import endecode

# Get logger object
logger = logging.getLogger(__name__)

_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
# Cells of a GFM alignment row as matched by the previous ``align_pattern``.
# Looser than ``_SEPARATOR_CELL``: any non-empty run of ``:``/``-`` qualifies.
_ALIGNMENT_CELL = re.compile(r"^[:-]+$")


class MarkdownTableUtil:
    """Utility class for formatting Markdown tables.

    此类通过以下方式标准化 Markdown 表格格式：
    -标准化列对齐标记（例如：---、:---:、---:）
    -在管道周围添加一致的间距 (|)
    -保留缩进级别
    -处理标题行和数据行

    Example:
        Input:  |姓名|年龄|城市|
                |:---|---:|:---:|
                |张三|25|北京|

        Output: | 姓名 | 年龄 | 城市 |
                | :--- | ---: | :---: |
                | 张三 | 25 | 北京 |
    """

    @staticmethod
    def _split_row_cells(row_line: str) -> List[str]:
        """将 Markdown 表格行拆成单元格，并保留空单元格。"""
        inner = row_line.strip()
        if not inner.startswith("|"):
            return []
        parts = inner.split("|")
        if parts and parts[0].strip() == "":
            parts = parts[1:]
        if parts and parts[-1].strip() == "":
            parts = parts[:-1]
        return [part.strip() for part in parts]

    @staticmethod
    def _is_table_row(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("|") and "|" in stripped[1:]

    @classmethod
    def _is_separator_row(cls, line: str) -> bool:
        cells = cls._split_row_cells(line)
        return bool(cells) and all(_SEPARATOR_CELL.match(cell) for cell in cells)

    @classmethod
    def _is_alignment_row(cls, line: str) -> bool:
        """检测 GFM 对齐行，与原有 align_pattern 规则一致。

        规则刻意比 _is_separator_row 宽松，后者要求每格至少三个连字符；
        这样可以保持 | - | - | 等输入的格式化结果不变。
        """
        cells = cls._split_row_cells(line)
        return bool(cells) and all(_ALIGNMENT_CELL.match(cell) for cell in cells)

    @classmethod
    def _is_empty_row(cls, line: str) -> bool:
        cells = cls._split_row_cells(line)
        return bool(cells) and all(cell == "" for cell in cells)

    @classmethod
    def _separator_row_for(cls, header_line: str) -> str:
        cells = cls._split_row_cells(header_line)
        return "| " + " | ".join("---" for _ in cells) + " |"

    @classmethod
    def _normalize_table_block(cls, block: List[str]) -> List[str]:
        """修复 MarkItDown 风格表格：移除伪前缀行，并补齐 GFM 分隔行。"""
        while block and cls._is_empty_row(block[0]):
            block.pop(0)
        if block and cls._is_separator_row(block[0]):
            block.pop(0)
        # GFM/marked need "| --- |" after the first row. Headerless Word tables
        # only have data rows after we strip the fake empty+separator prefix.
        if len(block) >= 2 and not cls._is_separator_row(block[1]):
            sep = cls._separator_row_for(block[0])
            block = [block[0], sep] + block[1:]
        return block

    def normalize_spurious_table_prefixes(self, content: str) -> str:
        """移除 MarkItDown 表格开头多余的空行或分隔行。"""
        lines = content.split("\n")
        out: List[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if not self._is_table_row(line):
                out.append(line)
                i += 1
                continue
            block: List[str] = []
            while i < len(lines) and self._is_table_row(lines[i]):
                block.append(lines[i])
                i += 1
            out.extend(self._normalize_table_block(block))
        return "\n".join(out)

    def format_table(self, content: str) -> str:
        """格式化正文中的全部 Markdown 表格。

        逐行处理且不使用正则；只有首尾均为 | 且至少有一个单元格的行才视为表格，
        避免畸形输入引发问题 #2768 中的灾难性回溯。扫描前将 CRLF/CR 规范化为 LF。
        参见 https://github.com/Tencent/WeKnora/issues/2768。

        参数：
            content: 包含表格的原始 Markdown 文本。

        返回：
            表格格式规范化后的 Markdown 文本。
        """

        def format_alignment_row(prefix: str, columns: List[str]) -> str:
            """规范化对齐行，并保留冒号对齐标记。"""
            processed = []
            for col in columns:
                # Preserve left alignment marker (:---)
                left_colon = ":" if col.startswith(":") else ""
                # Preserve right alignment marker (---:)
                right_colon = ":" if col.endswith(":") else ""
                processed.append(left_colon + "---" + right_colon)
            return prefix + "| " + " | ".join(processed) + " |"

        def format_data_row(prefix: str, columns: List[str]) -> str:
            """规范化表头行或数据行。"""
            return prefix + "| " + " | ".join(columns) + " |"

        # Unify CRLF/CR first so a trailing ``\r`` left by split("\n") cannot
        # be mistaken for "ends with |" via str.rstrip(), and so we do not
        # emit mixed line endings. Trailing newlines are preserved.
        unified = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = unified.split("\n")
        out: List[str] = []
        for line in lines:
            stripped = line.lstrip(" \t")
            # A row must both begin and end with a pipe to be a table row;
            # anything else is passed through unchanged. This also keeps
            # unclosed rows (the old regex's exponential worst case) cheap.
            # rstrip only spaces/tabs (old ``\|[\t ]*$``), not all whitespace.
            if stripped.startswith("|") and line.rstrip(" \t").endswith("|"):
                prefix = line[: len(line) - len(stripped)]
                columns = self._split_row_cells(line)
                # Lone "|" is not a table row: the old line_pattern required
                # opening *and* closing pipes. Formatting it to "|  |" would
                # let normalize_spurious_table_prefixes drop the line.
                if not columns:
                    out.append(line)
                elif self._is_alignment_row(line):
                    out.append(format_alignment_row(prefix, columns))
                else:
                    out.append(format_data_row(prefix, columns))
            else:
                out.append(line)
        return self.normalize_spurious_table_prefixes("\n".join(out))

    @staticmethod
    def _self_test():
        test_content = """
# 测试表格
普通文本---不会被匹配

## 表格1（无前置空格）

| 姓名   | 年龄  | 城市          |
|      :---------- | -------: | :------      |
| 张三 | 25 | 北京 |

## 表格3（前置4个空格+首尾|）
    |   产品   |   价格   |   库存   |
    | :-------------: | ----------- | :-----------: |
    | 手机 | 5999       | 100 |
"""
        util = MarkdownTableUtil()
        format_content = util.format_table(test_content)
        print(format_content)


class MarkdownTableFormatter(BaseParser):
    """Markdown 表格格式化解析器。

    统一文档中表格的空格和对齐标记。

    示例：
        >>> formatter = MarkdownTableFormatter()
        >>> content = b"|Name|Age|\n|---|---|\n|John|30|"
        >>> doc = formatter.parse_into_text(content)
        >>> print(doc.content)
        | Name | Age |
        | --- | --- |
        | John | 30 |
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table_helper = MarkdownTableUtil()

    def parse_into_text(self, content: bytes) -> Document:
        """解析并格式化 Markdown 表格。

        参数：
            content: 原始 Markdown 字节内容。

        返回：
            包含格式化表格正文的 Document。
        """
        # Decode bytes to string with automatic encoding detection
        text = endecode.decode_bytes(content)
        # Format all tables in the content
        text = self.table_helper.format_table(text)
        return Document(content=text)


class MarkdownImageUtil:
    """Markdown 图片处理工具。

    支持提取 Base64 内嵌图片和普通图片路径、将图片路径替换为新 URL，
    以及将 Base64 图片解码为二进制。
    支持格式：![alt](data:image/png;base64,iVBORw0...) 和 ![alt](path/to/image.png)。
    """

    def __init__(self):
        # Pattern to match base64 embedded images
        # Captures: (1) alt text, (2) image format, (3) base64 data
        # Alt text uses .*? (non-greedy) to allow literal ] (e.g. Windows paths).
        # MIME subtype uses [^;]+ to handle types with hyphens like x-emf.
        self.b64_pattern = re.compile(
            r"!\[(.*?)\]\(data:image/([^;]+);base64,([^\)]+)\)"
        )
        # Pattern to match regular image syntax (alt text allows ])
        self.image_pattern = re.compile(r"!\[(.*?)\]\(([^)]+)\)")
        # Pattern for replacing image paths
        self.replace_pattern = re.compile(r"!\[(.*?)\]\(([^)]+)\)")

    def extract_image(
        self,
        content: str,
        path_prefix: Optional[str] = None,
        replace: bool = True,
    ) -> Tuple[str, List[str]]:
        """从 Markdown 正文中提取图片路径。

        参数：
            content: 包含图片的 Markdown 文本。
            path_prefix: 可选的图片路径前缀。
            replace: 是否替换正文中的图片语法。

        返回：
            (处理后的文本, 图片路径列表)。

        示例：
            >>> util = MarkdownImageUtil()
            >>> text, images = util.extract_image("![logo](img/logo.png)")
            >>> print(images)
            ['img/logo.png']
        """
        # List to store extracted image paths
        images: List[str] = []

        def repl(match: Match[str]) -> str:
            """处理每个图片匹配项的替换函数。"""
            title = match.group(1)  # Alt text
            image_path = match.group(2)  # Image path

            # Add prefix if specified
            if path_prefix:
                image_path = f"{path_prefix}/{image_path}"

            images.append(image_path)

            # Keep original if replace is False
            if not replace:
                return match.group(0)

            # Replace image path with potentially prefixed path
            return f"![{title}]({image_path})"

        text = self.image_pattern.sub(repl, content)
        logger.debug(f"Extracted {len(images)} images from markdown")
        return text, images

    def extract_base64(
        self,
        content: str,
        path_prefix: Optional[str] = None,
        replace: bool = True,
    ) -> Tuple[str, Dict[str, bytes]]:
        """提取并解码 Markdown 中的 Base64 内嵌图片。

        为图片生成唯一文件名，可按需将正文中的内嵌数据替换为文件路径引用。

        参数：
            content: 包含 Base64 图片的 Markdown 文本。
            path_prefix: 生成路径的可选目录前缀。
            replace: 是否将 Base64 图片语法替换为文件路径。

        返回：
            (处理后的文本, 路径到图片字节的字典)。

        示例：
            >>> util = MarkdownImageUtil()
            >>> text = "![logo](data:image/png;base64,iVBORw0KGg...)"
            >>> new_text, images = util.extract_base64(text, "images")
            >>> print(new_text)
            ![logo](images/uuid.png)
            >>> print(len(images))
            1
        """
        # Dictionary mapping generated file paths to binary image data
        images: Dict[str, bytes] = {}

        def repl(match: Match[str]) -> str:
            """处理每个 Base64 图片匹配项的替换函数。"""
            title = match.group(1)  # Alt text
            img_ext = match.group(2)  # Image format (png, jpg, etc.)
            img_b64 = match.group(3)  # Base64 encoded data

            # Decode base64 string to bytes
            image_byte = endecode.encode_image(img_b64, errors="ignore")
            if not image_byte:
                logger.error(f"Failed to decode base64 image skip it: {img_b64}")
                return title  # Return just the alt text if decode fails

            # Generate unique filename with original extension
            image_path = f"{uuid.uuid4()}.{img_ext}"
            if path_prefix:
                image_path = f"{path_prefix}/{image_path}"
            images[image_path] = image_byte

            # Keep original base64 if replace is False
            if not replace:
                return match.group(0)

            # Replace base64 data with file path reference
            return f"![{title}]({image_path})"

        text = self.b64_pattern.sub(repl, content)
        logger.debug(f"Extracted {len(images)} base64 images from markdown")
        return text, images

    def replace_path(self, content: str, images: Dict[str, str]) -> str:
        """将 Markdown 中的图片路径替换为新 URL，常用于图片存储后的链接更新。

        参数：
            content: 包含图片引用的 Markdown 文本。
            images: 旧路径到新 URL 的映射。

        返回：
            更新图片 URL 后的 Markdown。

        示例：
            >>> util = MarkdownImageUtil()
            >>> content = "![logo](temp/img.png)"
            >>> mapping = {"temp/img.png": "https://cdn.com/img.png"}
            >>> result = util.replace_path(content, mapping)
            >>> print(result)
            ![logo](https://cdn.com/img.png)
        """
        # Track which paths were actually replaced
        content_replace: set = set()

        def repl(match: Match[str]) -> str:
            """处理每个图片匹配项的替换函数。"""
            title = match.group(1)  # Alt text
            image_path = match.group(2)  # Current image path

            # Only replace if path exists in mapping
            if image_path not in images:
                return match.group(0)  # Keep original

            content_replace.add(image_path)
            # Get new URL from mapping
            image_path = images[image_path]
            return f"![{title}]({image_path})" if image_path else title

        text = self.replace_pattern.sub(repl, content)
        logger.debug(f"Replaced {len(content_replace)} images in markdown")
        return text

    @staticmethod
    def _self_test():
        your_content = "test![](data:image/png;base64,iVBORw0KGgoAAAA)test"
        image_handle = MarkdownImageUtil()
        text, images = image_handle.extract_base64(your_content)
        print(text)

        for image_url, image_byte in images.items():
            with open(image_url, "wb") as f:
                f.write(image_byte)


class MarkdownImageBase64(BaseParser):
    """从 Markdown 中提取 Base64 图片的解析器。

    将内嵌图片替换为路径引用，原始数据放入 Document.images，
    由 Go 端 ImageResolver 或 main.py 的 _resolve_images 处理存储。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_helper = MarkdownImageUtil()

    def parse_into_text(self, content: bytes) -> Document:
        text = endecode.decode_bytes(content)
        text, img_b64 = self.image_helper.extract_base64(text, path_prefix="images")

        images: Dict[str, str] = {}
        for ipath, raw_bytes in img_b64.items():
            images[ipath] = base64.b64encode(raw_bytes).decode()

        logger.debug("Extracted %d base64 images from markdown", len(images))
        return Document(content=text, images=images)


class MarkdownParser(PipelineParser):
    """采用流水线处理的完整 Markdown 解析器。

    依次使用 MarkdownTableFormatter 规范化表格，
    再使用 MarkdownImageBase64 提取内嵌图片。每个阶段的输出作为下一阶段的输入。
    """

    _parser_cls = (MarkdownTableFormatter, MarkdownImageBase64)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.DEBUG)

    # Test the complete MarkdownParser pipeline
    your_content = "test![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgA)test"
    parser = MarkdownParser()

    # Parse content and display results
    document = parser.parse_into_text(your_content.encode())
    logger.info(document.content)
    logger.info(f"Images: {len(document.images)}, name: {document.images.keys()}")

    # Run individual utility tests
    MarkdownImageUtil._self_test()
    MarkdownTableUtil._self_test()
