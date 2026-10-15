"""文档解析器组合模块。

提供两种职责链实现：
1. FirstParser：依次尝试多个解析器，直到首次成功。
2. PipelineParser：串联多个解析器，后一个处理前一个的输出。
"""

import logging
from typing import Dict, List, Tuple, Type

from docreader.models.document import Document
from docreader.parser.base_parser import BaseParser
from docreader.utils import endecode

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FirstParser(BaseParser):
    """依次尝试解析器，返回首个有效文档。

    若所有解析器都失败，则返回空 Document。

    用法：
        CustomParser = FirstParser.create(MarkdownParser, HTMLParser)
        parser = CustomParser()
        document = parser.parse_into_text(content_bytes)
    """

    # 需要实例化的解析器类元组。
    _parser_cls: Tuple[Type["BaseParser"], ...] = ()

    def __init__(self, *args, **kwargs):
        """根据配置的解析器类初始化 FirstParser。"""
        super().__init__(*args, **kwargs)

        # 将所有解析器类实例化。
        self._parsers: List[BaseParser] = []
        for parser_cls in self._parser_cls:
            parser = parser_cls(*args, **kwargs)
            self._parsers.append(parser)

    def parse_into_text(self, content: bytes) -> Document:
        """依次解析内容并返回首个成功的结果。

        参数：
            content: 待解析的原始字节。

        返回：
            首个有效 Document；全部失败时返回空 Document。
        """
        for p in self._parsers:
            logger.info(f"FirstParser: using parser {p.__class__.__name__}")
            try:
                document = p.parse_into_text(content)
            except Exception:
                logger.exception(
                    "FirstParser: parser %s raised exception; trying next parser",
                    p.__class__.__name__,
                )
                continue

            if document.is_valid():
                logger.info(f"FirstParser: parser {p.__class__.__name__} succeeded")
                return document
        return Document()

    @classmethod
    def create(cls, *parser_classes: Type["BaseParser"]) -> Type["FirstParser"]:
        """创建使用指定解析器的 FirstParser 子类。

        参数：
            *parser_classes: 按尝试顺序排列的 BaseParser 子类。

        返回：
            配置好解析器的新 FirstParser 子类。

        示例：
            CustomParser = FirstParser.create(MarkdownParser, HTMLParser)
            parser = CustomParser()
        """
        # 根据解析器名称生成便于识别的类名。
        names = "_".join([p.__name__ for p in parser_classes])
        # 动态创建包含解析器配置的新类。
        return type(f"FirstParser_{names}", (cls,), {"_parser_cls": parser_classes})


class PipelineParser(BaseParser):
    """按顺序串联多个解析器的流水线。

    每个解析器接收上一阶段的输出，各阶段图片累积后合并到最终文档。

    用法：
        CustomParser = PipelineParser.create(PreParser, MarkdownParser, PostParser)
        parser = CustomParser()
        document = parser.parse_into_text(content_bytes)
    """

    # 需要实例化并按顺序串联的解析器类元组。
    _parser_cls: Tuple[Type["BaseParser"], ...] = ()

    def __init__(self, *args, **kwargs):
        """根据配置的解析器类初始化 PipelineParser。"""
        super().__init__(*args, **kwargs)

        # 将所有解析器类实例化。
        self._parsers: List[BaseParser] = []
        for parser_cls in self._parser_cls:
            parser = parser_cls(*args, **kwargs)
            self._parsers.append(parser)

    def parse_into_text(self, content: bytes) -> Document:
        """通过解析器流水线处理内容。

        每个解析器处理上一阶段的输出，所有阶段的图片累积后合并到最终文档。

        参数：
            content: 待解析的原始字节。

        返回：
            所有阶段处理后的 Document，包含累积的图片。
        """
        # 累积各阶段解析器的图片和元数据。
        images: Dict[str, str] = {}
        metadata: Dict = {}
        document = Document()
        for p in self._parsers:
            logger.info(f"PipelineParser: using parser {p.__class__.__name__}")
            # 使用当前解析器处理内容。
            document = p.parse_into_text(content)
            # 将文档正文转回字节，供下一阶段解析器使用。
            content = endecode.encode_bytes(document.content)
            # 累积当前解析器的图片和元数据。
            images.update(document.images)
            metadata.update(document.metadata)
        # 将累积的图片和元数据合并到最终文档。
        document.images.update(images)
        document.metadata.update(metadata)
        return document

    @classmethod
    def create(cls, *parser_classes: Type["BaseParser"]) -> Type["PipelineParser"]:
        """创建按顺序串联指定解析器的 PipelineParser 子类。

        参数：
            *parser_classes: 按流水线顺序排列的 BaseParser 子类。

        返回：
            配置好解析器的新 PipelineParser 子类。

        示例：
            CustomParser = PipelineParser.create(PreprocessParser, MarkdownParser)
            parser = CustomParser()
        """
        # 根据解析器名称生成便于识别的类名。
        names = "_".join([p.__name__ for p in parser_classes])
        # 动态创建包含解析器配置的新类。
        return type(f"PipelineParser_{names}", (cls,), {"_parser_cls": parser_classes})


if __name__ == "__main__":
    from docreader.parser.markdown_parser import MarkdownParser

    # 示例：创建并使用包含 MarkdownParser 的 FirstParser。
    FpCls = FirstParser.create(MarkdownParser)
    lparser = FpCls()
    print(lparser.parse_into_text(b"aaa"))
