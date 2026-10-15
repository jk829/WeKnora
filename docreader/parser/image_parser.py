import base64
import logging
import os

from docreader.models.document import Document
from docreader.parser.base_parser import BaseParser

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """独立图片文件解析器。

    返回 Markdown 图片引用，将原始图片数据放入 Document.images，
    由 Go 端 ImageResolver 或 main.py 的 _resolve_images 处理存储上传。
    """

    def parse_into_text(self, content: bytes) -> Document:
        logger.info("Parsing image file=%s, size=%d bytes", self.file_name, len(content))

        ext = os.path.splitext(self.file_name)[1].lower() or ".png"
        ref_path = f"images/{self.file_name}"

        text = f"![{self.file_name}]({ref_path})"
        images = {ref_path: base64.b64encode(content).decode()}

        return Document(content=text, images=images)
