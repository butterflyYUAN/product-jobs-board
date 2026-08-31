# -*- coding: utf-8 -*-
"""
腾讯招聘 - 产品职位爬虫（HTTP API，无需浏览器）
列表: post/Query  (categoryId=40003001~4 = 产品类, cityId=2,12, attrId=1 社招全职)
详情: post/ByPostId (含 岗位职责 Responsibility + 岗位要求 Requirement + 加分项 + 岗位亮点)
"""
import os, sys, json, time, urllib.request, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from digest_common import parse_date, render_section, write_section

COMPANY = "腾讯"
MARKER = "## 🟡 腾讯招聘"
LIST_URL = ("https://careers.tencent.com/search.html?query=ot_40003001,ot_40003002,"
            "ot_40003003,ot_40003004,at_1,ci_2,ci_12")
CATEGORY_IDS = "40003001,40003002,40003003,40003004"   # 产品类
CITY_IDS = "2,12"                                       # 北京,上海
ATTR_ID = "1"                                           # 全职
SOURCE_URL = LIST_URL

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

def _get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": "https://careers.tencent.com/search.html"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_list():
    jobs = []
    page = 1
    while True:
        ts = int(time.time()*1000)
        url = (f"https://careers.tencent.com/tencentcareer/api/post/Query?"
               f"timestamp={ts}&countryId=&cityId={CITY_IDS}&bgIds=&productId="
               f"&categoryId={CATEGORY_IDS}&parentCategoryId=&attrId={ATTR_ID}"
               f"&keyword=&pageIndex={page}&pageSize=20&language=zh-cn&area=cn")
        d = _get(url)
        posts = (d.get("Data") or {}).get("Posts") or []
        if not posts:
            break
        for p in posts:
            jobs.append(p)
        if len(posts) < 20:
            break
        page += 1
        time.sleep(0.5)
    return jobs

def fetch_detail(post_id):
    ts = int(time.time()*1000)
    url = (f"https://careers.tencent.com/tencentcareer/api/post/ByPostId?"
           f"timestamp={ts}&postId={post_id}&language=zh-cn")
    try:
        d = _get(url)
        return d.get("Data") or {}
    except Exception as e:
        print(f"[WARN] 腾讯详情失败 {post_id}: {e}")
        return {}

def build_desc(detail):
    parts = []
    resp = (detail.get("Responsibility") or "").strip()
    req = (detail.get("Requirement") or "").strip()
    imp = (detail.get("ImportantItem") or "").strip()
    light = (detail.get("PostLightItem") or "").strip()
    if resp:
        parts.append("【岗位职责】\n" + resp)
    if req:
        parts.append("【岗位要求】\n" + req)
    if imp:
        parts.append("【加分项】\n" + imp)
    if light:
        parts.append("【岗位亮点】\n" + light)
    return "\n\n".join(parts)

def normalize(post, detail):
    pu = (post.get("PostURL") or "").strip()
    if pu.startswith("http://"):
        pu = "https://" + pu[len("http://"):]
    if not pu.startswith("http"):
        pu = "https://careers.tencent.com" + pu
    return {
        "company": COMPANY,
        "title": (post.get("RecruitPostName") or "").strip(),
        "location": (post.get("LocationName") or "").strip(),
        "experience": (post.get("RequireWorkYearsName") or "").strip(),
        "description": build_desc(detail) if detail else ((post.get("Responsibility") or "").strip()),
        "date": (detail.get("LastUpdateTime") or post.get("LastUpdateTime") or "").strip(),
        "url": pu,
        "source_url": SOURCE_URL,
    }

def main():
    print(f">>> 腾讯: 抓取产品职位列表 ...")
    posts = fetch_list()
    print(f">>> 列表共 {len(posts)} 个，逐个抓取详情(职责+要求) ...")
    jobs = []
    for i, p in enumerate(posts, 1):
        detail = fetch_detail(p.get("PostId"))
        jobs.append(normalize(p, detail))
        if i % 10 == 0:
            print(f"  已处理 {i}/{len(posts)}")
        time.sleep(0.25)
    # 写 job_digest.md
    today = time.strftime("%Y-%m-%d")
    intro = (f"_腾讯产品类社招职位（北京/上海），按更新时间排序（当日>一周内>一个月内>更早），"
             f"共 {len(jobs)} 个；分页栏可翻页/跳页。_")
    body, total = render_section(COMPANY, jobs, intro=intro)
    write_section(os.path.join(HERE, "job_digest.md"), MARKER,
                  f"{MARKER}（{today}）\n\n" + body)
    # 写出本源数据
    with open(os.path.join(HERE, "jobs_tencent.json"), "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)
    print(f">>> 腾讯完成：{len(jobs)} 个岗位已写入 jobs_tencent.json / job_digest.md")
    return jobs

if __name__ == "__main__":
    main()
