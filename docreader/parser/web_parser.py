import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional

from lxml.etree import XPath
from playwright.async_api import Page, async_playwright
from trafilatura import extract, utils, xpaths

from docreader.config import CONFIG
from docreader.models.document import Document
from docreader.parser.base_parser import BaseParser
from docreader.parser.chain_parser import PipelineParser
from docreader.parser.markdown_parser import MarkdownParser
from docreader.utils import endecode
from docreader.utils.ssrf import is_ssrf_safe_url
from docreader.utils.ssrf_proxy import SSRFProxy

logger = logging.getLogger(__name__)


class WebParseError(RuntimeError):
    """URL 抓取失败或没有可提取内容时抛出的异常。

    必须作为解析失败向上传播；若将错误字符串作为正文返回，会被错误地索引为知识。
    """


_GOTO_TIMEOUT_MS = 30_000
_NETWORK_IDLE_TIMEOUT_MS = 10_000
_SPA_WAIT_TIMEOUT_MS = 15_000
# Minimum visible characters before treating an SPA shell as "rendered".
_SPA_MIN_TEXT_LEN = 80
# Minimum visible characters for Playwright text fallback when trafilatura fails.
_MIN_FALLBACK_TEXT_LEN = 50

# Monkey-patch trafilatura internals to better support WeChat Official Account
# articles, whose images live on `mmbiz.qpic.cn` without a standard file
# extension and whose main content sits inside `#js_content` /
# `.rich_media_content`. Trafilatura's `utils.IMAGE_EXTENSION` and
# `xpaths.BODY_XPATH` are internal APIs, so we guard the patch and skip
# silently if they are renamed/removed in a future release.
try:
    _WECHAT_IMAGE_EXTENSION = re.compile(
        r"[^\s]+\.(avif|bmp|gif|hei[cf]|jpe?g|png|webp)(\b|$)|"  # Standard extensions
        r"mmbiz\.qpic\.cn/[^\s]*wx_fmt=(jpeg|jpg|png|gif|webp)"  # WeChat query format
    )
    utils.IMAGE_EXTENSION = _WECHAT_IMAGE_EXTENSION

    _WECHAT_BODY_XPATH = XPath(
        '(.//*[@id="js_content" or contains(@class, "rich_media_content")])[1]'
    )
    _wechat_xpath_str = str(_WECHAT_BODY_XPATH)
    if not any(str(x) == _wechat_xpath_str for x in xpaths.BODY_XPATH):
        xpaths.BODY_XPATH.insert(0, _WECHAT_BODY_XPATH)
except (AttributeError, ImportError) as e:
    logger.warning(
        "Failed to patch trafilatura internals for WeChat support: %s", e
    )


@dataclass(frozen=True)
class _ScrapeResult:
    html: str
    visible_text: str
    page_title: str
    error: str = ""


def extract_markdown_from_html(html: str) -> Optional[str]:
    """使用 trafilatura 处理 HTML，返回 Markdown；无可提取内容时返回 None。"""
    if not html or not html.strip():
        return None
    md_text = extract(
        html,
        output_format="markdown",
        with_metadata=True,
        include_images=True,
        include_tables=True,
        include_links=True,
    )
    if not md_text or not md_text.strip():
        return None
    return md_text


def build_visible_text_fallback(visible_text: str, page_title: str = "") -> Optional[str]:
    """trafilatura 未找到文章正文时，从 Playwright 可见文本构建 Markdown。"""
    text = (visible_text or "").strip()
    if len(text) < _MIN_FALLBACK_TEXT_LEN:
        return None
    title = (page_title or "").strip()
    if title and not text.startswith(title):
        return f"# {title}\n\n{text}"
    return text


