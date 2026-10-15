import re
from typing import Callable, List


def split_text_keep_separator(text: str, separator: str) -> List[str]:
    """按分隔符切分文本，并将分隔符保留在后续片段开头。

    参数：
        text: 待切分文本。
        separator: 分隔字符串。

    返回：
        文本片段列表；除首片段外，每个片段开头保留分隔符。

    示例：
        >>> split_text_keep_separator("Hello\nWorld\nTest", "\n")
        ["Hello", "\nWorld", "\nTest"]
    """
    # 按分隔符切分文本。
    parts = text.split(separator)
    # 将分隔符补回后续片段的开头，首片段除外。
    result = [separator + s if i > 0 else s for i, s in enumerate(parts)]
    # 过滤空字符串。
    return [s for s in result if s]


def split_by_sep(sep: str, keep_sep: bool = True) -> Callable[[str], List[str]]:
    """创建按指定分隔符切分文本的函数。

    参数：
        sep: 分隔字符串。
        keep_sep: 为 True 时保留分隔符，否则丢弃。

    返回：
        接收文本并返回字符串片段列表的可调用对象。
    """
    if keep_sep:
        return lambda text: split_text_keep_separator(text, sep)
    else:
        return lambda text: text.split(sep)


def split_by_char() -> Callable[[str], List[str]]:
    """创建逐字符切分函数，接收文本并返回字符列表。"""
    return lambda text: list(text)


def split_by_regex(regex: str) -> Callable[[str], List[str]]:
    """创建按正则表达式切分文本的函数。

    参数：
        regex: 用于切分的正则表达式。

    返回：
        接收文本并返回片段列表的函数；使用捕获组保留匹配的分隔符。
    """
    # 将正则表达式包装为捕获组，保留结果中的分隔符。
    pattern = re.compile(f"({regex})")
    # 按正则模式切分，并过滤 None 和空字符串。
    return lambda text: list(filter(None, pattern.split(text)))


def match_by_regex(regex: str) -> Callable[[str], bool]:
    """创建检查文本是否匹配正则表达式的函数。

    参数：
        regex: 待匹配的正则表达式。

    返回：
        接收文本并返回布尔值的函数，从文本开头进行匹配。
    """
    # 预编译正则表达式以便重复使用。
    pattern = re.compile(regex)
    # 返回从文本开头检查模式匹配的函数。
    return lambda text: bool(pattern.match(text))
