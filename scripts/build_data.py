# -*- coding: utf-8 -*-
"""Step4: 组装看板数据 dashboard.json"""
import json, os, sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import resolve, generate          # 基准日单一真源，勿再硬编码日期

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
BASE, WINDOW_END, WINDOW_DAYS = resolve()
base_dt = datetime.strptime(BASE, "%Y-%m-%d")

raw = json.load(open(os.path.join(D, "lockup_raw.json"), encoding="utf-8"))
rows = raw["data"]
top30 = json.load(open(os.path.join(D, "top30.json"), encoding="utf-8"))
q = json.load(open(os.path.join(D, "quotes_raw.json"), encoding="utf-8"))
det = json.load(open(os.path.join(D, "picks_detail.json"), encoding="utf-8"))

# ---------- 类型归并 ----------
def cat(t):
    t = t or ""
    if "追加承诺" in t:
        return "追加承诺限售股"
    if "定向增发" in t:
        return "定向增发机构配售"
    if "股权激励" in t or "股权分置" in t:
        return "股权激励/股改"
    if "原股东限售" in t and "战略配售" in t:
        return "原股东+战略配售"
    if "原股东限售" in t:
        return "原股东限售股"
    if "战略配售" in t or "机构配售" in t:
        return "战略/机构配售"
    return "其他"

