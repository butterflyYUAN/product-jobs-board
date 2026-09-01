"""Crawl ByteDance product positions (experienced) via network interception.

The page computes a client-side `_signature`; we let the real browser do it and
capture the XHR responses instead of replaying them.

v2: paginate deterministically by looping the `current` query param with a larger
`limit` (the old next-page-click approach silently re-captured page 1, leaving us
with only 10 unique jobs after dedupe).
"""
import json, re
from pwutil import run_with_retry, launch_browser, new_ctx, save_json

BASE = ("https://jobs.bytedance.com/experienced/position?keywords="
        "&category=6704215864629004552%2C6704215864591255820"
        "%2C6704215924712409352%2C6704216224387041544"
        "&location=CT_11%2CCT_188&project=&type=&job_hot_flag="
        "&current=1&limit=30&functionCategory=&tag=")

LIMIT = 30
MAX_PAGES = 12  # safety cap; stop early when a page yields < LIMIT new items

def url_for(current):
    u = re.sub(r"current=\d+", "current=" + str(current), BASE)
    u = re.sub(r"limit=\d+", "limit=" + str(LIMIT), u)
    return u

def crawl(p):
    b = launch_browser(p)
    ctx = new_ctx(b)
    page = ctx.new_page()
    captured = []        # raw API responses
    seen_ids = set()
    total_new = 0
    def on_resp(r):
        if "search/job/posts" in r.url:
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
            lst = (cap.get("data") or {}).get("job_post_list") or []
            if lst:
                captured.append(cap)
    page.on("response", on_resp)

    for current in range(1, MAX_PAGES + 1):
        page.goto(url_for(current), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4500)
        # count new unique ids seen so far in captured
        new_in_page = 0
        for cap in captured:
            for it in (cap.get("data") or {}).get("job_post_list") or []:
                iid = it.get("id")
                if iid not in seen_ids:
                    seen_ids.add(iid)
                    new_in_page += 1
        total_new = len(seen_ids)
        # stop when this page added nothing new or fewer than a full page
        if current > 1 and (new_in_page == 0):
            break
    b.close()
    return captured

def main():
    data = run_with_retry(crawl)
    # Flatten + dedupe by id
    jobs = []
    seen = set()
    for cap in data:
        try:
            lst = cap["data"]["job_post_list"]
        except Exception:
            continue
        for it in lst:
            iid = it.get("id")
            if iid in seen:
                continue
            seen.add(iid)
            jobs.append(it)
    print(f"captured responses: {len(data)}, unique items: {len(jobs)}")
    save_json("bytedance_raw.json", jobs)
    print("saved bytedance_raw.json")

if __name__ == "__main__":
    main()
