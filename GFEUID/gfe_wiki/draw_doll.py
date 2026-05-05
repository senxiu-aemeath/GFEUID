"""角色 Wiki 图片渲染 — Playwright 截图 gf2.mcc.wiki"""

import base64
import time
from pathlib import Path

from ..utils.render_utils import get_browser, PLAYWRIGHT_AVAILABLE
from ..utils.resource.RESOURCE_PATH import WIKI_CACHE_PATH
from ..gfe_config.gfe_config import GfeConfig

WIKI_BASE = "https://gf2.mcc.wiki"
CACHE: dict[str, str] = {}


async def draw_doll_wiki(slug: str, name: str) -> str | None:
    """返回角色 Wiki 图片的 base64 字符串"""
    if not PLAYWRIGHT_AVAILABLE:
        return None

    key = f"doll_{slug}"
    if key in CACHE:
        if Path(CACHE[key]).exists():
            return _read_cached_file(Path(CACHE[key]))

    cache_file = WIKI_CACHE_PATH / f"doll_{slug}.png"
    ttl_days = GfeConfig.get_config("WikiRenderCacheTtlDays").data
    if cache_file.exists():
        if time.time() - cache_file.stat().st_mtime < ttl_days * 86400:
            CACHE[key] = str(cache_file)
            return _read_cached_file(cache_file)

    page = None
    try:
        browser = await get_browser()
        page = await browser.new_page()
        width = GfeConfig.get_config("ScreenshotWidth").data or 800
        await page.set_viewport_size({"width": width, "height": 600})
        await page.goto(f"{WIKI_BASE}/doll/{slug}", wait_until="networkidle", timeout=30000)

        # 等待内容加载
        try:
            await page.wait_for_selector("main, .container, #app", timeout=10000)
        except Exception:
            pass

        # 滚动触发图片懒加载
        await page.evaluate("""async () => {
            const wrap = document.querySelector('.el-scrollbar__wrap');
            if (!wrap) return;
            await new Promise(resolve => {
                const step = 300;
                const timer = setInterval(() => {
                    wrap.scrollTop += step;
                    if (wrap.scrollTop + wrap.clientHeight >= wrap.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 150);
            });
        }""")

        # 等待图片加载
        await page.evaluate("""async () => {
            await Promise.all(
                Array.from(document.images).map(img =>
                    img.complete ? Promise.resolve() : new Promise(resolve => {
                        img.onload = resolve; img.onerror = resolve; setTimeout(resolve, 5000);
                    })
                )
            );
        }""")

        # 展开完整内容并截图
        content_height = await page.evaluate("""() => {
            const wrap = document.querySelector('.el-scrollbar__wrap');
            if (!wrap) return document.documentElement.scrollHeight;
            wrap.scrollTop = 0;
            const full = wrap.scrollHeight;
            wrap.style.overflow = 'visible';
            wrap.style.height = full + 'px';
            wrap.style.maxHeight = 'none';
            const bar = wrap.closest('.el-scrollbar');
            if (bar) { bar.style.overflow = 'visible'; bar.style.height = full + 'px'; }
            document.body.style.height = full + 'px';
            document.documentElement.style.height = full + 'px';
            document.documentElement.style.overflow = 'visible';
            return full;
        }""")

        await page.set_viewport_size({"width": width, "height": content_height + 50})
        screenshot = await page.screenshot(full_page=True, type="png")
        await page.close()

        cache_file.write_bytes(screenshot)
        CACHE[key] = str(cache_file)
        return "base64://" + base64.b64encode(screenshot).decode()

    except Exception:
        if page is not None:
            try:
                await page.close()
            except Exception:
                pass
        return None


def _read_cached_file(path: Path) -> str:
    return "base64://" + base64.b64encode(path.read_bytes()).decode()