async def wait_for_rendered_content(page: Page) -> None:
    """等待 SPA/JavaScript 页面加载，越过初始 HTML 空壳阶段。"""
    try:
        await page.wait_for_load_state("networkidle", timeout=_NETWORK_IDLE_TIMEOUT_MS)
        logger.info("Network idle after navigation")
    except Exception:
        logger.info("Network idle wait timed out, continuing")

    try:
        await page.wait_for_function(
            """(minLen) => {
                const root = document.querySelector('#app')
                    || document.querySelector('main')
                    || document.body;
                return ((root?.innerText || '').trim().length >= minLen);
            }""",
            arg=_SPA_MIN_TEXT_LEN,
            timeout=_SPA_WAIT_TIMEOUT_MS,
        )
        logger.info("SPA/root visible text reached minimum length")
    except Exception:
        logger.info("SPA text wait timed out, using current DOM")


async def read_visible_text(page: Page) -> str:
    """优先读取 #app/main 的 innerText，再回退到 body。"""
    return await page.evaluate(
        """() => {
            const root = document.querySelector('#app')
                || document.querySelector('main')
                || document.querySelector('[role="main"]')
                || document.body;
            return (root?.innerText || '').trim();
        }"""
    )


async def install_ssrf_route_guard(page: Page) -> None:
    """尽早拒绝不安全的初始 URL；SSRFProxy 会校验每次实际连接。"""

    async def handle_route(route) -> None:
        safe, reason = is_ssrf_safe_url(route.request.url)
        if not safe:
            logger.warning(
                "SSRF guard blocked request to %s: %s", route.request.url, reason
            )
            await route.abort("blockedbyclient")
            return
        await route.continue_()

    await page.route("**/*", handle_route)


class StdWebParser(BaseParser):
    """基于 Playwright 和 Trafilatura 的标准网页解析器。

    使用 Playwright 的 WebKit 浏览器抓取网页，再通过 Trafilatura 提取干净正文，
    支持代理配置，并将 HTML 转换为 Markdown。
    """

    def __init__(self, title: str, **kwargs):
        """初始化网页解析器。

        参数：
            title: 用作文件名的网页标题。
            **kwargs: 传递给 BaseParser 的其他参数。
        """
        self.title = title
        # Get proxy configuration from config if available
        self.proxy = CONFIG.external_https_proxy
        super().__init__(file_name=title, **kwargs)
        logger.info(f"Initialized WebParser with title: {title}")

    async def scrape(self, url: str) -> _ScrapeResult:
        """使用 Playwright 抓取网页。

        参数：
            url: 目标网页 URL。

        返回：
            HTML、可见文本和文档标题；严重失败时内容字段为空，由 error 说明原因。
        """
        logger.info(f"Starting web page scraping for URL: {url}")
        safe, reason = is_ssrf_safe_url(url)
        if not safe:
            logger.error("URL blocked by SSRF guard before navigation: %s", reason)
            return _ScrapeResult(
                html="", visible_text="", page_title="",
                error=f"URL blocked by SSRF guard: {reason}",
            )
        try:
            async with SSRFProxy(self.proxy) as proxy, async_playwright() as p:
                kwargs = {"proxy": {"server": proxy.url, "bypass": ""}}
                logger.info("Launching WebKit browser")
                browser = await p.webkit.launch(**kwargs)
                page = await browser.new_page(service_workers="block")
                await install_ssrf_route_guard(page)

                logger.info(f"Navigating to URL: {url}")
                try:
                    await page.goto(
                        url,
                        timeout=_GOTO_TIMEOUT_MS,
                        wait_until="domcontentloaded",
                    )
                    logger.info("Initial page load complete")
                except Exception as e:
                    logger.error(f"Error navigating to URL: {str(e)}")
                    await browser.close()
                    return _ScrapeResult(
                        html="", visible_text="", page_title="",
                        error=f"navigation failed: {e}",
                    )

                await wait_for_rendered_content(page)

                page_title = await page.title()
                visible_text = await read_visible_text(page)
                content = await page.content()
                logger.info(
                    "Retrieved %d bytes HTML, %d chars visible text, title=%r",
                    len(content),
                    len(visible_text),
                    page_title[:80] if page_title else "",
                )

                await browser.close()
                logger.info("Browser closed")

            logger.info("Successfully retrieved HTML content")
            return _ScrapeResult(
                html=content,
                visible_text=visible_text,
                page_title=page_title or "",
            )

        except Exception as e:
            logger.error(f"Failed to scrape web page: {str(e)}")
            return _ScrapeResult(
                html="", visible_text="", page_title="",
                error=f"scrape failed: {e}",
            )

    def parse_into_text(self, content: bytes) -> Document:
        """将网页内容解析为 Document。

        参数：
            content: 编码为字节的 URL。

        返回：
            包含 Markdown 正文的 Document。

        异常：
            WebParseError: 抓取失败或页面无可提取内容。调用方须报告解析失败，
                不得将错误字符串作为正文索引。
        """
        url = endecode.decode_bytes(content)

        logger.info(f"Scraping web page: {url}")
        scrape_result = asyncio.run(self.scrape(url))
        if scrape_result.error or (
            not scrape_result.html and not scrape_result.visible_text
        ):
            detail = scrape_result.error or "no HTML or visible text"
            logger.error("Failed to scrape web page %s: %s", url, detail)
            raise WebParseError(f"Failed to scrape web page: {url} ({detail})")

        md_text = extract_markdown_from_html(scrape_result.html)
        if not md_text:
            md_text = build_visible_text_fallback(
                scrape_result.visible_text,
                scrape_result.page_title,
            )
            if md_text:
                logger.info(
                    "Trafilatura empty; using Playwright visible-text fallback (%d chars)",
                    len(md_text),
                )

        if not md_text:
            logger.error("Failed to parse web page: %s", url)
            raise WebParseError(f"Failed to parse web page: {url}")

        metadata = {}
        title_match = re.search(r"^title:\s*(.+)", md_text, re.MULTILINE)
        if title_match:
            extracted_title = title_match.group(1).strip()
            if extracted_title:
                metadata["title"] = extracted_title
                logger.info(
                    f"Extracted article title from trafilatura: {extracted_title}"
                )
        elif scrape_result.page_title:
            metadata["title"] = scrape_result.page_title.strip()
            logger.info(
                "Using page title from Playwright: %s", metadata["title"]
            )
        else:
            logger.info(
                "No title found in trafilatura output, first 200 chars: %r",
                md_text[:200],
            )
        return Document(content=md_text, metadata=metadata)


