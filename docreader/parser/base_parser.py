# -*- coding: utf-8 -*-
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

from docreader.models.document import Document

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BaseParser(ABC):
    """解析器的抽象接口。

    轻量化重构后，BaseParser 只提取 Markdown 文本和原始图片引用。
    分块、图片存储、OCR 和视觉语言模型（VLM）图片描述由 Go 应用负责。
    """

    def __init__(
        self,
        file_name: str = "",
        file_type: Optional[str] = None,
        **kwargs,
    ):
        self.file_name = file_name
        self.file_type = file_type or os.path.splitext(file_name)[1].lstrip(".")

        logger.info(
            "Initializing parser for file=%s, type=%s",
            file_name,
            self.file_type,
        )

    @abstractmethod
    def parse_into_text(self, content: bytes) -> Document:
        """将文档字节内容解析为 Markdown 文本。

        返回：
            Document，其中 content 为 Markdown 字符串；可选的 images 字典
            将相对存储路径映射到 Base64 图片数据。
        """

    def parse(self, content: bytes) -> Document:
        """解析文档并返回 Markdown 正文与图片引用。

        分块、OCR 和 VLM 图片描述均交由 Go 端处理。
        """
        logger.info(
            "Parsing document with %s, bytes: %d",
            self.__class__.__name__,
            len(content),
        )
        document = self.parse_into_text(content)
        logger.info(
            "Extracted %d characters from %s",
            len(document.content),
            self.file_name,
        )
        return document
