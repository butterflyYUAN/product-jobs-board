"""Shared Playwright helpers with retry against flaky Windows segfaults."""
import time
import json
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

def launch_browser(p):
    try:
        return p.chromium.launch(headless=True, channel="chrome",
                                  args=["--no-sandbox", "--disable-dev-shm-usage"])
    except Exception:
        return p.chromium.launch(headless=True,
                                 args=["--no-sandbox", "--disable-dev-shm-usage"])

def new_ctx(b):
    return b.new_context(user_agent=UA, locale="zh-CN",
                         viewport={"width": 1366, "height": 900})

def run_with_retry(fn, attempts=4):
    """Run fn() that uses a fresh playwright session; retry on crash."""
    last = None
    for i in range(1, attempts + 1):
        try:
            with sync_playwright() as p:
                return fn(p)
        except Exception as e:
            last = e
            print(f"  [retry {i}/{attempts}] {type(e).__name__}: {str(e)[:120]}")
            time.sleep(1.5 * i)
    raise last

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
