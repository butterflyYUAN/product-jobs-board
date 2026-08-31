# -*- coding: utf-8 -*-
"""Normalize the 5 raw crawls into a single jobs_data.json with a common schema."""
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

def split_tencent_desc(text):
    """Split combined Tencent description into (responsibility, requirement)."""
    if not text:
        return "", ""
    resp, req = "", ""
    # requirement marker
    rm = re.search(r"【岗位要求】", text)
    if rm:
        before = text[:rm.start()].strip()
        after = text[rm.end():].strip()
        # responsibility may also have its own marker
        rrm = re.search(r"【岗位职责】", before)
        resp = (before[rrm.end():] if rrm else before).strip() if rrm else before
        # strip trailing extra sections from requirement
        for mk in ["【加分项】", "【岗位亮点】"]:
            idx = after.find(mk)
            if idx != -1:
                after = after[:idx].strip()
                break
        req = after.strip()
    else:
        resp = text
    return resp, req

def norm_tencent(item):
    desc = item.get("description", "") or ""
    resp, req = split_tencent_desc(desc)
    return {
        "title": item.get("title", ""),
        "location": item.get("location", ""),
        "experience": item.get("experience", ""),
        "education": "",
        "date": parse_date(item.get("date", "")),
        "description": resp,
        "requirement": req,
        "url": item.get("url", ""),
        "source_url": item.get("source_url", ""),
    }

def norm_bytedance(item):
    ci = item.get("city_info") or {}
    loc = ci.get("name") or ""
    cl = item.get("city_list") or []
    if not loc and cl:
        loc = "/".join([c.get("name", "") for c in cl if c.get("name")])
    pub = parse_date(item.get("publish_time"))
    return {
        "title": item.get("title", ""),
        "location": loc,
        "experience": "",
        "education": "",
        "date": pub,
        "description": (item.get("description") or "").strip(),
        "requirement": (item.get("requirement") or "").strip(),
        "url": "https://jobs.bytedance.com/experienced/position/" + str(item.get("id", "")),
        "source_url": "https://jobs.bytedance.com/experienced/position?category=6704215864629004552%2C6704215864591255820%2C6704215924712409352%2C6704216224387041544&location=CT_11%2CCT_188",
    }

def norm_taotian(item, domain):
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
    pub = parse_date(item.get("publishTime"))
    purl = item.get("positionUrl") or ""
    if purl.startswith("/"):
        purl = "https://" + domain + purl
    return {
        "title": item.get("name", ""),
        "location": loc,
        "experience": exp_s,
        "education": deg_s,
        "date": pub,
        "description": (item.get("description") or "").strip(),
        "requirement": (item.get("requirement") or "").strip(),
        "url": purl,
        "source_url": "https://" + domain + "/off-campus/position-list",
    }

def norm_baidu(item):
    return {
        "title": item.get("name", ""),
        "location": item.get("workPlace", "") or "",
        "experience": item.get("workYears", "") or "",
        "education": item.get("education", "") or "",
        "date": parse_date(item.get("publishDate")),
        "description": (item.get("workContent") or "").strip(),
        "requirement": (item.get("serviceCondition") or "").strip(),
        "url": "https://talent.baidu.com/detail/social/" + str(item.get("postId", "")),
        "source_url": "https://talent.baidu.com/jobs/social-list",
    }

SOURCES = [
    ("tencent", "腾讯", "jobs_tencent.json", norm_tencent),
    ("bytedance", "字节跳动", "bytedance_raw.json", norm_bytedance),
    ("taotian", "淘天集团", "taotian_raw.json", lambda it: norm_taotian(it, "talent.taotian.com")),
    ("eleme", "饿了么", "eleme_raw.json", lambda it: norm_taotian(it, "talent.ele.me")),
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
            # dedupe
            did = (key, job["title"], job["url"])
            if did in seen:
                continue
            seen.add(did)
            out.append(job)
            cnt += 1
        print(f"{company}: {cnt} normalized")
    # date sort: unknown dates last
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
