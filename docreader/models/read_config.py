from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    """为向后兼容保留的旧配置。

    轻量化重构后，分块由 Go 端完成；保留此类以兼容已有解析器构造函数。
    """

    chunk_size: int = 512
    chunk_overlap: int = 50
    separators: list[str] | None = None
    enable_multimodal: bool = False
    storage_config: dict[str, str] | None = None
    vlm_config: dict[str, str] | None = None
