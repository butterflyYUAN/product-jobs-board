# -*- coding: utf-8 -*-
"""Build a self-contained public HTML board from jobs_data.json.

优化点（v2）：
  - 顶部「按公司分 Tab」导航（全部 + 各家 + 数量），点 Tab 立即按公司展示，
    解决「一进去像没岗位、要自己搜」的体验问题。
  - 保留：关键词搜索、时间筛选、分页、JD 展开/收起、高亮、跳转官网。
"""
import os, json, html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "site")
os.makedirs(OUT_DIR, exist_ok=True)

data = json.load(open(os.path.join(HERE, "jobs_data.json"), encoding="utf-8"))
jobs = data["jobs"]
generated = data["generated_at"]

# company color map
COMPANY_COLORS = {
    "腾讯": "#0052d9",
    "字节跳动": "#fe2c55",
    "淘天集团": "#ff6a00",
    "饿了么": "#0085ff",
    "百度": "#2932e1",
}

from collections import Counter
comp_counts = Counter(j["company"] for j in jobs)
today_count = sum(1 for j in jobs if j.get("is_today"))

jobs_compact = []
for i, j in enumerate(jobs):
    jobs_compact.append({
        "i": i,
        "company": j["company"],
        "title": j["title"],
        "location": j.get("location", ""),
        "experience": j.get("experience", ""),
        "education": j.get("education", ""),
        "category": j.get("category", ""),
        "type": j.get("type", ""),
        "post_id": j.get("post_id", ""),
        "date": j.get("date", ""),
        "publish_date": j.get("publish_date", ""),
        "description": j.get("description", ""),
        "requirement": j.get("requirement", ""),
        "url": j.get("url", ""),
        "source_url": j.get("source_url", ""),
        "is_today": bool(j.get("is_today")),
    })

