import logging
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path
from typing import List, Optional

import textract

from docreader.config import CONFIG
from docreader.models.document import Document
from docreader.parser.docx2_parser import Docx2Parser
from docreader.utils.tempfile import TempDirContext, TempFileContext

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """支持代理配置的命令执行沙箱。"""

    def __init__(self, proxy: Optional[str] = None, default_timeout: int = 60):
        """初始化沙箱执行器。

        参数：
            proxy: 网络代理 URL；为 None 时读取 WEB_PROXY 环境变量。
            default_timeout: 命令执行的默认超时秒数。
        """
        # 优先使用参数中的代理，其次读取环境变量，最后使用默认阻断代理。
        # 用 or None 将空字符串转为 None，再应用默认值。
        self.proxy = proxy or CONFIG.external_https_proxy or "http://128.0.0.1:1"
        self.default_timeout = default_timeout

    def execute_in_sandbox(self, cmd: List[str]) -> tuple:
        """在配置了代理的沙箱中执行命令。

        参数：
            cmd: 待执行的命令。

        返回：
            (stdout, stderr, returncode) 元组。
        """
        # 按优先级尝试不同的沙箱执行方式。
        sandbox_methods = [
            self._execute_with_proxy,
        ]

        for method in sandbox_methods:
            try:
                return method(cmd)
            except Exception as e:
                logger.warning(f"Sandbox method {method.__name__} failed: {e}")
                continue

        raise RuntimeError("All sandbox methods failed")

    def _execute_with_proxy(self, cmd: List[str]) -> tuple:
        """使用代理配置执行命令，返回 (stdout, stderr, returncode)。

        参数：
            cmd: 待执行的命令。
        """
        # 设置包含代理配置的执行环境。
        env = os.environ.copy()
        if self.proxy:
            env["http_proxy"] = self.proxy
            env["https_proxy"] = self.proxy
            env["HTTP_PROXY"] = self.proxy
            env["HTTPS_PROXY"] = self.proxy

        logger.info(f"Executing command with proxy: {' '.join(cmd)}")
        if self.proxy:
            logger.info(f"Using proxy: {self.proxy}")

        is_posix = os.name == "posix"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            # 在 POSIX 系统上创建独立进程组，使超时命令及其
            # 派生子进程（如 soffice.bin）可以一并终止。
            start_new_session=is_posix,
        )
        # POSIX 的 start_new_session 会让直接子进程成为组长，
        # 即使它在清理前退出，也要保留进程组 ID。
        process_group_id = process.pid if is_posix else None

        try:
            stdout, stderr = process.communicate(timeout=self.default_timeout)
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            # 终止 POSIX 进程组（其他平台终止直接子进程），
            # 并在有限时间内回收进程。此处不读取管道：
            # communicate() 会等待 EOF；若后代进程脱离进程组（setsid）
            # 或仍持有管道写端，等待可能永久阻塞。
            try:
                self._kill_timed_out_command(process, process_group_id)
            finally:
                self._reap_timed_out_process(process)
            raise RuntimeError(
                f"Command execution timeout after {self.default_timeout} seconds"
            )

    def _kill_timed_out_command(
        self, process: subprocess.Popen, process_group_id: Optional[int]
    ) -> None:
        if process_group_id is None:
            try:
                process.kill()
            except OSError:
                pass
            return

        self._signal_process_group(process_group_id, signal.SIGTERM)
        grace_period = 0.5
        grace_deadline = time.monotonic() + grace_period
        try:
            process.wait(timeout=grace_period)
        except subprocess.TimeoutExpired:
            pass
        remaining_grace_period = grace_deadline - time.monotonic()
        if remaining_grace_period > 0:
            time.sleep(remaining_grace_period)
        # 直接子进程可能响应 SIGTERM 退出，但后代进程仍忽略该信号。
        # 因此宽限期结束后始终发送 SIGKILL。
        self._signal_process_group(process_group_id, signal.SIGKILL)

    @staticmethod
    def _signal_process_group(process_group_id: int, sig: int) -> None:
        try:
            os.killpg(process_group_id, sig)
        except OSError:
            pass

    @staticmethod
    def _reap_timed_out_process(
        process: subprocess.Popen, timeout: float = 1.0
    ) -> None:
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Timed-out command pid=%s did not exit after SIGKILL",
                    process.pid,
                )
        finally:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass


