# -*- coding: utf-8 -*-
"""Normalize the 5 raw crawls into a single jobs_data.json with a common schema.

Enhanced schema (v3): keeps richer fields that the source APIs actually return
but the old version dropped — category (岗位类别), type (社招/校招), post_id,
city (拆分), publish_date. Salary stays unavailable because none of the public
list/search endpoints return it (source limitation).
"""
import os, json, re, time
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))

def parse_date(v):
    """Return 'YYYY-MM-DD' or '' from various formats."""
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        # ms timestamp
        if v > 1e12:
            v = v / 1000
        try:
            return datetime.fromtimestamp(v).strftime("%Y-%m-%d")
        except Exception:
            return ""
    s = str(v).strip()
    if not s:
        return ""
    m = re.search(r"(\d{4})[年\-/.](\d{1,2})[月\-/.](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""

REC_TYPE_MAP = {
    "SOCIAL": "社招", "CAMPUS": "校招", "INTERN": "实习",
    "校园招聘": "校招", "社会招聘": "社招", "实习": "实习",
}

def map_type(v):
    if not v:
        return ""
    return REC_TYPE_MAP.get(str(v).upper(), REC_TYPE_MAP.get(str(v), str(v)))

def clean(text):
    """Normalize JD whitespace: unify CRLF/LF, strip, drop zero-width/nbsp junk."""
    if not text:
        return ""
    s = str(text).replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\u200b", "").replace("\u00a0", " ")
    return s.strip()

def norm_tencent(item):
    # crawl_tencent already builds the FULL JD (岗位职责/要求/加分项/亮点) into
    # `description`; keep it verbatim so no section is dropped.
    desc = clean(item.get("description", ""))
    return {
        "title": item.get("title", ""),
        "location": item.get("location", ""),
        "city": item.get("city", "") or item.get("location", ""),
        "experience": item.get("experience", ""),
        # Tencent list/detail APIs do NOT expose education -> source limitation
        "education": item.get("education", "") or "",
        "category": item.get("category", "") or "产品",
        "type": item.get("type", "") or "社招",
        "post_id": item.get("post_id", "") or "",
        "date": parse_date(item.get("date", "")),
        "publish_date": parse_date(item.get("date", "")),
        "description": desc,
        "requirement": "",
        "responsibility": desc,
        "url": item.get("url", ""),
        "source_url": item.get("source_url", ""),
    }

def norm_bytedance(item):
    ci = item.get("city_info") or {}
    loc = ci.get("name") or ""
    cl = item.get("city_list") or []
    if not loc and cl:
        loc = "/".join([c.get("name", "") for c in cl if c.get("name")])
    city = cl[0].get("name", "") if cl else loc
    pub = parse_date(item.get("publish_time"))
    jc = item.get("job_category") or {}
    cat = jc.get("name") or ""
    return {
        "title": item.get("title", ""),
        "location": loc,
        "city": city,
        "experience": "",
        "education": "",
        "category": cat,
        "type": map_type(item.get("recruit_type")),
        "post_id": str(item.get("id", "")),
        "date": pub,
        "publish_date": pub,
        "description": clean(item.get("description")),
        "requirement": clean(item.get("requirement")),
        "responsibility": clean(item.get("description")),
        "url": "https://jobs.bytedance.com/experienced/position/" + str(item.get("id", "")),
        "source_url": "https://jobs.bytedance.com/experienced/position?category=6704215864629004552%2C6704215864591255820%2C6704215924712409352%2C6704216224387041544&location=CT_11%2CCT_188",
    }

def norm_taotian(item, domain, source_list_url):
    exp = item.get("experience") or {}
    f, t = exp.get("from"), exp.get("to")
    if f or t:
        if f and t:
            exp_s = f"{f}-{t}年"
        elif f:
            exp_s = f"{f}年以上" if int(f) > 0 else "经验不限"
        else:
            exp_s = f"{t}年以内"
    else:
        exp_s = ""
    deg = item.get("degree") or ""
    deg_map = {"bachelor": "本科", "master": "硕士", "doctor": "博士", "college": "大专", "": ""}
    deg_s = deg_map.get(deg, deg)
    locs = item.get("workLocations") or []
    loc = "/".join([str(x) for x in locs]) if locs else ""
    city = locs[0] if locs else ""
    pub = parse_date(item.get("publishTime"))
    purl = item.get("positionUrl") or ""
    if purl.startswith("/"):
        purl = "https://" + domain + purl
    return {
        "title": item.get("name", ""),
        "location": loc,
        "city": city,
        "experience": exp_s,
        "education": deg_s,
        "category": item.get("categoryName") or "",
        "type": map_type(item.get("positionType") or item.get("recruitType")),
        "post_id": str(item.get("id", "")),
        "date": pub,
        "publish_date": pub,
        "description": clean(item.get("description")),
        "requirement": clean(item.get("requirement")),
        "responsibility": clean(item.get("description")),
        "url": purl,
        "source_url": source_list_url or ("https://" + domain + "/off-campus/position-list"),
    }

def norm_baidu(item):
    return {
        "title": item.get("name", ""),
        "location": item.get("workPlace", "") or "",
        "city": item.get("workPlace", "") or "",
        "experience": item.get("workYears", "") or "",
        "education": item.get("education", "") or "",
        "category": item.get("postType") or "",
        "type": map_type(item.get("recruitType")) or "社招",
        "post_id": str(item.get("postId", "")),
        "date": parse_date(item.get("publishDate")),
        "publish_date": parse_date(item.get("publishDate")),
        "description": clean(item.get("workContent")),
        "requirement": clean(item.get("serviceCondition")),
        "responsibility": clean(item.get("workContent")),
        "url": "https://talent.baidu.com/detail/social/" + str(item.get("postId", "")),
        "source_url": "https://talent.baidu.com/jobs/social-list",
    }

SOURCES = [
    ("tencent", "腾讯", "jobs_tencent.json", norm_tencent),
    ("bytedance", "字节跳动", "bytedance_raw.json", norm_bytedance),
    ("taotian", "淘天集团", "taotian_raw.json", lambda it: norm_taotian(it, "talent.taotian.com", "https://talent.taotian.com/social/position-list?search=%E4%BA%A7%E5%93%81")),
    ("eleme", "饿了么", "eleme_raw.json", lambda it: norm_taotian(it, "talent.ele.me", "https://talent.ele.me/off-campus/position-list?search=%E4%BA%A7%E5%93%81")),
    ("baidu", "百度", "baidu_raw.json", norm_baidu),
]

def main():
    out = []
    seen = set()
    for key, company, fname, fn in SOURCES:
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            print("missing", path)
            continue
        raw = json.load(open(path, encoding="utf-8"))
        cnt = 0
        for it in raw:
            job = fn(it)
            job["company"] = company
            job["company_key"] = key
            did = (key, job["title"], job["url"])
            if did in seen:
                continue
            seen.add(did)
            out.append(job)
            cnt += 1
        print(f"{company}: {cnt} normalized")
    out.sort(key=lambda j: j["date"] if j["date"] else "0000-00-00", reverse=True)
    today = time.strftime("%Y-%m-%d")
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    for j in out:
        try:
            d = datetime.strptime(j["date"], "%Y-%m-%d")
            j["is_today"] = (d == today_dt)
        except Exception:
            j["is_today"] = False
    data = {
        "generated_at": today,
        "total": len(out),
        "jobs": out,
    }
    with open(os.path.join(HERE, "jobs_data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"TOTAL jobs: {len(out)} -> jobs_data.json")

if __name__ == "__main__":
    main()
