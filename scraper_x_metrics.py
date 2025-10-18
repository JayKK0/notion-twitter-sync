from playwright.sync_api import sync_playwright
import time, random, re

_VIEWS_TEXT = re.compile(r"(\d{1,3}(?:,\d{3})*)\s+Views", re.I)
_NUM        = re.compile(r"(\d{1,3}(?:,\d{3})*)")

def get_metrics(tweet_url: str, debug: bool = False):
    """Return (views, likes). Any missing value -> None."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        try:
            page.goto(tweet_url, timeout=45000, wait_until="domcontentloaded")
            time.sleep(2.5 + random.random()*1.5)

            views = None
            likes = None


            try:
                like_btn = page.locator('[data-testid="like"]').first
                if like_btn.count() == 0:
                    like_btn = page.locator("button[aria-label*='Like']").first
                if like_btn.count() > 0:
                    label = like_btn.get_attribute("aria-label") or like_btn.inner_text()
                    if label:
                        m = _NUM.search(label)
                        if m:
                            likes = int(m.group(1).replace(",", ""))
            except Exception:
                pass


            try:
                views_el = page.locator("span:has-text('Views')").last
                if views_el.count() > 0:
                    handle = views_el.element_handle()
                    if handle:
                        prev_num = page.evaluate("""
                            el => {
                              const prev = el.previousSibling;
                              return prev && prev.textContent ? prev.textContent.trim() : null;
                            }
                        """, handle)
                        if prev_num:
                            m = _NUM.search(prev_num)
                            if m:
                                views = int(m.group(1).replace(",", ""))
            except Exception:
                pass


            if views is None:
                try:
                    body_text = page.inner_text("body")
                    m = _VIEWS_TEXT.search(body_text)
                    if m:
                        views = int(m.group(1).replace(",", ""))
                except Exception:
                    pass

            return views, likes

        finally:
            browser.close()

