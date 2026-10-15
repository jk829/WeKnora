import logging
import os
import tempfile

logger = logging.getLogger(__name__)


class TempFileContext:
    def __init__(self, file_content: bytes, suffix: str):
        """初始化临时文件上下文。

        :param file_content: 要写入文件的字节数据。
        :param suffix: 文件后缀。
        """
        self.file_content = file_content
        self.suffix = suffix
        self.file = None

    def _cleanup(self):
        """关闭并删除临时文件。

        close() 可能再次抛出先前的刷新错误（如 ENOSPC），因此仍须执行删除；
        清理阶段的异常不应覆盖最初的异常。
        """
        temp_file = getattr(self, "temp_file", None)
        if not temp_file:
            return
        try:
            temp_file.close()
        except OSError:
            pass
        try:
            os.remove(temp_file.name)
        except OSError:
            pass

    def __enter__(self):
        """进入上下文时创建临时文件。"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=self.suffix, delete=False)
        # 若写入或刷新失败（如 ENOSPC），异常会从 __enter__ 抛出，
        # __exit__ 不会执行，因此必须在这里清理，避免临时文件
        # 永久遗留；delete=False 也意味着垃圾回收不会删除文件。
        try:
            self.temp_file.write(self.file_content)
            self.temp_file.flush()
        except BaseException:
            self._cleanup()
            raise
        logger.info(
            f"Saved {self.suffix} content to temporary file: {self.temp_file.name}"
        )
        return self.temp_file.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时删除临时文件。"""
        if getattr(self, "temp_file", None):
            name = self.temp_file.name
            self._cleanup()
            logger.info(f"File {name} has been deleted.")
        # 返回 False，让上下文中的异常继续向外传播。
        return False


class TempDirContext:
    def __init__(self):
        """初始化临时目录上下文。"""
        self.temp_dir = None

    def __enter__(self):
        """进入上下文时创建临时目录。"""
        self.temp_dir = tempfile.TemporaryDirectory()
        logger.info(f"Created temporary directory: {self.temp_dir.name}")
        return self.temp_dir.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时删除临时目录。"""
        if self.temp_dir and os.path.exists(self.temp_dir.name):
            self.temp_dir.cleanup()
            logger.info(f"Directory {self.temp_dir.name} has been deleted.")
        # 返回 False，让上下文中的异常继续向外传播。
        return False


if __name__ == "__main__":
    example_bytes = b"Hello, this is a test file."
    file_name = "test_file.txt"

    # 使用 with 语句管理生命周期。
    with TempFileContext(example_bytes, file_name) as temp_file:
        # 可在上下文中执行文件操作。
        print(f"Does file {file_name} exist: {os.path.exists(file_name)}")
