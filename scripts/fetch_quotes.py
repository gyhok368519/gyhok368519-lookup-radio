# -*- coding: utf-8 -*-
"""Step3: 实时行情(腾讯) + 口径终检 + TOP30 + 代表股历史解禁/分红"""
import json, os, time, random, urllib.request
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session(); S.trust_env = False
S.headers.update({"User-Agent": UA, "Referer": "https://data.eastmoney.com/"})
DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(D, exist_ok=True)

_last = [0.0]
def em_get(url, params=None, timeout=20):
    w = 1.0 - (time.time() - _last[0])
    if w > 0:
        time.sleep(w + random.uniform(0.1, 0.4))
    try:
        return S.get(url, params=params, timeout=timeout)
    finally:
        _last[0] = time.time()

def dc(report, filt, size=100, sort="", stype="-1"):
    p = {"reportName": report, "columns": "ALL", "filter": filt, "pageNumber": "1",
         "pageSize": str(size), "sortColumns": sort, "sortTypes": stype,
         "source": "WEB", "client": "WEB"}
    d = em_get(DC, p).json()
    return (d.get("result") or {}).get("data") or []

# ---------- 1. 口径终检（push2 本机网络不可达 -> 容错跳过） ----------
def push2_info(sec):
    try:
        return em_get("https://push2.eastmoney.com/api/qt/stock/get",
                      {"secid": sec, "fields": "f57,f58,f43,f84,f85,f116,f117"}).json().get("data") or {}
    except Exception as e:
        return {"_err": type(e).__name__}

for code, sec in [("601328", "1.601328"), ("688783", "1.688783")]:
    r = push2_info(sec)
    if "_err" in r:
        print(f"[口径] {code} push2 不可达({r['_err']}) -> 改用腾讯行情推导流通股本")
        continue
    print(f"[口径] {code} {r.get('f58')} 现价={r.get('f43')} 总股本={r.get('f84')} "
          f"流通股={r.get('f85')} 流通市值={r.get('f117')}")

# ---------- 2. 腾讯实时行情 ----------
def tx_prefix(c):
    if c.startswith("920") or c.startswith("8") or c.startswith("43"):
        return "bj" + c
    if c.startswith("6") or c.startswith("9"):
        return "sh" + c
    return "sz" + c

def tencent_quote(codes):
    url = "https://qt.gtimg.cn/q=" + ",".join(tx_prefix(c) for c in codes)
    req = urllib.request.Request(url); req.add_header("User-Agent", UA)
    data = urllib.request.urlopen(req, timeout=15).read().decode("gbk")
    out = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        f = lambda i: float(vals[i]) if vals[i] not in ("", "-") else 0.0
        out[key[2:]] = {
            "name": vals[1], "price": f(3), "last_close": f(4), "change_pct": f(32),
            "turnover_pct": f(38), "pe_ttm": f(39), "mcap_yi": f(44),
            "float_mcap_yi": f(45), "pb": f(46), "amount_wan": f(37),
        }
    return out

raw = json.load(open(os.path.join(D, "lockup_raw.json"), encoding="utf-8"))
rows = raw["data"]
top = sorted(rows, key=lambda r: -(r.get("LIFT_MARKET_CAP") or 0))[:30]
codes = [r["SECURITY_CODE"] for r in top]
q = tencent_quote(codes)
print(f"\n[行情] 请求{len(codes)}只, 命中{len(q)}只")
miss = [c for c in codes if c not in q]
print("       未命中:", miss)

# 组装 TOP30 明细
detail = []
for r in top:
    c = r["SECURITY_CODE"]
    qq = q.get(c, {})
    px = qq.get("price") or r.get("NEW") or 0
    shares_wan = r.get("CURRENT_FREE_SHARES") or 0
    cap_now_yi = shares_wan * px / 10000.0            # 万股*元/10000 = 亿元
    float_shares_yi = (qq.get("float_mcap_yi") or 0) / px if px else 0
    ratio_float = (shares_wan / 10000.0) / float_shares_yi * 100 if float_shares_yi else None
    detail.append({
        "code": c, "name": qq.get("name") or r["SECURITY_NAME_ABBR"],
        "date": str(r["FREE_DATE"])[:10], "type": r.get("FREE_SHARES_TYPE"),
        "shares_wan": shares_wan,
        "cap_east_yi": (r.get("LIFT_MARKET_CAP") or 0) / 10000.0,
        "cap_now_yi": cap_now_yi,
        "free_ratio_pct": (r.get("FREE_RATIO") or 0) * 100,
        "total_ratio_pct": (r.get("TOTALSHARES_RATIO") or 0) * 100,
        "ratio_float_rt": ratio_float,
        "price": px, "price_date_ref": r.get("NEW"), "change_pct": qq.get("change_pct"),
        "pe_ttm": qq.get("pe_ttm"), "pb": qq.get("pb"),
        "mcap_yi": qq.get("mcap_yi"), "float_mcap_yi": qq.get("float_mcap_yi"),
        "turnover_pct": qq.get("turnover_pct"),
        "circ_checked": (round(float_shares_yi, 4), round(shares_wan / 10000.0, 4)),
    })
print("\n[TOP30 实时校准] 代码 名称 东财口径亿 -> 实时价亿 | 占流通盘(东财) 占流通盘(实算)")
for d in detail:
    print(f"  {d['code']} {d['name']:<8} {d['cap_east_yi']:>9,.2f} -> {d['cap_now_yi']:>9,.2f} | "
          f"{d['free_ratio_pct']:>8.2f}% {('%.2f%%' % d['ratio_float_rt']) if d['ratio_float_rt'] is not None else 'NA':>9}")

json.dump(detail, open(os.path.join(D, "top30.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(q, open(os.path.join(D, "quotes_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 3. 代表股详情 ----------
PICKS = ["601328", "688795", "601088"]
det = {}
for c in PICKS:
    hist = dc("RPT_LIFT_STAGE", f'(SECURITY_CODE="{c}")', size=40, sort="FREE_DATE")
    div = dc("RPT_SHAREBONUS_DET", f'(SECURITY_CODE="{c}")', size=15, sort="EX_DIVIDEND_DATE")
    det[c] = {"history": hist, "dividend": div}
    print(f"\n[代表股] {c} 历史解禁{len(hist)}条 分红{len(div)}条")
    for h in hist[:8]:
        print(f"    {str(h.get('FREE_DATE'))[:10]} {h.get('CURRENT_FREE_SHARES')}万股 "
              f"{(h.get('LIFT_MARKET_CAP') or 0)/10000:.2f}亿 {h.get('FREE_SHARES_TYPE')} FREE_RATIO={(h.get('FREE_RATIO') or 0)*100:.2f}%")
    for d0 in div[:6]:
        print(f"    分红除权 {str(d0.get('EX_DIVIDEND_DATE'))[:10]} 每股税前 {d0.get('PRETAX_BONUS_RMB')} "
              f"送{d0.get('BONUS_RATIO')} 转{d0.get('TRANSFER_RATIO')} {d0.get('ASSIGN_PROGRESS')}")
json.dump(det, open(os.path.join(D, "picks_detail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 4. 异常记录 ----------
bad = [r for r in rows if not (r.get("LIFT_MARKET_CAP") or 0) > 0 or not (r.get("NEW") or 0) > 0]
print("\n[异常记录]", [(r["SECURITY_CODE"], r["SECURITY_NAME_ABBR"], r.get("NEW"), r.get("LIFT_MARKET_CAP")) for r in bad])