# ---------- 全量明细（含实时价校准） ----------
# 腾讯行情字段实测校准（SKILL.md 索引 44/45 写反了）：
#   索引 44 = 流通市值(亿)   索引 45 = 总市值(亿)
items = []
for r in rows:
    c = r["SECURITY_CODE"]
    d = datetime.strptime(str(r["FREE_DATE"])[:10], "%Y-%m-%d")
    px_east = r.get("NEW") or 0
    qq = q.get(c) or {}
    px = qq.get("price") or px_east
    sh = r.get("CURRENT_FREE_SHARES") or 0
    items.append({
        "code": c,
        "name": qq.get("name") or r.get("SECURITY_NAME_ABBR") or "",
        "date": d.strftime("%Y-%m-%d"),
        "week": (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d"),
        "days": (d - base_dt).days,
        "raw_type": r.get("FREE_SHARES_TYPE") or "未标注",
        "cat": cat(r.get("FREE_SHARES_TYPE")),
        "shares_wan": sh,                                   # 万股
        "cap_east_yi": (r.get("LIFT_MARKET_CAP") or 0) / 1e4,   # 东财口径解禁市值(亿元)
        "cap_now_yi": sh * px / 1e4 if px else 0,           # 实时价估算(亿元)
        "float_ratio_pct": (r.get("FREE_RATIO") or 0) * 100,      # 占流通盘比例
        "total_ratio_pct": (r.get("TOTALSHARES_RATIO") or 0) * 100,  # 占总股本比例
        "holders": r.get("BATCH_HOLDER_NUM"),
        "px": px, "change_pct": qq.get("change_pct"),
        "pe_ttm": qq.get("pe_ttm"), "pb": qq.get("pb"),
        "mcap_yi": qq.get("float_mcap_yi"),   # 45=总市值(亿) 实测校准
        "float_mcap_yi": qq.get("mcap_yi"),   # 44=流通市值(亿) 实测校准
        "has_quote": bool(qq),
    })

items.sort(key=lambda x: (-x["cap_now_yi"], x["date"]))

# ---------- 概览 ----------
total_cap = sum(i["cap_east_yi"] for i in items)
codes = set(i["code"] for i in items)

# ---------- 周分布 ----------
wk = defaultdict(lambda: {"n": 0, "cap": 0.0, "codes": set()})
for i in items:
    w = wk[i["week"]]
    w["n"] += 1
    w["cap"] += i["cap_east_yi"]
    w["codes"].add(i["code"])
weeks = []
for k in sorted(wk):
    v = wk[k]
    st = datetime.strptime(k, "%Y-%m-%d")
    en = st + timedelta(days=6)
    s2 = max(st, base_dt)
    e2 = min(en, datetime.strptime(WINDOW_END, "%Y-%m-%d"))
    weeks.append({
        "monday": k, "label": st.strftime("%m-%d"),
        "range": f"{s2.strftime('%m-%d')}~{e2.strftime('%m-%d')}",
        "n": v["n"], "cap": round(v["cap"], 2), "codes": len(v["codes"]),
        "complete": st >= base_dt and en <= datetime.strptime(WINDOW_END, "%Y-%m-%d"),
    })
peak = max(weeks, key=lambda w: w["cap"])

# ---------- 类型分布 ----------
tc = defaultdict(lambda: {"n": 0, "cap": 0.0})
for i in items:
    tc[i["cat"]]["n"] += 1
    tc[i["cat"]]["cap"] += i["cap_east_yi"]
types = sorted([{"cat": k, "n": v["n"], "cap": round(v["cap"], 2)}
                for k, v in tc.items()], key=lambda x: -x["cap"])

# ---------- 风险分级 ----------
def risk(i):
    hi = i["float_ratio_pct"] >= 30
    near = i["days"] <= 14
    big = i["cap_now_yi"] >= 100
    if hi and near:
        return "both"
    if hi or big:
        return "high"
    if near:
        return "near"
    return "normal"

for i in items:
    i["risk"] = risk(i)

# ---------- TOP ----------
top = items[:30]
tcap = [{"code": i["code"], "name": i["name"], "cap": round(i["cap_now_yi"], 2),
         "date": i["date"], "ratio": round(i["float_ratio_pct"], 2),
         "risk": i["risk"], "cat": i["cat"]} for i in top]

# ---------- 代表股详情 ----------
picks = []
PICKS = ["601328", "688795", "601088"]
for c in PICKS:
    it = next(i for i in items if i["code"] == c)
    h = det[c]["history"]
    hist = [{
        "date": str(x.get("FREE_DATE"))[:10],
        "shares_wan": x.get("CURRENT_FREE_SHARES") or 0,
        "cap_yi": round((x.get("LIFT_MARKET_CAP") or 0) / 1e4, 2),
        "type": x.get("FREE_SHARES_TYPE") or "",
        "ratio": round((x.get("FREE_RATIO") or 0) * 100, 2),
    } for x in h]
    hist.sort(key=lambda x: x["date"], reverse=True)
    dv = det[c]["dividend"]
    divs = []
    for x in dv:
        ed = str(x.get("EX_DIVIDEND_DATE") or "")[:10]
        if not ed:
            continue
        divs.append({"date": ed, "bonus10": x.get("PRETAX_BONUS_RMB") or 0,
                     "send": x.get("BONUS_RATIO") or 0, "trans": x.get("TRANSFER_RATIO") or 0,
                     "progress": x.get("ASSIGN_PROGRESS") or "",
                     "plan": x.get("IMPL_PLAN_PROFILE") or "",
                     "report": str(x.get("REPORT_DATE") or "")[:10]})
    divs.sort(key=lambda x: x["date"], reverse=True)
    # TTM 股息率：PRETAX_BONUS_RMB 实为「每10股派息(税前)」，需 /10（IMPL_PLAN_PROFILE 已证实）
    cutoff = base_dt - timedelta(days=365)
    ttm10 = sum(d["bonus10"] for d in divs
                if datetime.strptime(d["date"], "%Y-%m-%d") >= cutoff)
    ttm = ttm10 / 10.0
    yld = round(ttm / it["px"] * 100, 2) if it["px"] else None
    picks.append({"code": c, "name": it["name"], "px": it["px"],
                  "cap_yi": round(it["cap_now_yi"], 2), "date": it["date"],
                  "days": it["days"], "ratio": round(it["float_ratio_pct"], 2),
                  "total_ratio": round(it["total_ratio_pct"], 2),
                  "type": it["raw_type"], "shares_wan": it["shares_wan"],
                  "pe_ttm": it["pe_ttm"], "pb": it["pb"],
                  "mcap_yi": it["mcap_yi"], "float_mcap_yi": it["float_mcap_yi"],
                  "change_pct": it["change_pct"],
                  "hist": hist, "divs": divs,
                  "ttm_div": round(ttm, 4), "ttm_div10": round(ttm10, 3),
                  "ttm_yield": yld, "div_count": len(divs)})

out = {
    "meta": {
        "base": BASE, "window_end": WINDOW_END, "generated": generate(),
        "src_lockup": "东方财富数据中心 RPT_LIFT_STAGE（限售解禁）",
        "src_quote": "腾讯财经行情 qt.gtimg.cn",
        "src_div": "东方财富数据中心 RPT_SHAREBONUS_DET（分红送转）",
    },
    "overview": {
        "batches": len(items),
        "codes": len(codes),
        "total_cap": round(total_cap, 2),
        "peak_week": peak["range"], "peak_cap": peak["cap"], "peak_n": peak["n"],
        "first_week": weeks[0]["range"], "first_week_cap": weeks[0]["cap"],
        "near14_n": sum(1 for i in items if i["days"] <= 14),
        "near14_cap": round(sum(i["cap_east_yi"] for i in items if i["days"] <= 14), 2),
        "hi_ratio_n": sum(1 for i in items if i["float_ratio_pct"] >= 30),
        "hi_ratio_cap": round(sum(i["cap_east_yi"] for i in items
                                  if i["float_ratio_pct"] >= 30), 2),
        "max_days": max(i["days"] for i in items),
    },
    "weeks": weeks, "types": types, "top": tcap, "picks": picks,
    "items": items,
}
json.dump(out, open(os.path.join(D, "dashboard.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("批次", len(items), "个股", len(codes), "合计解禁市值", round(total_cap, 2), "亿")
print("高峰周", peak["range"], peak["cap"], "亿", peak["n"], "批")
print("周数", len(weeks), "| 类型", [(t["cat"], t["n"], t["cap"]) for t in types])
print("近14天", out["overview"]["near14_n"], "批", out["overview"]["near14_cap"], "亿")
print("高比例(>=30%)", out["overview"]["hi_ratio_n"], "批", out["overview"]["hi_ratio_cap"], "亿")
for p in picks:
    print(f"  {p['code']} {p['name']} px={p['px']} 解禁{p['cap_yi']}亿 占流通{p['ratio']}% "
          f"历史{len(p['hist'])}条 分红{len(p['divs'])}条 TTM股息率{p['ttm_yield']}%")
