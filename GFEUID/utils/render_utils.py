"""Playwright / Jinja2 渲染工具"""

import asyncio
from pathlib import Path
from typing import Optional

from gsuid_core.logger import logger

from ..gfe_config.gfe_config import GfeConfig

TEMPLATES_ABS_PATH = Path(__file__).parent.parent / "templates"

_playwright = None
_browser = None
_browser_lock = asyncio.Lock()


def _import_playwright():
    try:
        from playwright.async_api import async_playwright
        return async_playwright
    except ImportError:
        logger.warning("[GFEuid] 未安装 playwright，Wiki渲染等功能不可用")
        return None


async_playwright = _import_playwright()
PLAYWRIGHT_AVAILABLE = async_playwright is not None


async def get_browser():
    global _playwright, _browser
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright 未安装")

    async with _browser_lock:
        if _browser and _browser.is_connected():
            return _browser

        if _playwright is None:
            _playwright = await async_playwright().start()

        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        return _browser


async def render_html(html: str, width: int = 800, height: int = 0) -> bytes:
    """用 Playwright 渲染 HTML 为 PNG 截图 bytes"""
    browser = await get_browser()
    page = await browser.new_page()
    try:
        await page.set_viewport_size({"width": width, "height": max(height, 600)})
        await page.set_content(html, wait_until="networkidle")
        if height == 0:
            body_height = await page.evaluate("document.body.scrollHeight")
            await page.set_viewport_size({"width": width, "height": body_height + 20})
        return await page.screenshot(full_page=True, type="png")
    finally:
        await page.close()


async def render_template(
    template_name: str,
    data: dict,
    width: Optional[int] = None,
) -> bytes:
    """Jinja2 模板 → Playwright 渲染 → PNG bytes"""
    from ..utils.resource.RESOURCE_PATH import gfe_templates

    if width is None:
        width = GfeConfig.get_config("ScreenshotWidth").data

    template = gfe_templates.get_template(template_name)
    html = template.render(**data)
    return await render_html(html, width)
