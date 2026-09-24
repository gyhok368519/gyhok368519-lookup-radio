# -*- coding: utf-8 -*-
"""Step1: 全市场未来90天解禁全量抓取 + 字段口径交叉校验"""
import json, os, time, random, sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import resolve, save          # 基准日单一真源，勿再硬编码日期

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": UA, "Referer": "https://data.eastmoney.com/"})

DC = "https://datacenter-web.eastmoney.com/api/data/v1/get"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(OUT, exist_ok=True)

_last = [0.0]
def em_get(url, params=None, timeout=20):
    w = 1.0 - (time.time() - _last[0])
    if w > 0:
        time.sleep(w + random.uniform(0.1, 0.4))
    try:
        return S.get(url, params=params, timeout=timeout)
    finally:
        _last[0] = time.time()

def dc(report, filt, size=500, page=1, sort="FREE_DATE", stype="1"):
    p = {"reportName": report, "columns": "ALL", "filter": filt,
         "pageNumber": str(page), "pageSize": str(size),
         "sortColumns": sort, "sortTypes": stype, "source": "WEB", "client": "WEB"}
    r = em_get(DC, p)
    d = r.json()
    res = d.get("result") or {}
    return res.get("data") or [], res.get("count"), res.get("pages")

BASE, END, WINDOW_DAYS = resolve()
save(BASE, END)          # 写回参数文件，供后续步骤读取
print("[参数] 基准日={} 窗口={} ~ {}（{} 天）".format(BASE, BASE, END, WINDOW_DAYS))

# ---------- A. 全量解禁 ----------
rows, cnt, pages = dc("RPT_LIFT_STAGE", f"(FREE_DATE>='{BASE}')(FREE_DATE<='{END}')", size=500)
print(f"[A] 全市场解禁: count={cnt} pages={pages} fetched={len(rows)}")
if cnt and len(rows) < cnt:
    for pg in range(2, (pages or 1) + 1):
        more, _, _ = dc("RPT_LIFT_STAGE", f"(FREE_DATE>='{BASE}')(FREE_DATE<='{END}')", size=500, page=pg)
        rows += more
        if len(more) < 500:
            break
    print(f"[A] 补页后 fetched={len(rows)}")

with open(os.path.join(OUT, "lockup_raw.json"), "w", encoding="utf-8") as f:
    json.dump({"base": BASE, "end": END, "count": cnt, "data": rows}, f, ensure_ascii=False, indent=1)

# ---------- B. 口径交叉校验（可选：push2 不可达时自动跳过） ----------
# 注意：本机 push2.eastmoney.com / push2delay 在网络层不可达（RemoteDisconnected）。
# 这一段只做打印校验、下游任何步骤都不依赖它，因此失败仅告警、绝不中断。
# 真正的口径结论由 fetch_quotes.py 用腾讯行情 + 东财 TOTAL_SHARES 二次验证。
def push2_info(code):
    secid = ("1." if code[0] in "65" else "0.") + code
    r = em_get("https://push2.eastmoney.com/api/qt/stock/get",
               {"secid": secid, "fields": "f57,f58,f43,f84,f85,f116,f117,f162,f167"})
    return r.json().get("data") or {}


try:
    for c in ["603500", "600426"]:
        info = push2_info(c)
        rec = next((x for x in rows if x["SECURITY_CODE"] == c), None)
        print(f"\n[B] {c} {info.get('f58')}")
        print(f"    push2 f43现价={info.get('f43')} f84总股本={info.get('f84')} f85流通股={info.get('f85')} "
              f"f116总市值={info.get('f116')} f117流通市值={info.get('f117')}")
        if rec:
            print(f"    解禁行 NEW={rec['NEW']} CURRENT_FREE_SHARES={rec['CURRENT_FREE_SHARES']} "
                  f"FREE_SHARES={rec['FREE_SHARES']} LIFT_MARKET_CAP={rec['LIFT_MARKET_CAP']} "
                  f"FREE_RATIO={rec['FREE_RATIO']} TOTALSHARES_RATIO={rec['TOTALSHARES_RATIO']}")
            print(f"    校验 CURRENT_FREE_SHARES*NEW = {rec['CURRENT_FREE_SHARES']*rec['NEW']:.2f} "
                  f"vs LIFT_MARKET_CAP={rec['LIFT_MARKET_CAP']}")
except Exception as e:
    print(f"[B] push2 交叉校验跳过（{type(e).__name__}，本机该域名不可达）"
          f"—— 不影响数据正确性，口径已由 fetch_quotes.py 二次验证")
