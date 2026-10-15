import logging
from typing import Callable, Dict, List, Optional, Tuple, Type

from docreader.parser.base_parser import BaseParser
from docreader.parser.doc_parser import DocParser
from docreader.parser.docx2_parser import Docx2Parser
from docreader.parser.epub_parser import EPUBParser
from docreader.parser.excel_parser import ExcelParser
from docreader.parser.html_parser import HTMLParser
from docreader.parser.image_parser import ImageParser
from docreader.parser.markdown_parser import MarkdownParser
from docreader.parser.markitdown_parser import MarkitdownParser
from docreader.parser.mhtml_parser import MHTMLParser
from docreader.parser.opendataloader_parser import (
    OpenDataLoaderParser,
    opendataloader_available,
)
from docreader.parser.pdf_parser import PDFParser
from docreader.parser.xmind_parser import XMindParser

logger = logging.getLogger(__name__)

BUILTIN_ENGINE = "builtin"

# builtin 未原生实现的文件类型。请求的
# 引擎（包括空值或 builtin）无法解析时，转交类型默认引擎，
# 避免直接抛出 ValueError；PPT/PPTX/CSV 由 markitdown 处理。
_DEFAULT_ENGINE_BY_TYPE = {
    "ppt": "markitdown",
    "pptx": "markitdown",
    "csv": "markitdown",
}


class ParserEngineRegistry:
    """解析引擎注册表。

    每个引擎将文件扩展名映射到解析器类。请求的引擎不支持目标类型时，
    先尝试该类型的默认引擎，再回退到 builtin。
    """

    def __init__(self):
        self._engines: Dict[str, Dict[str, Type[BaseParser]]] = {}
        self._descriptions: Dict[str, str] = {}
        self._check_available: Dict[str, Callable[..., Tuple[bool, str]]] = {}
        self._unavailable_hint: Dict[str, str] = {}

    def register(
        self,
        name: str,
        file_types: Dict[str, Type[BaseParser]],
        description: str = "",
        check_available: Callable[..., Tuple[bool, str]] | None = None,
        unavailable_hint: str = "",
    ):
        self._engines[name] = file_types
        self._descriptions[name] = description
        if check_available is not None:
            self._check_available[name] = check_available
            self._unavailable_hint[name] = unavailable_hint
        logger.info(
            "Registered parser engine '%s' with file types: %s",
            name,
            ", ".join(file_types.keys()),
        )

    def get_parser_class(self, engine: str, file_type: str) -> Type[BaseParser]:
        """根据引擎和文件类型选择解析器类。

        请求引擎为空或不支持该类型时，先使用类型默认引擎（如 ppt 对应 markitdown），
        再回退到 builtin。仍无法解析时，抛出错误并列出支持该类型的引擎，便于调整配置。
        """
        ft = file_type.lower().lstrip(".")

        if engine and engine in self._engines:
            cls = self._engines[engine].get(ft)
            if cls:
                logger.info("Using engine '%s' for file type '%s'", engine, ft)
                return cls
            logger.info(
                "Engine '%s' does not support '%s', falling back",
                engine,
                ft,
            )

        default_engine = _DEFAULT_ENGINE_BY_TYPE.get(ft)
        if default_engine:
            cls = self._engines.get(default_engine, {}).get(ft)
            if cls:
                logger.info(
                    "Using default engine '%s' for file type '%s'",
                    default_engine,
                    ft,
                )
                return cls

        builtin = self._engines.get(BUILTIN_ENGINE, {})
        cls = builtin.get(ft)
        if cls:
            return cls

        supported = sorted(
            name for name, parsers in self._engines.items() if ft in parsers
        )
        engine_label = engine or BUILTIN_ENGINE
        if supported:
            raise ValueError(
                f"Unsupported file type {file_type!r} for engine {engine_label!r}. "
                f"Configure one of: {', '.join(supported)}"
            )
        raise ValueError(f"Unsupported file type: {file_type}")

    def list_engines(self, overrides: Optional[Dict[str, str]] = None) -> List[Dict]:
        """返回所有已注册引擎的元数据，包括可用性。

        参数：
            overrides: 租户级配置覆盖项，如 mineru_endpoint、mineru_api_key，
                会传递给各引擎的 check_available 函数。
        """
        result = []
        for name, parsers in self._engines.items():
            available = True
            unavailable_reason = ""
            check = self._check_available.get(name)
            if check is not None:
                try:
                    available, unavailable_reason = check(overrides)
                except Exception as e:
                    available = False
                    unavailable_reason = str(e) or self._unavailable_hint.get(name, "")
            if not available and not unavailable_reason:
                unavailable_reason = self._unavailable_hint.get(name, "不可用")
            result.append(
                {
                    "name": name,
                    "description": self._descriptions.get(name, ""),
                    "file_types": sorted(parsers.keys()),
                    "available": available,
                    "unavailable_reason": unavailable_reason,
                }
            )
        return result

    def get_engine_names(self) -> List[str]:
        return list(self._engines.keys())


def _build_default_registry() -> ParserEngineRegistry:
    """创建默认注册表，并注册所有已知引擎。"""
    reg = ParserEngineRegistry()

    _image_types = {
        ext: ImageParser for ext in ("jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp")
    }

    reg.register(
        BUILTIN_ENGINE,
        {
            "docx": Docx2Parser,
            "doc": DocParser,
            "pdf": PDFParser,
            "md": MarkdownParser,
            "markdown": MarkdownParser,
            "xlsx": ExcelParser,
            "xls": ExcelParser,
            "pptx": MarkitdownParser,
            "ppt": MarkitdownParser,
            "epub": EPUBParser,
            "html": HTMLParser,
            "htm": HTMLParser,
            "mhtml": MHTMLParser,
            "xmind": XMindParser,
            **_image_types,
        },
        description="内置解析引擎",
    )

    reg.register(
        "markitdown",
        {
            "md": MarkitdownParser,
            "markdown": MarkitdownParser,
            "pdf": MarkitdownParser,
            "docx": MarkitdownParser,
            "doc": MarkitdownParser,
            "pptx": MarkitdownParser,
            "ppt": MarkitdownParser,
            "xlsx": MarkitdownParser,
            "xls": MarkitdownParser,
            "csv": MarkitdownParser,
        },
        description="MarkItDown 解析引擎（微软 MarkItDown 库）",
    )

    reg.register(
        "opendataloader",
        {"pdf": OpenDataLoaderParser},
        description="OpenDataLoader PDF（版面分析，需 Java 11+）",
        check_available=lambda overrides: opendataloader_available(
            overrides, quick=True
        ),
        unavailable_hint="请安装 opendataloader-pdf 与 Java 11+",
    )

    # 注意：引擎列表由 Go 端注册表
    # docparser.ListAllEngines 管理。Python 的 list_engines 仅为
    # 兼容 gRPC ListEngines RPC 保留，Go 应用
    # 已不再调用；MinerU 引擎也由 Go 原生处理。

    return reg


registry = _build_default_registry()
