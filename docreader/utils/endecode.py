"""编码与解码工具模块。

提供图片 Base64 编解码、多字符集文本转换和字节转换工具。
"""

import base64
import io
import logging
from typing import List, Union

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def decode_image(image: Union[str, bytes, Image.Image, np.ndarray]) -> str:
    """将图片转换为 Base64 字符串，便于嵌入 JSON、HTML 等文本格式。

    参数：
        image: 图片文件路径、原始 bytes、PIL/Pillow Image 或 NumPy 数组。

    返回：
        图片的 Base64 字符串。

    异常：
        ValueError: 不支持该图片类型。

    示例：
        >>> base64_str = decode_image("/path/to/image.png")
        >>> from PIL import Image
        >>> img = Image.open("photo.jpg")
        >>> base64_str = decode_image(img)
    """
    if isinstance(image, str):
        # 图片路径：读取文件并编码为 Base64。
        with open(image, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    elif isinstance(image, bytes):
        # 原始字节：直接编码为 Base64。
        return base64.b64encode(image).decode()

    elif isinstance(image, Image.Image):
        # PIL 图片：先写入缓冲区，再编码。
        buffer = io.BytesIO()
        # 优先保留原始格式；没有格式信息时使用 PNG。
        img_format = image.format if image.format else "PNG"
        image.save(buffer, format=img_format)
        return base64.b64encode(buffer.getvalue()).decode()

    elif isinstance(image, np.ndarray):
        # NumPy 数组：先转为 PIL 图片，再按 PNG 编码。
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    raise ValueError(f"Unsupported image type: {type(image)}")


def encode_image(image: str, errors="strict") -> bytes:
    """将 Base64 图片字符串解码为原始字节。

    参数：
        image: 图片的 Base64 字符串。
        errors: 错误处理方式；strict 默认抛出异常，ignore 在失败时返回空字节，
            也可传入 codecs.register_error 注册的其他名称。

    返回：
        解码后的 bytes；ignore 模式下失败则返回空字节。

    异常：
        ValueError: strict 模式下解码失败。填充或字符集错误会产生 binascii.Error，
            非 ASCII 字符串会产生 ValueError；前者是后者的子类，故统一捕获。

    示例：
        >>> base64_str = "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
        >>> image_bytes = encode_image(base64_str)
        >>> image_bytes = encode_image(base64_str, errors="ignore")
    """
    try:
        # 尝试将 Base64 字符串解码为字节。
        image_bytes = base64.b64decode(image)
    except ValueError as e:
        # 仅捕获 binascii.Error 会遗漏非 ASCII 字符串：
        # 这类输入在进入解码器之前就会触发普通 ValueError，
        # errors="ignore" 模式也需要处理该异常。
        if errors == "ignore":
            return b""
        else:
            raise e
    return image_bytes


def encode_bytes(content: str) -> bytes:
    """Convert a string to bytes using UTF-8 encoding.

    Args:
        content: String to be encoded

    Returns:
        bytes: UTF-8 encoded bytes representation of the string

    Example:
        >>> text = "Hello, 世界"
        >>> encoded = encode_bytes(text)
        >>> type(encoded)
        <class 'bytes'>
    """
    return content.encode()


def decode_bytes(
    content: bytes,
    encodings: List[str] = [
        "utf-8",
        "gb18030",
        "gb2312",
        "gbk",
        "big5",
        "ascii",
        "latin-1",
    ],
) -> str:
    """Decode bytes to string with automatic encoding detection.

    This function attempts to decode bytes using multiple encoding formats
    in order of priority. It's particularly useful for handling text files
    with unknown or mixed encodings, especially for Chinese text.

    The function tries encodings in the provided order and returns the first
    successful decode. If all encodings fail, it falls back to latin-1 with
    error replacement to ensure a result is always returned.

    Args:
        content: Bytes content to be decoded
        encodings: List of encoding formats to try, in order of priority.
            Default includes common encodings for Chinese and Western text:
            - utf-8: Universal encoding (tried first)
            - gb18030, gb2312, gbk: Chinese encodings (Simplified)
            - big5: Chinese encoding (Traditional)
            - ascii, latin-1: Western encodings

    Returns:
        str: Decoded string content

    Note:
        - If all encodings fail, latin-1 with error='replace' is used as fallback
        - The fallback may result in character replacement (�) for invalid bytes
        - A warning is logged when fallback encoding is used

    Example:
        >>> # Decode with default encodings
        >>> text = decode_bytes(b"\\xe4\\xb8\\xad\\xe6\\x96\\x87")  # UTF-8 Chinese
        >>> print(text)
        中文
        >>> # Decode with custom encodings
        >>> text = decode_bytes(content, encodings=["utf-8", "gbk"])
    """
    # 按顺序尝试各字符编码。
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            logger.debug(f"Decode content with {encoding}: {len(text)} characters")
            return text
        except UnicodeDecodeError:
            # 当前编码不适用，继续尝试下一个。
            continue

    # 所有编码均失败时，回退到 latin-1，并替换无法处理的字符。
    # latin-1 可解码任意字节序列，但结果可能存在错误字符。
    text = content.decode(encoding="latin-1", errors="replace")
    logger.warning(
        "Unable to determine correct encoding, using latin-1 as fallback. "
        "This may cause character issues."
    )
    return text


if __name__ == "__main__":
    # 示例：测试 encode_image 的错误处理。
    # 演示使用 ignore 模式解码 Base64 字符串。
    img = "test![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgA)test"
    encode_image(img, errors="ignore")
