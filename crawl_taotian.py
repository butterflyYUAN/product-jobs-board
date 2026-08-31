"""Crawl Taotian (Alibaba off-campus) product positions via search=产品.
Paginate by clicking the antd next-page button; capture /position/search responses."""
from pwutil import run_with_retry, launch_browser, new_ctx, save_json
import json, time

URL = "https://talent.taotian.com/off-campus/position-list?lang=zh&search=%E4%BA%A7%E5%93%81"

def click_next(page):
    for sel in ["button.next-next:not(.next-disabled)",
                "button.next-btn.next-pagination-item.next-next",
                "button[aria-label*='下一页']",
                ".next-pagination .next-next"]:
        try:
            el = page.locator(sel).first
            if el.count() and el.is_enabled():
                el.scroll_into_view_if_needed(timeout=2000)
                el.click(timeout=2500)
                return True
        except Exception:
            continue
    return False

def crawl(p):
    b = launch_browser(p)
    ctx = new_ctx(b)
    page = ctx.new_page()
    captured = []
    seen = set()
    def on_resp(r):
        if "position/search" in r.url:
            try:
                t = r.body().decode("utf-8", "ignore")
            except Exception:
                return
            if not t:
                return
            try:
                cap = json.loads(t)
            except Exception:
                return
            key = cap.get("content", {}).get("currentPage")
            if key not in seen:
                seen.add(key)
                captured.append(cap)
    page.on("response", on_resp)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)

    max_pages = 20
    for _ in range(max_pages - 1):
        before = len(captured)
        if not click_next(page):
            break
        page.wait_for_timeout(2500)
        if len(captured) == before:
            # try pressing End / scroll
            try:
                page.keyboard.press("End")
            except Exception:
                pass
            page.wait_for_timeout(2500)
            if len(captured) == before:
                break
    b.close()
    return captured

def main():
    caps = run_with_retry(crawl)
    jobs = []
    for c in caps:
        for it in c.get("content", {}).get("datas", []):
            jobs.append(it)
    print(f"responses: {len(caps)}, items: {len(jobs)}")
    save_json("taotian_raw.json", jobs)
    print("saved taotian_raw.json")

if __name__ == "__main__":
    main()
