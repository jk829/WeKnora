"""文档及其分块的数据结构。"""

import json
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """文档分块，包含文本内容与元数据。"""

    content: str = Field(default="", description="chunk text content")
    seq: int = Field(default=0, description="Chunk sequence number")
    start: int = Field(default=0, description="Chunk start position")
    end: int = Field(description="Chunk end position")
    images: List[Dict[str, Any]] = Field(
        default_factory=list, description="Images in the chunk"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="metadata fields",
    )

    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        """将分块转换为字典，并合并额外字段。"""

        data = self.model_dump()
        data.update(kwargs)
        data["class_name"] = self.__class__.__name__
        return data

    def to_json(self, **kwargs: Any) -> str:
        """将分块序列化为 JSON 字符串。"""
        data = self.to_dict(**kwargs)
        return json.dumps(data)

    def __hash__(self):
        """根据分块文本计算哈希值。"""
        return hash((self.content,))

    def __eq__(self, other):
        """按文本内容判断两个分块是否相等。"""
        return self.content == other.content

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs: Any):  # type: ignore
        """从字典创建分块，忽略 class_name 字段。"""
        if isinstance(kwargs, dict):
            data.update(kwargs)

        data.pop("class_name", None)
        return cls(**data)

    @classmethod
    def from_json(cls, data_str: str, **kwargs: Any):  # type: ignore
        """从 JSON 字符串创建分块。"""
        data = json.loads(data_str)
        return cls.from_dict(data, **kwargs)


class Document(BaseModel):
    """文档数据，包含正文、图片、分块及元数据。"""

    model_config = {"arbitrary_types_allowed": True}

    content: str = Field(default="", description="document text content")
    images: Dict[str, str] = Field(
        default_factory=dict, description="Images in the document"
    )

    chunks: List[Chunk] = Field(default_factory=list, description="document chunks")
    source_blocks: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Ranges of content mapped to positions in the original file: "
            '{"start": int, "end": int, "locator": {"type": "pdf", "page": 1, '
            '"bbox": [x0, y0, x1, y1]}}. Offsets are code point indices into '
            "content, end exclusive; ordinals are 1-based; bbox is fractions of "
            "the page with the origin at the top-left corner."
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="metadata fields",
    )

    def set_content(self, content: str) -> None:
        """设置文档正文。"""
        self.content = content

    def get_content(self) -> str:
        """获取文档正文。"""
        return self.content

    def is_valid(self) -> bool:
        return self.content != ""
