"""Crawl ByteDance product positions (experienced) via network interception.
The page computes a client-side `_signature`; we let the real browser do it and
capture the XHR responses instead of replaying them."""
import json
from pwutil import run_with_retry, launch_browser, new_ctx, save_json

URL = ("https://jobs.bytedance.com/experienced/position?keywords="
       "&category=6704215864629004552%2C6704215864591255820"
       "%2C6704215924712409352%2C6704216224387041544"
       "&location=CT_11%2CCT_188&project=&type=&job_hot_flag="
       "&current=1&limit=10&functionCategory=&tag=")

def crawl(p):
    b = launch_browser(p)
    ctx = new_ctx(b)
    page = ctx.new_page()
    captured = []
    def on_resp(r):
        if "search/job/posts" in r.url:
            try:
                t = r.body().decode("utf-8", "ignore")
            except Exception:
                return
            if not t:
                return
            try:
                captured.append(json.loads(t))
            except Exception:
                pass
    page.on("response", on_resp)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)

    # Try to paginate by clicking the next-page button a few times.
    max_pages = 6
    for _ in range(max_pages - 1):
        before = len(captured)
        clicked = False
        for sel in ["text=下一页", "button[aria-label='Next page']",
                    ".ant-pagination-next:not(.ant-pagination-disabled)",
                    "li.ant-pagination-next:not(.ant-pagination-disabled)"]:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_enabled():
                    el.click(timeout=2000)
                    clicked = True
                    break
            except Exception:
                continue
        if not clicked:
            # try generic next arrow
            try:
                page.keyboard.press("End")
            except Exception:
                pass
        page.wait_for_timeout(3500)
        if len(captured) == before:
            break
    b.close()
    return captured

def main():
    data = run_with_retry(crawl)
    # Flatten
    jobs = []
    for cap in data:
        try:
            lst = cap["data"]["job_post_list"]
        except Exception:
            continue
        jobs.extend(lst)
    print(f"captured responses: {len(data)}, raw items: {len(jobs)}")
    save_json("bytedance_raw.json", jobs)
    print("saved bytedance_raw.json")

if __name__ == "__main__":
    main()