logger = logging.getLogger(__name__)


class DocParser(Docx2Parser):
    """DOC 文档解析器。"""

    def __init__(self, *args, **kwargs):
        """使用沙箱执行器初始化 DOC 解析器。"""
        super().__init__(*args, **kwargs)
        self.sandbox_executor = SandboxExecutor()

    def parse_into_text(self, content: bytes) -> Document:
        logger.info(f"Parsing DOC document, content size: {len(content)} bytes")

        handle_chain = [
            # 1. 优先转为 DOCX，以便同时提取图片。
            self._parse_with_docx,
            # 2. 无需提取图片或转换失败时，
            # 尝试使用 antiword 提取文本。
            self._parse_with_antiword,
            # 3. antiword 提取失败时原计划使用 textract。
            # 注意：因存在 SSRF 漏洞，_parse_with_textract 已禁用。
            # self._parse_with_textract,
        ]

        # 将字节内容保存为临时文件。
        with TempFileContext(content, ".doc") as temp_file_path:
            for handle in handle_chain:
                try:
                    document = handle(temp_file_path)
                    if document:
                        return document
                except Exception as e:
                    logger.warning(f"Failed to parse DOC with {handle.__name__} {e}")

            return Document(content="")

    def _parse_with_docx(self, temp_file_path: str) -> Document:
        logger.info("Multimodal enabled, attempting to extract images from DOC")

        docx_content = self._try_convert_doc_to_docx(temp_file_path)
        if not docx_content:
            raise RuntimeError("Failed to convert DOC to DOCX")

        logger.info("Successfully converted DOC to DOCX, using DocxParser")
        # 使用已有 DocxParser 解析转换后的 DOCX。
        document = super(Docx2Parser, self).parse_into_text(docx_content)
        logger.info(f"Extracted {len(document.content)} characters using DocxParser")
        return document

    def _parse_with_antiword(self, temp_file_path: str) -> Document:
        logger.info("Attempting to parse DOC file with antiword")

        # 检查是否安装 antiword。
        antiword_path = self._try_find_antiword()
        if not antiword_path:
            raise RuntimeError("antiword not found in PATH")

        # 在沙箱中使用 antiword 直接提取文本。
        cmd = [antiword_path, temp_file_path]
        logger.info("Executing antiword in sandbox with proxy configuration")

        stdout, stderr, returncode = self.sandbox_executor.execute_in_sandbox(cmd)

        if returncode != 0:
            raise RuntimeError(
                f"antiword extraction failed: {stderr.decode('utf-8', errors='ignore')}"
            )
        text = stdout.decode("utf-8", errors="ignore")
        logger.info(f"Successfully extracted {len(text)} characters using antiword")
        return Document(content=text)

    def _parse_with_textract(self, temp_file_path: str) -> Document:
        logger.info(f"Parsing DOC file with textract: {temp_file_path}")
        text = textract.process(temp_file_path, method="antiword").decode("utf-8")
        logger.info(f"Successfully extracted {len(text)} bytes of DOC using textract")
        return Document(content=str(text))

    def _try_convert_doc_to_docx(self, doc_path: str) -> Optional[bytes]:
        """通过 LibreOffice/OpenOffice 将 DOC 转为 DOCX。

        参数：
            doc_path: DOC 文件路径。

        返回：
            DOCX 文件字节；转换失败时返回 None。
        """
        logger.info(f"Converting DOC to DOCX: {doc_path}")

        # 检查是否安装 LibreOffice 或 OpenOffice。
        soffice_path = self._try_find_soffice()
        if not soffice_path:
            return None

        # 执行格式转换命令。
        logger.info(f"Using {soffice_path} to convert DOC to DOCX")

        # LibreOffice 默认共享一个用户配置目录，并发调用
        # soffice 会竞争同一配置锁，竞争失败的一方
        # 可能静默转换失败。为每次尝试创建独立配置目录，
        # 并进行有限次数重试，避免并发请求退回到
        # 保真度较低的 antiword 解析路径。
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            # 创建临时目录以保存转换结果。
            with TempDirContext() as temp_dir, TempDirContext() as profile_dir:
                user_installation = Path(profile_dir).as_uri()
                cmd = [
                    soffice_path,
                    "--headless",
                    f"-env:UserInstallation={user_installation}",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    temp_dir,
                    doc_path,
                ]
                logger.info(
                    f"Running command in sandbox (attempt {attempt}/{max_attempts}): "
                    f"{' '.join(cmd)}"
                )

                # 在配置了代理的沙箱中执行。
                stdout, stderr, returncode = self.sandbox_executor.execute_in_sandbox(
                    cmd
                )

                if returncode != 0:
                    logger.warning(
                        f"Error converting DOC to DOCX (attempt {attempt}/"
                        f"{max_attempts}): {stderr.decode('utf-8', errors='ignore')}"
                    )
                    if attempt < max_attempts:
                        time.sleep(0.5 * attempt)
                        continue
                    return None

                # 查找转换后的文件。
                docx_file = [
                    file for file in os.listdir(temp_dir) if file.endswith(".docx")
                ]
                logger.info(
                    f"Found {len(docx_file)} DOCX file(s) in temporary directory"
                )
                for file in docx_file:
                    converted_file = os.path.join(temp_dir, file)
                    logger.info(f"Found converted file: {converted_file}")

                    # 读取转换后的文件内容。
                    with open(converted_file, "rb") as f:
                        docx_content = f.read()
                        logger.info(
                            f"Successfully read DOCX file, size: {len(docx_content)}"
                        )
                        return docx_content

                # 命令报告成功但未生成 DOCX，继续重试。
                logger.warning(
                    f"No DOCX produced despite success (attempt {attempt}/"
                    f"{max_attempts})"
                )
                if attempt < max_attempts:
                    time.sleep(0.5 * attempt)
        return None

    def _try_find_executable_path(
        self,
        executable_name: str,
        possible_path: List[str] = [],
        environment_variable: List[str] = [],
    ) -> Optional[str]:
        """查找可执行文件路径。

        参数：
            executable_name: 可执行文件名。
            possible_path: 候选路径列表。
            environment_variable: 待检查的环境变量列表。

        返回：
            可执行文件路径；未找到时返回 None。
        """
        # 常见可执行文件路径。
        paths: List[str] = []
        paths.extend(possible_path)
        paths.extend(os.environ.get(env_var, "") for env_var in environment_variable)
        paths = list(set(paths))

        # 检查环境变量是否指定路径。
        for path in paths:
            if os.path.exists(path):
                logger.info(f"Found {executable_name} at {path}")
                return path

        # 尝试在 PATH 中查找。
        result = subprocess.run(
            ["which", executable_name], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            logger.info(f"Found {executable_name} at {path}")
            return path

        logger.warning(f"Failed to find {executable_name}")
        return None

    def _try_find_soffice(self) -> Optional[str]:
        """查找 LibreOffice/OpenOffice 可执行文件，未找到时返回 None。"""
        # LibreOffice/OpenOffice 常见可执行文件路径。
        possible_paths = [
            # Linux
            "/usr/bin/soffice",
            "/usr/lib/libreoffice/program/soffice",
            "/opt/libreoffice25.2/program/soffice",
            # macOS
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            # Windows
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
            "C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe",
        ]
        return self._try_find_executable_path(
            executable_name="soffice",
            possible_path=possible_paths,
            environment_variable=["LIBREOFFICE_PATH"],
        )

    def _try_find_antiword(self) -> Optional[str]:
        """查找 antiword 可执行文件，未找到时返回 None。"""
        # antiword 常见可执行文件路径。
        possible_paths = [
            # Linux/macOS
            "/usr/bin/antiword",
            "/usr/local/bin/antiword",
            # Windows
            "C:\\Program Files\\Antiword\\antiword.exe",
            "C:\\Program Files (x86)\\Antiword\\antiword.exe",
        ]
        return self._try_find_executable_path(
            executable_name="antiword",
            possible_path=possible_paths,
            environment_variable=["ANTIWORD_PATH"],
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    file_name = "/path/to/your/test.doc"
    logger.info(f"Processing file: {file_name}")
    doc_parser = DocParser(
        file_name=file_name,
        enable_multimodal=True,
        chunk_size=512,
        chunk_overlap=60,
    )
    with open(file_name, "rb") as f:
        content = f.read()

    document = doc_parser.parse_into_text(content)
    logger.info(f"Processing complete, extracted text length: {len(document.content)}")
    logger.info(f"Sample text: {document.content[:200]}...")
