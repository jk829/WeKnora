"""WeKnora 文档处理系统的解析器模块。

提供 Word（.doc、.docx）、PDF、Markdown、纯文本、图片及网页等格式
的内容提取能力。生产流程中的分块与后续索引由 Go 应用负责。
"""

from .doc_parser import DocParser
from .docx2_parser import Docx2Parser
from .excel_parser import ExcelParser
from .html_parser import HTMLParser
from .image_parser import ImageParser
from .markdown_parser import MarkdownParser
from .parser import Parser
from .pdf_parser import PDFParser
from .registry import ParserEngineRegistry, registry
from .web_parser import WebParser

# 导出公共类和模块。
__all__ = [
    "Docx2Parser",
    "DocParser",
    "PDFParser",
    "MarkdownParser",
    "ImageParser",
    "WebParser",
    "Parser",
    "ExcelParser",
    "HTMLParser",
    "ParserEngineRegistry",
    "registry",
]
