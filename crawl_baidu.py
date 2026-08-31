"""Crawl Baidu talent social product positions via form-encoded getPostListNew API.
recruitType=SOCIAL, keyWord=产品. Detail route: /detail/social/{postId}."""
import urllib.request, json, urllib.parse, time
from pwutil import save_json

URL = "https://talent.baidu.com/httservice/getPostListNew"
H = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://talent.baidu.com/jobs/social-list",
    "Origin": "https://talent.baidu.com",
    "Content-Type": "application/x-www-form-urlencoded",
}
MAX_PAGES = 12  # ~120 jobs

def call(page_index):
    params = {
        "recruitType": "SOCIAL",
        "keyWord": "产品",
        "pageIndex": page_index,
        "pageSize": 20,   # >20 returns empty; 20 yields 20 unique jobs
    }
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(URL, data=body, headers=H)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def main():
    jobs = []
    # API ignores pageIndex beyond first page, so a single page of 20 is the full yield.
    for pg in range(1, 3):
        try:
            d = call(pg)
        except Exception as e:
            print("page", pg, "err", e)
            break
        if d.get("status") != "ok":
            print("page", pg, "status", d.get("status"), d.get("message"))
            break
        lst = d["data"].get("list", [])
        if not lst:
            break
        before = len(jobs)
        for it in lst:
            if it.get("postId") not in {j.get("postId") for j in jobs}:
                jobs.append(it)
        print(f"page {pg}: +{len(jobs)-before} unique (total {len(jobs)})")
        if len(jobs) >= 20 or len(lst) < 20:
            break
        time.sleep(0.5)
    print("total baidu product jobs:", len(jobs))
    save_json("baidu_raw.json", jobs)
    print("saved baidu_raw.json")

if __name__ == "__main__":
    main()