class WebParser(PipelineParser):
    """基于流水线的网页解析器。

    先由 StdWebParser 抓取网页并将 HTML 转换为 Markdown，
    再交由 MarkdownParser 继续处理，两阶段顺序执行。
    """

    # Parser classes to be executed in sequence
    _parser_cls = (StdWebParser, MarkdownParser)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    url = sys.argv[1] if len(sys.argv) > 1 else "https://cloud.tencent.com/document/product/457/6759"
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    parser = WebParser(title="")
    doc = parser.parse_into_text(url.encode())

    print(f"--- metadata ---")
    for k, v in doc.metadata.items():
        print(f"  {k}: {v}")

    print(f"\n--- images ({len(doc.images)}) ---")
    for path in list(doc.images.keys())[:10]:
        print(f"  {path}  ({len(doc.images[path])} chars base64)")

    print(f"\n--- content ({len(doc.content)} chars) ---")
    print(doc.content[:300000])
    if len(doc.content) > 300000:
        print(f"\n... (truncated, total {len(doc.content)} chars)")

    print(f"\n--- chunks ({len(doc.chunks)}) ---")
    for i, chunk in enumerate(doc.chunks[:5]):
        print(f"  [{i}] seq={chunk.seq} range=[{chunk.start}:{chunk.end}] len={len(chunk.content)}")
        print(f"      {chunk.content[:120]}{'...' if len(chunk.content) > 120 else ''}")
    if len(doc.chunks) > 5:
        print(f"  ... ({len(doc.chunks) - 5} more chunks)")