DATA_JSON = json.dumps(jobs_compact, ensure_ascii=False)
companies = [c for c, _ in comp_counts.most_common()]

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>大厂产品岗招聘聚合 · Product Jobs Board</title>
<style>
  :root{
    --bg:#f5f6f8; --card:#ffffff; --ink:#1d2129; --sub:#86909c; --line:#e5e6eb;
    --accent:#0052d9; --tag:#f2f3f5;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
       background:var(--bg);color:var(--ink);line-height:1.6}
  .wrap{max-width:980px;margin:0 auto;padding:0 16px 60px}
  header.hero{background:linear-gradient(135deg,#0052d9,#2b6fed);color:#fff;padding:30px 16px 22px;margin-bottom:0}
  header.hero .inner{max-width:980px;margin:0 auto}
  header.hero h1{margin:0 0 6px;font-size:25px;letter-spacing:.5px}
  header.hero p{margin:0;opacity:.9;font-size:14px}
  .stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
  .stat{background:rgba(255,255,255,.15);border-radius:10px;padding:8px 14px;font-size:13px}
  .stat b{font-size:18px;display:block}

  /* 公司 Tab 栏 */
  .tabs{position:sticky;top:0;z-index:30;background:var(--bg);padding:12px 0 4px;border-bottom:1px solid var(--line)}
  .tabs-inner{max-width:980px;margin:0 auto;padding:0 16px;display:flex;gap:8px;overflow-x:auto}
  .tab{flex:0 0 auto;display:flex;align-items:center;gap:7px;border:1px solid var(--line);background:#fff;
       color:var(--ink);padding:8px 14px;border-radius:999px;font-size:14px;cursor:pointer;user-select:none;
       transition:.15s;white-space:nowrap;font-weight:600}
  .tab:hover{border-color:#c9cdd4}
  .tab .dot{width:8px;height:8px;border-radius:50%;flex:0 0 auto}
  .tab .n{font-size:12px;color:var(--sub);font-weight:600;background:var(--tag);border-radius:999px;padding:1px 7px}
  .tab.active{color:#fff;border-color:transparent}
  .tab.active .n{background:rgba(255,255,255,.25);color:#fff}

  .toolbar{background:var(--bg);padding:12px 0 8px}
  .search{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:10px;font-size:15px;outline:none;background:#fff}
  .search:focus{border-color:var(--accent)}
  .filters{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;align-items:center}
  .chip{border:1px solid var(--line);background:#fff;color:var(--ink);padding:5px 12px;border-radius:999px;
        font-size:13px;cursor:pointer;user-select:none;transition:.15s}
  .chip.active{background:var(--accent);color:#fff;border-color:var(--accent)}
  .chip .n{opacity:.7;font-size:11px;margin-left:4px}
  .meta{color:var(--sub);font-size:13px;margin:12px 2px 4px}
  .cur{color:var(--accent);font-weight:600}

  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px;
        box-shadow:0 1px 2px rgba(0,0,0,.03)}
  .card .top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
  .card h3{margin:0;font-size:17px;line-height:1.4}
  .badge{font-size:12px;color:#fff;padding:3px 9px;border-radius:6px;white-space:nowrap;font-weight:600}
  .today{background:#f53f3f;color:#fff;font-size:12px;padding:2px 7px;border-radius:6px;margin-left:8px}
  .info{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--sub);font-size:13px;margin:8px 0 4px}
  .info span b{color:var(--ink);font-weight:600}
  .tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
  .tag{font-size:12px;padding:3px 9px;border-radius:6px;font-weight:600;white-space:nowrap}
  .tag-cat{background:#e8f3ff;color:#0052d9}
  .tag-type{background:#e8ffea;color:#00a854}
  .jdshow{margin-top:8px;font-size:14px;color:#4e5969;white-space:pre-wrap;word-break:break-word;
          transition:max-height .25s;line-height:1.7}
  .jdshow.clamp{max-height:170px;overflow:hidden;position:relative}
  .jdshow.open{max-height:none}
  .jdshow.clamp:not(.open)::after{content:"";position:absolute;left:0;right:0;bottom:0;height:54px;
          background:linear-gradient(180deg,rgba(255,255,255,0),#fff)}
  .toggle{color:var(--accent);font-size:13px;cursor:pointer;margin-top:4px;user-select:none;display:inline-block}
  .foot{display:flex;justify-content:space-between;align-items:center;margin-top:10px;gap:10px;flex-wrap:wrap}
  .foot a{color:var(--accent);text-decoration:none;font-size:13px;font-weight:600}
  .foot a:hover{text-decoration:underline}
  .src{color:var(--sub);font-size:12px}
  .pager{display:flex;justify-content:center;gap:6px;margin-top:22px;flex-wrap:wrap}
  .pager button{border:1px solid var(--line);background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer;font-size:13px}
  .pager button.active{background:var(--accent);color:#fff;border-color:var(--accent)}
  .pager button:disabled{opacity:.4;cursor:not-allowed}
  .empty{text-align:center;color:var(--sub);padding:50px 0}
  footer{text-align:center;color:var(--sub);font-size:12px;margin-top:30px}
  .hl{background:#fff3a3;border-radius:3px}
</style>
</head>
<body>
<header class="hero"><div class="inner">
  <h1>大厂产品岗招聘聚合</h1>
  <p>腾讯 · 字节跳动 · 淘天集团 · 饿了么 · 百度 — 产品类职位实时聚合看板</p>
  <div class="stats">
    <div class="stat"><b id="stTotal">0</b>在招产品岗</div>
    <div class="stat"><b id="stToday">0</b>今日新发 🔥</div>
    <div class="stat"><b id="stDate"></b>数据日期</div>
  </div>
</div></header>

<!-- 按公司分 Tab -->
<div class="tabs"><div class="tabs-inner" id="tabs"></div></div>

<div class="wrap">
  <div class="toolbar">
    <input id="search" class="search" placeholder="搜索职位名称 / 职责 / 要求 / 城市，如：AI产品、电商、北京…"/>
    <div class="filters" id="timeFilters">
      <span class="chip active" data-time="all">全部时间</span>
      <span class="chip" data-time="today">今日新发 🔥</span>
      <span class="chip" data-time="7">7天内</span>
      <span class="chip" data-time="30">30天内</span>
    </div>
  </div>
  <div class="meta" id="meta"></div>
  <div id="list"></div>
  <div class="pager" id="pager"></div>
  <footer>数据来源于各公司官方招聘网站公开页面，仅作聚合展示，最终以官网为准 · 生成于 <span id="genDate"></span></footer>
</div>

<script>
const JOBS = __DATA__;
const COMPANY_COLORS = __COLORS__;
const companies = __COMPANIES__;
const compCounts = __COMPCOUNTS__;
const PER_PAGE = 20;

// tab: "" = 全部；否则公司名
let state = { q:"", tab:"", time:"all", page:1, expanded:new Set() };

function daysAgo(d){
  if(!d) return 1e9;
  const t = new Date(d); if(isNaN(t)) return 1e9;
  return Math.floor((Date.now()-t)/86400000);
}
function highlight(text, q){
  if(!q || !text) return escapeHtml(text);
  try{
    const re = new RegExp("("+q.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")+")","gi");
    return escapeHtml(text).replace(re,"<span class='hl'>$1</span>");
  }catch(e){ return escapeHtml(text); }
}
function escapeHtml(s){return (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));}

function filtered(){
  const q = state.q.trim().toLowerCase();
  return JOBS.filter(j=>{
    if(state.tab && j.company!==state.tab) return false;
    if(state.time==="today" && !j.is_today) return false;
    if(state.time==="7" && daysAgo(j.date)>7) return false;
    if(state.time==="30" && daysAgo(j.date)>30) return false;
    if(q){
      const hay=(j.title+" "+(j.description||"")+" "+(j.requirement||"")+" "+(j.location||"")+" "+(j.category||"")+" "+(j.type||"")).toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
}

function renderStats(){
  document.getElementById("stTotal").textContent = JOBS.length;
  document.getElementById("stToday").textContent = JOBS.filter(j=>j.is_today).length;
  document.getElementById("stDate").textContent = __GENERATED__;
  document.getElementById("genDate").textContent = __GENERATED__;
}

function renderTabs(){
  const box = document.getElementById("tabs");
  box.innerHTML="";
  const all = [{name:"全部", color:"var(--accent)", count:JOBS.length, key:""}];
  companies.forEach(c=> all.push({name:c, color:COMPANY_COLORS[c]||"#888", count:compCounts[c], key:c}));
  all.forEach(t=>{
    const el=document.createElement("div");
    el.className="tab"+(state.tab===t.key?" active":"");
    if(state.tab===t.key && t.color && t.color!=="var(--accent)") el.style.background=t.color;
    else if(state.tab===t.key) el.style.background="var(--accent)";
    el.innerHTML = (t.key? '<span class="dot" style="background:'+t.color+'"></span>':'') +
                   t.name + '<span class="n">'+t.count+'</span>';
    el.onclick=()=>{ state.tab=t.key; state.page=1; renderTabs(); render(); window.scrollTo({top:0,behavior:"smooth"}); };
    box.appendChild(el);
  });
}

function jdHtml(j){
  // Render the full JD, preserving the source's line breaks (already \n-separated).
  // Tencent descriptions already embed 【岗位职责】/【岗位要求】/【加分项】/【岗位亮点】
  // sections, so show them verbatim; other sources get explicit headers.
  const d = (j.description||"").trim();
  const r = (j.requirement||"").trim();
  const hasSec = /【(岗位)?职责】|【岗位要求】/.test(d);
  const parts = [];
  if(d) parts.push(hasSec ? d : ("【岗位职责】\n"+d));
  if(r && !hasSec) parts.push("【岗位要求】\n"+r);
  return parts.join("\n\n");
}

function cardHtml(j){
  const color = COMPANY_COLORS[j.company]||"#888";
  const info=[];
  if(j.location) info.push("<span><b>城市</b> "+escapeHtml(j.location)+"</span>");
  if(j.experience) info.push("<span><b>经验</b> "+escapeHtml(j.experience)+"</span>");
  if(j.education) info.push("<span><b>学历</b> "+escapeHtml(j.education)+"</span>");
  if(j.publish_date) info.push("<span><b>发布</b> "+escapeHtml(j.publish_date)+"</span>");
  // category / type tags
  let tags="";
  if(j.category) tags+='<span class="tag tag-cat">'+escapeHtml(j.category)+'</span>';
  if(j.type) tags+='<span class="tag tag-type">'+escapeHtml(j.type)+'</span>';
  const q = state.q.trim();
  const body = jdHtml(j);
  const needExpand = body.length>200;
  const open = state.expanded.has(j.i);
  return `<div class="card">
    <div class="top">
      <h3>${highlight(j.title,q)}${j.is_today?'<span class="today">今日新发</span>':''}</h3>
      <span class="badge" style="background:${color}">${escapeHtml(j.company)}</span>
    </div>
    ${tags?('<div class="tags">'+tags+'</div>'):''}
    <div class="info">${info.join("")}</div>
    <div class="jdshow ${needExpand?'clamp':''} ${open?'open':''}" id="jd-${j.i}">${highlight(body,q)}</div>
    ${needExpand?`<span class="toggle" data-i="${j.i}">${open?'收起 ▲':'展开全文 ▼'}</span>`:''}
    <div class="foot">
      <span class="src">来源：${escapeHtml(j.company)}官方招聘</span>
      <a href="${escapeHtml(j.url||'#')}" target="_blank" rel="noopener">查看职位详情 →</a>
    </div>
  </div>`;
}

function render(){
  const list = filtered();
  const meta = document.getElementById("meta");
  const totalPages = Math.max(1, Math.ceil(list.length/PER_PAGE));
  if(state.page>totalPages) state.page=totalPages;
  const start=(state.page-1)*PER_PAGE;
  const pageItems = list.slice(start,start+PER_PAGE);
  const box=document.getElementById("list");
  if(list.length===0){ box.innerHTML='<div class="empty">没有匹配的职位，试试别的关键词或切换公司 Tab～</div>'; }
  else box.innerHTML = pageItems.map(cardHtml).join("");
  const tabLabel = state.tab ? ('「'+state.tab+'」') : '全部公司';
  meta.innerHTML = tabLabel+' 下共 <span class="cur">'+list.length+'</span> 个职位（第 '+state.page+'/'+totalPages+' 页）';
  box.querySelectorAll(".toggle").forEach(t=>{
    t.onclick=()=>{ const i=+t.dataset.i; if(state.expanded.has(i)) state.expanded.delete(i); else state.expanded.add(i); render(); window.scrollTo({top:document.getElementById("jd-"+i).offsetTop-120,behavior:"smooth"}); };
  });
  renderPager(totalPages);
}

function renderPager(tp){
  const p=document.getElementById("pager"); p.innerHTML="";
  if(tp<=1) return;
  const mk=(label,page,dis,act)=>{ const b=document.createElement("button"); b.textContent=label; if(dis)b.disabled=true; if(act)b.className="active"; b.onclick=()=>{state.page=page;render();window.scrollTo({top:0,behavior:"smooth"});}; p.appendChild(b); };
  mk("上一页",state.page-1,state.page===1,false);
  const win=[];
  for(let i=1;i<=tp;i++){ if(i===1||i===tp||Math.abs(i-state.page)<=2) win.push(i); else if(win[win.length-1]!=="…") win.push("…"); }
  win.forEach(i=>{ if(i==="…"){ const s=document.createElement("button"); s.textContent="…"; s.disabled=true; p.appendChild(s);} else mk(i,i,false,i===state.page); });
  mk("下一页",state.page+1,state.page===tp,false);
}

document.getElementById("search").addEventListener("input",e=>{state.q=e.target.value;state.page=1;render();});
document.querySelectorAll("#timeFilters .chip").forEach(c=>{
  c.onclick=()=>{ document.querySelectorAll("#timeFilters .chip").forEach(x=>x.classList.remove("active")); c.classList.add("active"); state.time=c.dataset.time; state.page=1; render(); };
});

renderTabs();
renderStats();
render();
</script>
</body>
</html>
"""

COLORS_JSON = json.dumps(COMPANY_COLORS, ensure_ascii=False)
COMPANIES_JSON = json.dumps(companies, ensure_ascii=False)
COMPCOUNTS_JSON = json.dumps(dict(comp_counts), ensure_ascii=False)

HTML = (HTML
        .replace("__DATA__", DATA_JSON)
        .replace("__COLORS__", COLORS_JSON)
        .replace("__COMPANIES__", COMPANIES_JSON)
        .replace("__COMPCOUNTS__", COMPCOUNTS_JSON)
        .replace("__GENERATED__", json.dumps(generated)))

out = os.path.join(OUT_DIR, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print("wrote", out, "size", os.path.getsize(out), "jobs", len(jobs))
