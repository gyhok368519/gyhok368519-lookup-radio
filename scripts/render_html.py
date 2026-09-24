# -*- coding: utf-8 -*-
"""Step5: 渲染单文件 HTML 雷达（资源全内联，暗色风控预警风）"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import deliverable          # 带日期的产出路径

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
data = json.load(open(os.path.join(D, "dashboard.json"), encoding="utf-8"))
M, OV = data["meta"], data["overview"]
TMAP = {t["cat"]: t for t in data["types"]}
WEEKS = data["weeks"]

# ---------------- 格式化 ----------------
def fc(yi, sign=True):
    p = "¥" if sign else ""
    if yi >= 10000:
        return f"{p}{yi/10000:,.2f}万亿"
    if yi >= 1:
        return f"{p}{yi:,.2f}亿"
    return f"{p}{yi*10000:,.0f}万"

def fs(wan):
    return f"{wan/10000:,.2f}亿股" if wan >= 10000 else f"{wan:,.1f}万股"

def num(v):
    return f"{v:,.0f}"

RISK = {"both": ("🚨", "r-both"), "high": ("🔴", "r-high"),
        "near": ("🟠", "r-near"), "normal": ("🟢", "r-ok")}
ALERT_BATCH = sum(1 for i in data["items"] if i["risk"] != "normal")

# ---------------- SVG: 周分布柱状图 ----------------
def svg_weekly(weeks):
    W, H = 1000, 396
    L, R, T, B = 66, 18, 26, 78
    pw, ph = W - L - R, H - T - B
    mx = max(w["cap"] for w in weeks)
    step = pw / len(weeks)
    bw = step * 0.56
    pk = max(weeks, key=lambda w: w["cap"])
    lo = min(weeks, key=lambda w: w["cap"])
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="未来90天按周解禁市值分布">',
         '<defs>',
         '<linearGradient id="gBar" x1="0" y1="1" x2="0" y2="0">'
         '<stop class="gs-a" offset="0"/><stop class="gs-b" offset="1"/></linearGradient>',
         '<linearGradient id="gPeak" x1="0" y1="1" x2="0" y2="0">'
         '<stop class="gp-a" offset="0"/><stop class="gp-b" offset="1"/></linearGradient>',
         '</defs>']
    for i in range(5):
        v = mx * i / 4
        y = T + ph - ph * i / 4
        p.append(f'<line class="sv-grid" x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}" stroke-width="1"'
                 + (' stroke-dasharray="3 4"' if i else '') + '/>')
        p.append(f'<text class="sv-axis" x="{L-9}" y="{y+4:.1f}" text-anchor="end" font-size="11" '
                 f'font-family="ui-monospace,Consolas,monospace">{v:,.0f}</text>')
    p.append(f'<text class="sv-axis" x="{L-9}" y="{T-9}" text-anchor="end" font-size="10">亿元</text>')
    for i, w in enumerate(weeks):
        h = ph * w["cap"] / mx if mx else 0
        x = L + step * i + (step - bw) / 2
        y = T + ph - h
        isp = w["monday"] == pk["monday"]
        p.append(f'<rect class="sv-bar{" sv-bar-peak" if isp else ""}" '
                 f'x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(h,1):.1f}" rx="2.5">'
                 f'<title>{w["range"]}：{w["n"]} 批 · {fc(w["cap"])} · {w["codes"]} 只个股</title></rect>')
        p.append(f'<text class="{"sv-vpk" if isp else "sv-v"}" x="{x+bw/2:.1f}" y="{y-6:.1f}" '
                 f'text-anchor="middle" font-size="10.5" '
                 f'font-family="ui-monospace,Consolas,monospace">{w["cap"]:,.0f}</text>')
        p.append(f'<text class="{"sv-lpk" if isp else "sv-lb"}" x="{x+bw/2:.1f}" y="{T+ph+17:.1f}" '
                 f'text-anchor="middle" font-size="10.5">{w["label"]}</text>')
        p.append(f'<text class="sv-nb" x="{x+bw/2:.1f}" y="{T+ph+31:.1f}" text-anchor="middle" '
                 f'font-size="9.5">{w["n"]}批</text>')
    p.append(f'<line class="sv-axisline" x1="{L}" y1="{T+ph}" x2="{W-R}" y2="{T+ph}" stroke-width="1.2"/>')
    p.append(f'<text class="sv-note" x="{L}" y="{T+ph+56:.1f}" font-size="11.5" font-weight="600">'
             f'▲ 解禁高峰周 {pk["range"]} · {fc(pk["cap"])} · {pk["n"]} 批　'
             f'<tspan class="sv-note2" font-weight="400">｜　最低周 {lo["range"]} · {fc(lo["cap"])}</tspan></text>')
    p.append('</svg>')
    return "".join(p)

# ---------------- SVG: TOP 条形图 ----------------
def svg_top(top, n=15):
    rows = top[:n]
    W, T, B, rh = 1200, 16, 12, 30
    H = T + B + rh * len(rows)
    L, R = 220, 200
    pw = W - L - R
    mx = max(r["cap"] for r in rows)
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="解禁市值 TOP{n}">']
    for i, r in enumerate(rows):
        y = T + i * rh
        bw = pw * r["cap"] / mx
        k = "h" if r["risk"] in ("both", "high") else ("n" if r["risk"] == "near" else "c")
        p.append(f'<text class="sv-name" x="{L-10}" y="{y+14:.1f}" text-anchor="end" '
                 f'font-size="12.5">{r["name"]}</text>')
        p.append(f'<text class="sv-code" x="{L-10}" y="{y+27:.1f}" text-anchor="end" font-size="10" '
                 f'font-family="ui-monospace,Consolas,monospace">{r["code"]} · {r["date"]}</text>')
        p.append(f'<rect class="sv-tbar sv-tbar-{k}" x="{L}" y="{y+3:.1f}" '
                 f'width="{max(bw,2):.1f}" height="20" rx="3" opacity="0.9">'
                 f'<title>{r["name"]} {r["code"]}：{fc(r["cap"])}，'
                 f'占流通盘 {r["ratio"]:.2f}%，{r["cat"]}</title></rect>')
        p.append(f'<text class="sv-tv-{k}" x="{L+bw+9:.1f}" y="{y+17:.1f}" font-size="11.5" '
                 f'font-family="ui-monospace,Consolas,monospace">{fc(r["cap"])}</text>')
        p.append(f'<text class="sv-right" x="{W-8}" y="{y+17:.1f}" text-anchor="end" '
                 f'font-size="11" font-family="ui-monospace,Consolas,monospace">'
                 f'占流通 {r["ratio"]:.1f}%</text>')
    p.append('</svg>')
    return "".join(p)

# ---------------- SVG: 类型占比环图 ----------------
def svg_donut(types):
    import math
    tot = sum(t["cap"] for t in types) or 1
    cx = cy = 150
    R, r = 104, 62
    a0 = -math.pi / 2
    arcs = []
    for i, t in enumerate(types):
        a1 = a0 + 2 * math.pi * t["cap"] / tot
        large = 1 if (a1 - a0) > math.pi else 0
        x0, y0 = cx + R * math.cos(a0), cy + R * math.sin(a0)
        x1, y1 = cx + R * math.cos(a1), cy + R * math.sin(a1)
        xi1, yi1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        xi0, yi0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        pct = t["cap"] / tot * 100
        arcs.append(f'<path class="sv-seg dp{i%8}" '
                    f'd="M{x0:.1f},{y0:.1f} A{R},{R} 0 {large} 1 {x1:.1f},{y1:.1f} '
                    f'L{xi1:.1f},{yi1:.1f} A{r},{r} 0 {large} 0 {xi0:.1f},{yi0:.1f} Z" '
                    f'stroke-width="2">'
                    f'<title>{t["cat"]}：{t["n"]} 批 · {fc(t["cap"])} · 占比 {pct:.1f}%</title></path>')
        a0 = a1
    donut = (f'<svg viewBox="0 0 300 300" width="100%" role="img" aria-label="解禁类型市值占比">'
             + "".join(arcs)
             + f'<text class="sv-ct" x="{cx}" y="{cy-4}" text-anchor="middle" font-size="13">合计</text>'
             + f'<text class="sv-cv" x="{cx}" y="{cy+19}" text-anchor="middle" font-size="17" '
               f'font-weight="700" font-family="ui-monospace,Consolas,monospace">{fc(tot)}</text></svg>')
    leg = "".join(
        f'<div class="lg-row"><span class="dot dp{i%8}"></span>'
        f'<span class="lg-nm">{t["cat"]}</span><span class="lg-n">{t["n"]}批</span>'
        f'<span class="lg-v">{fc(t["cap"])}</span>'
        f'<span class="lg-p">{t["cap"]/tot*100:.1f}%</span></div>'
        for i, t in enumerate(types))
    return donut, leg

# ---------------- 表格行 ----------------
def tr(i, is_top):
    ic, cls = RISK[i["risk"]]
    chg = i["change_pct"]
    chg_cls = "up" if (chg or 0) > 0 else ("dn" if (chg or 0) < 0 else "")
    chg_txt = f"{chg:+.2f}%" if chg is not None else "—"
    warn = ""
    if i["float_ratio_pct"] >= 30:
        warn += '<span class="tag tg-r">高比例</span>'
    if i["days"] <= 14:
        warn += '<span class="tag tg-o">临近</span>'
    if i["cap_now_yi"] >= 100:
        warn += '<span class="tag tg-a">大额</span>'
    if not i["has_quote"]:
        warn += '<span class="tag tg-b">无行情</span>'
    star = '<span class="star">TOP</span>' if is_top else ""
    rowcls = f"{cls}{' is-top' if is_top else ''}"
    ds = (f'{i["cap_now_yi"]:.4f}|{i["float_ratio_pct"]:.4f}|{i["days"]}|{i["shares_wan"]:.2f}|'
          f'{i["total_ratio_pct"]:.4f}|{i["px"]:.4f}|{(chg or 0):.4f}')
    return (
        f'<tr class="{rowcls}" data-risk="{i["risk"]}" data-cat="{i["cat"]}" data-s="{ds}">'
        f'<td class="c-i" title="{ic}">{ic}</td>'
        f'<td class="c-d"><span class="d-day">{i["date"]}</span><span class="d-left">T+{i["days"]}天</span></td>'
        f'<td class="c-code">{i["code"]}</td>'
        f'<td class="c-nm">{i["name"]}{star}</td>'
        f'<td class="c-ty" title="{i["raw_type"]}">{i["cat"]}</td>'
        f'<td class="num">{fs(i["shares_wan"])}</td>'
        f'<td class="num strong">{fc(i["cap_now_yi"])}</td>'
        f'<td class="num {"hr" if i["float_ratio_pct"] >= 30 else ""}">{i["float_ratio_pct"]:.2f}%</td>'
        f'<td class="num mut">{i["total_ratio_pct"]:.2f}%</td>'
        f'<td class="num">{i["px"]:.2f}</td>'
        f'<td class="num {chg_cls}">{chg_txt}</td>'
        f'<td class="c-w">{warn}</td></tr>')

# ---------------- 代表股卡片 ----------------
def pick_card(p):
    hist_tr = "".join(
        f'<tr><td class="num2">{h["date"]}</td><td class="num2">{fs(h["shares_wan"])}</td>'
        f'<td class="num2">{fc(h["cap_yi"], False)}</td><td class="num2">{h["ratio"]:.1f}%</td>'
        f'<td class="ty2" title="{h["type"]}">{h["type"][:16]}</td></tr>'
        for h in p["hist"][:6])
    if p["divs"]:
        div_tr = "".join(
            f'<tr><td class="num2">{d["date"]}</td>'
            f'<td class="ty2" style="max-width:210px;white-space:nowrap" title="{d["plan"]}">{d["plan"] or ("10派" + str(d["bonus10"]) + "元")}</td>'
            f'<td class="num2">{d["report"]}</td><td class="ty2">{d["progress"]}</td></tr>'
            for d in p["divs"][:6])
    else:
        div_tr = '<tr><td colspan="4" class="empty">暂无已实施分红记录（上市未满完整会计年度或无派息）</td></tr>'
    yld = f'{p["ttm_yield"]:.2f}%' if p["ttm_yield"] is not None else "—"
    chg = p["change_pct"]
    chg_cls = "up" if (chg or 0) > 0 else ("dn" if (chg or 0) < 0 else "")
    return f'''
<div class="pcard">
  <div class="pc-hd">
    <div><span class="pc-nm">{p["name"]}</span><span class="pc-code">{p["code"]}</span></div>
    <div class="pc-px">{p["px"]:.2f}<span class="pc-chg {chg_cls}">{chg:+.2f}%</span></div>
  </div>
  <div class="pc-kv">
    <div><span>解禁日</span><b>{p["date"]}</b></div>
    <div><span>距今</span><b class="o">{p["days"]} 天</b></div>
    <div><span>解禁股数</span><b>{fs(p["shares_wan"])}</b></div>
    <div><span>估算解禁市值</span><b class="r">{fc(p["cap_yi"])}</b></div>
    <div><span>占流通盘</span><b class="r">{p["ratio"]:.2f}%</b></div>
    <div><span>占总股本</span><b>{p["total_ratio"]:.2f}%</b></div>
    <div><span>解禁类型</span><b class="sm">{p["type"]}</b></div>
    <div><span>PE(TTM) / PB</span><b>{p["pe_ttm"]:.1f} / {p["pb"]:.2f}</b></div>
    <div><span>流通市值 / 总市值</span><b>{fc(p["float_mcap_yi"], 0)} / {fc(p["mcap_yi"], 0)}</b></div>
    <div><span>近12月股息率</span><b class="c">{yld}</b><i class="hint">已实施分红 {p["div_count"]} 次</i></div>
  </div>
  <div class="pc-sec"><h4>历史解禁记录（近 6 批）</h4>
    <table class="mini"><thead><tr><th>解禁日</th><th>解禁股数</th><th>解禁市值</th><th>占流通盘</th><th>类型</th></tr></thead>
    <tbody>{hist_tr}</tbody></table>
  </div>
  <div class="pc-sec"><h4>最近分红方案（近 6 次）</h4>
    <table class="mini"><thead><tr><th>除权日</th><th>分配方案</th><th>报告期</th><th>进度</th></tr></thead>
    <tbody>{div_tr}</tbody></table>
  </div>
</div>'''

# ---------------- 组装 ----------------
weekly_svg = svg_weekly(WEEKS)
top_svg = svg_top(data["top"], 15)
donut_svg, donut_leg = svg_donut(data["types"])
top_codes = set(r["code"] for r in data["top"])
table_rows = "".join(tr(i, i["code"] in top_codes) for i in data["items"])
picks_html = "".join(pick_card(p) for p in data["picks"])
type_opts = "".join(f'<option value="{t["cat"]}">{t["cat"]}（{t["n"]}批）</option>' for t in data["types"])
big_n = sum(1 for i in data["items"] if i["cap_now_yi"] >= 100)
RD_ORDER = [("both", "rh", "🚨", "高比例 + 临近"), ("high", "rd", "🔴", "高比例 / 大额"),
            ("near", "ro", "🟠", "临近解禁"), ("normal", "rc", "🟢", "常态")]
_rd = {}
for _i in data["items"]:
    _d = _rd.setdefault(_i["risk"], {"n": 0, "cap": 0.0})
    _d["n"] += 1
    _d["cap"] += _i["cap_east_yi"]
risk_html = "".join(
    f'<div class="rs {cls}"><span class="rs-t">{ic} {nm}</span>'
    f'<b class="rs-v">{num(_rd.get(k, {}).get("n", 0))} 批</b>'
    f'<span class="rs-c">{fc(_rd.get(k, {}).get("cap", 0))}'
    f' · 占 {_rd.get(k, {}).get("cap", 0) / OV["total_cap"] * 100:.1f}%</span></div>'
    for k, cls, ic, nm in RD_ORDER)
pk_n = max(WEEKS, key=lambda w: w["n"])
lo_w = min(WEEKS, key=lambda w: w["cap"])
_wk_sorted = sorted(WEEKS, key=lambda w: w["cap"], reverse=True)
pk2_w = _wk_sorted[1]                   # 次高峰周（压力簇不能写死月份）
C_ORIG_STRAT = TMAP["原股东+战略配售"]["cap"]
C_APPEND = TMAP["追加承诺限售股"]["cap"]
C_EQUITY = TMAP["股权激励/股改"]
COMBO = C_ORIG_STRAT + C_APPEND

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#070b12;--panel:#0d141f;--panel2:#111a27;--line:#1c2839;--line2:#243448;
--txt:#dbe7f3;--txt2:#a9bccf;--mut:#7c8ea6;--dim:#5d7186;
--red:#ff4d4f;--red2:#ff2d55;--orange:#ff8c42;--amber:#ffc53d;--cyan:#22d3ee;--teal:#2dd4bf;
--near:#ff9f43;
--mono:ui-monospace,SFMono-Regular,Consolas,"Cascadia Mono",monospace;
/* --- 主题化 token（白天模式在下方覆盖，勿再写死颜色） --- */
--bg-glow1:rgba(34,211,238,.09);--bg-glow2:rgba(255,77,79,.10);
--hd-grad:linear-gradient(180deg,rgba(13,20,31,.96),rgba(7,11,18,.6));
--hd-grad2:linear-gradient(180deg,rgba(34,211,238,.05),transparent);
--wash:rgba(255,255,255,.018);--wash2:rgba(255,255,255,.022);--wash3:rgba(255,255,255,.012);
--input-bg:#0a121c;--thead-bg:#101927;
--row-line:rgba(28,40,57,.65);--row-line2:rgba(28,40,57,.5);--dash:rgba(36,52,72,.75);
--hover:rgba(34,211,238,.055);--hover2:rgba(34,211,238,.07);--top-bg:rgba(34,211,238,.05);
--rhigh:rgba(255,77,79,.075);--rhigh-h:rgba(255,77,79,.12);
--rboth:rgba(255,45,85,.12);--rboth-h:rgba(255,45,85,.17);--rnear:rgba(255,140,66,.06);
--alarm-tx:#ffb4b5;--rh-v:#ff5c78;--up:#ff4d4f;--dn:#2dd4bf;--star-tx:#0a121c;
--code-bg:rgba(34,211,238,.09);--code-tx:#7fd6e8;
--wb-bg:rgba(255,140,66,.075);--wb-bd:rgba(255,140,66,.32);--wb-tx:#ffcfa8;
--bar1:#0e7490;--bar2:#b91c1c;--glow1:rgba(34,211,238,.4);--glow2:rgba(255,77,79,.4);
--tg-r-bg:rgba(255,77,79,.16);--tg-r-tx:#ff9a9b;--tg-r-bd:rgba(255,77,79,.4);
--tg-o-bg:rgba(255,140,66,.16);--tg-o-tx:#ffbb80;--tg-o-bd:rgba(255,140,66,.4);
--tg-a-bg:rgba(255,197,61,.14);--tg-a-tx:#ffd977;--tg-a-bd:rgba(255,197,61,.36);
--tg-b-bg:rgba(124,142,166,.14);--tg-b-bd:rgba(124,142,166,.35);
/* 内联 SVG 图表语义色 */
--c-grid:#1d2a3c;--c-axis:#6b7f97;--c-axisline:#2b3b52;--c-nb:#5d7186;
--g-bar-a:#0b5c73;--g-bar-b:#22d3ee;--g-peak-a:#8f1d1d;--g-peak-b:#ff7a3d;
--c-v:#7fd6e8;--c-vpk:#ff8c42;--c-lb:#8b9bb0;--c-lpk:#ff8c42;
--c-name:#c7d6e6;--c-code:#66798f;--c-right:#8b9bb0;--c-ct:#7c8ea6;--c-cv:#e6edf3;
--c-seg-stroke:#0d141f;
color-scheme:dark}
html[data-theme="light"]{--bg:#eef3f9;--panel:#ffffff;--panel2:#f7fafd;--line:#dbe4ef;--line2:#c6d3e3;
--txt:#0d1a26;--txt2:#3b4c60;--mut:#526578;--dim:#6b7d92;
--red:#d92c2c;--red2:#c4183a;--orange:#c2410c;--amber:#9a6700;--cyan:#0b6f88;--teal:#0f766e;
--near:#b45309;
--bg-glow1:rgba(11,111,136,.06);--bg-glow2:rgba(217,44,44,.05);
--hd-grad:linear-gradient(180deg,rgba(255,255,255,.97),rgba(238,243,249,.8));
--hd-grad2:linear-gradient(180deg,rgba(11,111,136,.06),transparent);
--wash:rgba(13,26,38,.03);--wash2:rgba(13,26,38,.038);--wash3:rgba(13,26,38,.02);
--input-bg:#ffffff;--thead-bg:#eaf1f8;
--row-line:#e2eaf4;--row-line2:#eaeff7;--dash:#cedae8;
--hover:rgba(11,111,136,.07);--hover2:rgba(11,111,136,.09);--top-bg:rgba(11,111,136,.07);
--rhigh:rgba(217,44,44,.07);--rhigh-h:rgba(217,44,44,.12);
--rboth:rgba(196,24,58,.1);--rboth-h:rgba(196,24,58,.15);--rnear:rgba(194,65,12,.07);
--alarm-tx:#a51b1b;--rh-v:#b01634;--up:#d92c2c;--dn:#0f766e;--star-tx:#ffffff;
--code-bg:rgba(11,111,136,.1);--code-tx:#0b6f88;
--wb-bg:rgba(194,65,12,.07);--wb-bd:rgba(194,65,12,.28);--wb-tx:#8a3a08;
--bar1:#0b6f88;--bar2:#a51b1b;--glow1:rgba(11,111,136,.28);--glow2:rgba(217,44,44,.26);
--tg-r-bg:rgba(217,44,44,.1);--tg-r-tx:#a51b1b;--tg-r-bd:rgba(217,44,44,.32);
--tg-o-bg:rgba(194,65,12,.1);--tg-o-tx:#8a3a08;--tg-o-bd:rgba(194,65,12,.3);
--tg-a-bg:rgba(154,103,0,.1);--tg-a-tx:#7a5200;--tg-a-bd:rgba(154,103,0,.3);
--tg-b-bg:rgba(93,112,134,.1);--tg-b-bd:rgba(93,112,134,.3);
--c-grid:#dbe4ef;--c-axis:#5d7086;--c-axisline:#b9c7d8;--c-nb:#7a8ca1;
--g-bar-a:#b3ecf7;--g-bar-b:#0e7490;--g-peak-a:#ffd2b0;--g-peak-b:#d13b12;
--c-v:#0b6f88;--c-vpk:#b3490a;--c-lb:#4a5c71;--c-lpk:#b3490a;
--c-name:#16283a;--c-code:#5d7086;--c-right:#41536b;--c-ct:#5d7086;--c-cv:#0d1a26;
--c-seg-stroke:#ffffff;
color-scheme:light}
body{background:var(--bg);color:var(--txt);font:14px/1.55 "PingFang SC","Microsoft YaHei",system-ui,-apple-system,sans-serif;
background-image:radial-gradient(900px 500px at 12% -8%,var(--bg-glow1),transparent 60%),radial-gradient(760px 460px at 92% 4%,var(--bg-glow2),transparent 62%);
padding:0 0 40px}
.wrap{max-width:1280px;margin:0 auto;padding:0 18px}
header{position:relative;overflow:hidden;border-bottom:1px solid var(--line);
background:var(--hd-grad)}
.hd-in{max-width:1280px;margin:0 auto;padding:22px 18px 18px;display:flex;gap:22px;align-items:center;flex-wrap:wrap}
.radar{width:76px;height:76px;flex:0 0 76px;border-radius:50%;position:relative;
background:radial-gradient(circle,rgba(34,211,238,.16),rgba(34,211,238,.02) 68%,transparent 70%);
border:1px solid rgba(34,211,238,.45);box-shadow:0 0 22px rgba(34,211,238,.16) inset}
.radar::before,.radar::after{content:"";position:absolute;border-radius:50%;border:1px solid rgba(34,211,238,.28)}
.radar::before{inset:15px}.radar::after{inset:29px}
.sweep{position:absolute;inset:0;border-radius:50%;
background:conic-gradient(from 0deg,rgba(255,77,79,0),rgba(255,77,79,0) 300deg,rgba(255,77,79,.42) 352deg,rgba(255,140,66,.85));
animation:spin 3.4s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.hd-t{flex:1 1 380px}
h1{font-size:23px;letter-spacing:.5px}
h1 em{font-style:normal;color:var(--orange)}
.hd-sub{margin-top:7px;color:var(--txt2);font-size:12.5px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{border:1px solid var(--line2);background:var(--panel2);border-radius:20px;padding:3px 11px;font-size:11.5px;color:var(--txt2);white-space:nowrap}
.chip b{color:var(--cyan);font-weight:600}
.chip.alarm{border-color:rgba(255,77,79,.5);background:rgba(255,77,79,.09);color:var(--alarm-tx)}
.chip.alarm b{color:var(--orange)}
.kpi{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0 12px}
.kpi2{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}
.card{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);
border-radius:10px;padding:13px 15px;position:relative;overflow:hidden}
.card::after{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--cyan);opacity:.75}
.card.r::after{background:var(--red)}.card.o::after{background:var(--orange)}.card.a::after{background:var(--amber)}
.card .k-l{font-size:11.5px;color:var(--mut);letter-spacing:.4px}
.card .k-v{font-size:25px;font-weight:700;font-family:var(--mono);margin:5px 0 2px;line-height:1.1}
.card .k-v.r{color:var(--red)}.card .k-v.o{color:var(--orange)}.card .k-v.c{color:var(--cyan)}.card .k-v.a{color:var(--amber)}
.card .k-s{font-size:11px;color:var(--dim)}
.card.sm .k-v{font-size:19px}
.grid{display:grid;grid-template-columns:2.05fr 1fr;gap:14px;margin-bottom:16px;align-items:start}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.p-hd{display:flex;align-items:center;gap:9px;padding:11px 15px;border-bottom:1px solid var(--line);
background:var(--hd-grad2);flex-wrap:wrap}
.p-hd h2{font-size:14px;font-weight:600;letter-spacing:.3px}
.p-hd .sub{font-size:11px;color:var(--dim);margin-left:auto;font-family:var(--mono)}
.p-bd{padding:14px 15px}
.cwrap{overflow-x:auto}
.cwrap>svg{display:block}
@media(max-width:860px){.cwrap>svg{min-width:700px}}
.bar{width:16px;height:16px;border-radius:3px;background:linear-gradient(135deg,var(--cyan),var(--bar1));box-shadow:0 0 8px var(--glow1)}
.bar.r{background:linear-gradient(135deg,var(--orange),var(--bar2));box-shadow:0 0 8px var(--glow2)}
.lg{display:grid;gap:7px;margin-top:10px}
.lg-row{display:grid;grid-template-columns:10px 1fr auto auto auto;gap:8px;align-items:center;
font-size:12px;padding:5px 7px;border-radius:6px;background:var(--wash)}
.lg-row:hover{background:var(--hover2)}
.dot{width:9px;height:9px;border-radius:2px}
.lg-nm{color:var(--txt2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lg-n{color:var(--dim);font-family:var(--mono);font-size:11px}
.lg-v{color:var(--txt);font-family:var(--mono);font-size:11.5px;min-width:76px;text-align:right}
.lg-p{color:var(--cyan);font-family:var(--mono);font-size:11.5px;min-width:46px;text-align:right}
.donut-wrap{max-width:236px;margin:0 auto 2px}
.rstat{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px;margin-top:15px;padding-top:14px;border-top:1px solid var(--line)}
.rs{background:var(--wash2);border:1px solid var(--line2);border-radius:8px;padding:9px 11px;min-width:0}
.rs-t{font-size:11.5px;color:var(--txt2);display:flex;gap:6px;align-items:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rs-v{display:block;font-family:var(--mono);font-size:15px;font-weight:700;margin-top:5px}
.rs-c{display:block;font-size:10.5px;color:var(--dim);font-family:var(--mono);margin-top:2px}
.rs.rh{border-color:rgba(255,45,85,.45)}.rs.rh .rs-v{color:var(--rh-v)}
.rs.rd{border-color:rgba(255,77,79,.35)}.rs.rd .rs-v{color:var(--red)}
.rs.ro{border-color:rgba(255,140,66,.35)}.rs.ro .rs-v{color:var(--orange)}
.rs.rc{border-color:var(--line2)}.rs.rc .rs-v{color:var(--cyan)}
.tbar{display:flex;gap:9px;flex-wrap:wrap;align-items:center;padding:11px 15px;border-bottom:1px solid var(--line);background:var(--wash3)}
.tbar input,.tbar select{background:var(--input-bg);border:1px solid var(--line2);color:var(--txt);
border-radius:7px;padding:6px 10px;font-size:12.5px;font-family:inherit;outline:none}
.tbar input{width:190px}.tbar input:focus,.tbar select:focus{border-color:var(--cyan)}
.btn{background:var(--input-bg);border:1px solid var(--line2);color:var(--txt2);border-radius:7px;
padding:6px 12px;font-size:12.5px;cursor:pointer;font-family:inherit}
.btn:hover{border-color:var(--cyan);color:var(--cyan)}
.btn.on{background:rgba(255,77,79,.13);border-color:rgba(255,77,79,.55);color:var(--alarm-tx)}
.tbar .cnt{margin-left:auto;font-size:11.5px;color:var(--dim);font-family:var(--mono)}
.tbox{max-height:620px;overflow:auto}
table.tbl{width:100%;border-collapse:collapse;font-size:12.5px}
table.tbl thead th{position:sticky;top:0;z-index:2;background:var(--thead-bg);color:var(--txt2);font-weight:600;
font-size:11.5px;text-align:left;padding:9px;border-bottom:1px solid var(--line2);white-space:nowrap;cursor:pointer}
table.tbl thead th:hover{color:var(--cyan)}
table.tbl thead th.num{text-align:right}
table.tbl td{padding:7px 9px;border-bottom:1px solid var(--row-line);white-space:nowrap;vertical-align:middle}
table.tbl tbody tr:hover{background:var(--hover)}
table.tbl tr.is-top{background:var(--top-bg)}
table.tbl tr.r-high{background:var(--rhigh)}table.tbl tr.r-high:hover{background:var(--rhigh-h)}
table.tbl tr.r-both{background:var(--rboth)}table.tbl tr.r-both:hover{background:var(--rboth-h)}
table.tbl tr.r-near{background:var(--rnear)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.num.strong{color:var(--txt);font-weight:600}
.num.hr{color:var(--red);font-weight:700}
.num.mut{color:var(--mut)}
.up{color:var(--up)}.dn{color:var(--dn)}
.c-i{width:26px;text-align:center}
.c-code{font-family:var(--mono);color:var(--txt2)}
.c-nm{font-weight:500}
.star{display:inline-block;margin-left:6px;font-size:9.5px;color:var(--star-tx);background:var(--cyan);
border-radius:3px;padding:0 4px;vertical-align:1px;font-weight:700}
.d-day{display:block;font-family:var(--mono);font-size:12px}
.d-left{display:block;font-size:10px;color:var(--dim);font-family:var(--mono)}
.c-ty{color:var(--txt2);font-size:11.5px;max-width:150px;overflow:hidden;text-overflow:ellipsis}
.c-w{white-space:nowrap}
.tag{display:inline-block;font-size:10px;border-radius:3px;padding:1px 5px;margin-right:3px;border:1px solid transparent}
.tg-r{background:var(--tg-r-bg);color:var(--tg-r-tx);border-color:var(--tg-r-bd)}
.tg-o{background:var(--tg-o-bg);color:var(--tg-o-tx);border-color:var(--tg-o-bd)}
.tg-a{background:var(--tg-a-bg);color:var(--tg-a-tx);border-color:var(--tg-a-bd)}
.tg-b{background:var(--tg-b-bg);color:var(--mut);border-color:var(--tg-b-bd)}
.picks{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.pcard{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:10px;padding:14px 15px 15px;min-width:0}
.pc-hd{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:10px;border-bottom:1px solid var(--line);gap:8px;flex-wrap:wrap}
.pc-hd>div{min-width:0}
.pc-nm{font-size:16px;font-weight:600}
.pc-code{font-family:var(--mono);font-size:11.5px;color:var(--mut);margin-left:7px}
.pc-px{font-family:var(--mono);font-size:17px;font-weight:700;white-space:nowrap}
.pc-chg{font-size:11.5px;margin-left:6px;font-weight:400}
.pc-kv{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin:11px 0 4px}
.pc-kv>div{display:flex;justify-content:space-between;gap:8px;font-size:11.5px;
border-bottom:1px dashed var(--dash);padding-bottom:4px}
.pc-kv span{color:var(--mut);white-space:nowrap}
.pc-kv b{font-family:var(--mono);font-weight:600;text-align:right}
.pc-kv b.r{color:var(--red)}.pc-kv b.o{color:var(--orange)}.pc-kv b.c{color:var(--cyan)}
.pc-kv b.sm{font-size:10.5px;font-family:inherit;font-weight:500;color:var(--txt2)}
.pc-kv i.hint{display:block;font-size:10px;color:var(--dim);font-style:normal}
.pc-sec{margin-top:13px;overflow-x:auto}
.pc-sec h4{font-size:11.5px;color:var(--txt2);font-weight:600;margin-bottom:6px;letter-spacing:.3px}
table.mini{width:100%;border-collapse:collapse;font-size:11px}
table.mini thead th{color:var(--dim);font-weight:500;text-align:left;padding:4px 5px;border-bottom:1px solid var(--line);font-size:10.5px}
table.mini td{padding:4px 5px;border-bottom:1px solid var(--row-line2);color:var(--txt2)}
table.mini td.num2{font-family:var(--mono);color:var(--txt);white-space:nowrap}
table.mini thead th{white-space:nowrap}
table.mini td.ty2{max-width:96px;overflow:hidden;text-overflow:ellipsis;font-size:10.5px;color:var(--mut)}
table.mini td.empty{color:var(--dim);font-size:10.5px;text-align:center;padding:10px 4px}
.notes{display:grid;grid-template-columns:1.35fr 1fr;gap:14px;margin-top:16px}
.nlist{display:grid;gap:9px}
.nrow{display:flex;gap:9px;font-size:12.5px;color:var(--txt2);line-height:1.65}
.nrow b{color:var(--txt)}
.nrow .mk{color:var(--orange);flex:0 0 auto;font-family:var(--mono)}
.legend{display:grid;gap:8px}
.lg-i{display:flex;gap:9px;align-items:flex-start;font-size:12px;color:var(--txt2);line-height:1.6}
.lg-i .sw{width:11px;height:11px;border-radius:3px;flex:0 0 11px;margin-top:4px}
.lg-i b{color:var(--txt)}
code{font-family:var(--mono);font-size:11px;background:var(--code-bg);color:var(--code-tx);padding:1px 5px;border-radius:3px}
footer{border-top:1px solid var(--line);margin-top:22px;padding:16px 18px 0;color:var(--dim);font-size:11.5px;line-height:1.75}
footer b{color:var(--txt2)}
.warnbar{background:var(--wb-bg);border:1px solid var(--wb-bd);border-radius:9px;
padding:12px 15px;font-size:12.5px;color:var(--wb-tx);margin-top:16px;line-height:1.75}
.warnbar b{color:var(--orange)}
@media(max-width:1080px){.kpi,.kpi2,.picks{grid-template-columns:repeat(2,minmax(0,1fr))}.grid,.notes{grid-template-columns:minmax(0,1fr)}}
@media(max-width:640px){.kpi,.kpi2{grid-template-columns:repeat(2,minmax(0,1fr))}.picks{grid-template-columns:minmax(0,1fr)}
.pc-kv{grid-template-columns:1fr}.wrap{padding:0 11px}.rstat{grid-template-columns:repeat(2,minmax(0,1fr))}
.card .k-v{font-size:19px}.card.sm .k-v{font-size:16px}}
/* ---------- 白天 / 黑夜查看模式 ---------- */
body,.panel,.card,.pcard,.rs,.tbar,.tbox,.nrow,.lg-row,.chip,.btn,.tbtn,input,select,
table.tbl thead th,table.tbl td,table.mini td,.warnbar,footer,.p-hd{
transition:background-color .18s ease,color .18s ease,border-color .18s ease}
.hd-act{flex:0 0 auto;margin-left:auto;display:flex;align-items:center;gap:8px}
.tbtn{display:inline-flex;align-items:center;gap:7px;background:var(--input-bg);
border:1px solid var(--line2);color:var(--txt2);border-radius:20px;padding:7px 14px;
font-size:12.5px;font-family:inherit;cursor:pointer;white-space:nowrap;line-height:1;min-height:34px}
.tbtn:hover{border-color:var(--cyan);color:var(--cyan)}
.tbtn:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.tbtn .tb-ic{font-size:14px;line-height:1}
.ft-warn{color:var(--orange)}
.sw-both{background:var(--red2)}.sw-high{background:var(--red)}
.sw-near{background:var(--orange)}.sw-normal{background:var(--cyan)}
.sw-neu{background:var(--mut)}.sw-amber{background:var(--amber)}
html[data-theme="light"] .radar{border-color:rgba(11,111,136,.4);
background:radial-gradient(circle,rgba(11,111,136,.1),rgba(11,111,136,.02) 68%,transparent 70%)}
html[data-theme="light"] .radar::before,html[data-theme="light"] .radar::after{border-color:rgba(11,111,136,.25)}
/* ---------- 内联 SVG 图表语义类（明暗两套走 token） ---------- */
.sv-grid{stroke:var(--c-grid)}
.sv-axisline{stroke:var(--c-axisline)}
.sv-axis{fill:var(--c-axis)}
.sv-nb{fill:var(--c-nb)}
.sv-ct{fill:var(--c-ct)}
.sv-cv{fill:var(--c-cv)}
.sv-bar{fill:url(#gBar)}
.sv-bar-peak{fill:url(#gPeak)}
.gs-a{stop-color:var(--g-bar-a)}.gs-b{stop-color:var(--g-bar-b)}
.gp-a{stop-color:var(--g-peak-a)}.gp-b{stop-color:var(--g-peak-b)}
.sv-v{fill:var(--c-v)}.sv-vpk{fill:var(--c-vpk)}
.sv-lb{fill:var(--c-lb)}.sv-lpk{fill:var(--c-lpk)}
.sv-note{fill:var(--c-vpk)}.sv-note2{fill:var(--c-nb)}
.sv-name{fill:var(--c-name)}.sv-code{fill:var(--c-code)}.sv-right{fill:var(--c-right)}
.sv-tbar-h,.sv-tv-h{fill:var(--red)}
.sv-tbar-n,.sv-tv-n{fill:var(--near)}
.sv-tbar-c,.sv-tv-c{fill:var(--cyan)}
.sv-seg{stroke:var(--c-seg-stroke)}
.dp0{fill:#ff6b3d;background:#ff6b3d}.dp1{fill:#22d3ee;background:#22d3ee}
.dp2{fill:#a78bfa;background:#a78bfa}.dp3{fill:#ffc53d;background:#ffc53d}
.dp4{fill:#2dd4bf;background:#2dd4bf}.dp5{fill:#ff4d6d;background:#ff4d6d}
.dp6{fill:#5b8def;background:#5b8def}.dp7{fill:#94a3b8;background:#94a3b8}
html[data-theme="light"] .dp0{fill:#d9541c;background:#d9541c}
html[data-theme="light"] .dp1{fill:#0e7490;background:#0e7490}
html[data-theme="light"] .dp2{fill:#6d4fd0;background:#6d4fd0}
html[data-theme="light"] .dp3{fill:#b8860b;background:#b8860b}
html[data-theme="light"] .dp4{fill:#0f9e8e;background:#0f9e8e}
html[data-theme="light"] .dp5{fill:#d61f45;background:#d61f45}
html[data-theme="light"] .dp6{fill:#2f63cf;background:#2f63cf}
html[data-theme="light"] .dp7{fill:#6b7c90;background:#6b7c90}
"""

THEME_INIT = """
/* 在 <head> 里同步执行：先把 data-theme 定下来，避免亮/暗闪烁 */
(function(){
 var t = "dark";
 try { var s = localStorage.getItem("radar-theme"); if (s === "light" || s === "dark") t = s; } catch (e) {}
 document.documentElement.setAttribute("data-theme", t);
})();
"""

JS = """
(function(){
 var rows=[].slice.call(document.querySelectorAll('#tbody tr'));
 var q=document.getElementById('q'),fs=document.getElementById('fs'),fw=document.getElementById('fw'),
     cnt=document.getElementById('cnt'),fbtn=document.getElementById('fbtn'),
     tb=document.querySelectorAll('table.tbl thead th');
 var onlyWarn=false,sortKey=-1,sortDir=-1;
 function vals(r){return r.dataset.s.split('|').map(Number)}
 function apply(){
   var s=(q.value||'').trim().toLowerCase(),f=fs.value,w=fw.value,n=0;
   rows.forEach(function(r){
     var ok=(!s||r.cells[2].textContent.toLowerCase().indexOf(s)>=0||r.cells[3].textContent.toLowerCase().indexOf(s)>=0)
            &&(!f||r.dataset.risk===f)
            &&(!w||r.dataset.cat===w)
            &&(!onlyWarn||r.dataset.risk!=='normal');
     r.style.display=ok?'':'none'; if(ok)n++;
   });
   if(sortKey>=0){
     var vis=rows.filter(function(r){return r.style.display!=='none'});
     vis.sort(function(a,b){return (vals(a)[sortKey]-vals(b)[sortKey])*sortDir});
     var body=document.getElementById('tbody');
     vis.forEach(function(r){body.appendChild(r)});
   }
   cnt.textContent='显示 '+n+' / '+rows.length+' 条'+(onlyWarn?'（仅预警）':'');
 }
 q.addEventListener('input',apply);fs.addEventListener('change',apply);fw.addEventListener('change',apply);
 fbtn.addEventListener('click',function(){onlyWarn=!onlyWarn;fbtn.classList.toggle('on',onlyWarn);apply()});
 var KEYS={1:2,5:3,6:0,7:1,8:4,9:5,10:6};
 tb.forEach(function(th,i){th.addEventListener('click',function(){
   var k=KEYS[i];if(k===undefined)return;
   sortDir=(sortKey===k)?-sortDir:-1;sortKey=k;apply();
 })});
 apply();
 var th=document.querySelectorAll('table.tbl thead th');
 if(th.length){th[6].click()}
})();

/* ---------- 白天 / 黑夜查看模式 ---------- */
(function(){
 var root=document.documentElement,
     btn=document.getElementById('themeBtn'),
     ic=document.getElementById('themeIc'),
     tx=document.getElementById('themeTx');
 if(!btn)return;
 function paint(){
   var dark=root.getAttribute('data-theme')!=='light';
   ic.textContent=dark?'🌙':'☀️';
   tx.textContent=dark?'黑夜':'白天';
   btn.setAttribute('aria-pressed',dark?'false':'true');
   btn.setAttribute('title',dark?'切换到白天模式':'切换到黑夜模式');
 }
 function set(t){
   root.setAttribute('data-theme',t);
   try{localStorage.setItem('radar-theme',t);}catch(e){}
   paint();
 }
 btn.addEventListener('click',function(){
   set(root.getAttribute('data-theme')==='light'?'dark':'light');
 });
 paint();
})();
"""

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A股未来90天限售解禁预警雷达 · 基准日 {M['base']}</title>
<meta name="color-scheme" content="dark light">
<script>{THEME_INIT}</script>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="hd-in">
    <div class="radar"><div class="sweep"></div></div>
    <div class="hd-t">
      <h1>A股 <em>未来 90 天限售解禁预警雷达</em></h1>
      <div class="hd-sub">
        <span class="chip">基准日 <b>{M['base']}</b></span>
        <span class="chip">扫描窗口 <b>{M['base']} → {M['window_end']}</b></span>
        <span class="chip">数据源 <b>东方财富数据中心</b></span>
        <span class="chip alarm">预警批次 <b>{num(ALERT_BATCH)}</b> 批（高比例 / 大额 / 临近）</span>
      </div>
    </div>
    <div class="hd-act">
      <button class="tbtn" id="themeBtn" type="button" aria-pressed="false"
              aria-label="切换白天 / 黑夜查看模式" title="切换白天 / 黑夜查看模式">
        <span class="tb-ic" id="themeIc" aria-hidden="true">🌙</span>
        <span class="tb-tx" id="themeTx">黑夜</span>
      </button>
    </div>
  </div>
</header>

<div class="wrap">

  <div class="kpi">
    <div class="card"><div class="k-l">待解禁批次</div><div class="k-v c">{num(OV['batches'])}<span style="font-size:13px;color:var(--mut)"> 批</span></div><div class="k-s">覆盖 {OV['max_days']} 个自然日</div></div>
    <div class="card"><div class="k-l">涉及个股</div><div class="k-v c">{num(OV['codes'])}<span style="font-size:13px;color:var(--mut)"> 只</span></div><div class="k-s">沪深京全市场</div></div>
    <div class="card r"><div class="k-l">合计解禁市值</div><div class="k-v r">{fc(OV['total_cap'])}</div><div class="k-s">解禁股数 × 参考价</div></div>
    <div class="card o"><div class="k-l">解禁高峰周</div><div class="k-v o" style="font-size:19px">{OV['peak_week']}</div><div class="k-s">{fc(OV['peak_cap'])} · {OV['peak_n']} 批</div></div>
  </div>

  <div class="kpi2">
    <div class="card sm o"><div class="k-l">最近 14 天内解禁</div><div class="k-v o">{num(OV['near14_n'])} 批</div><div class="k-s">{fc(OV['near14_cap'])} · 窗口首周 {OV['first_week']} {fc(OV['first_week_cap'])}</div></div>
    <div class="card sm r"><div class="k-l">高比例解禁（占流通盘 ≥30%）</div><div class="k-v r">{num(OV['hi_ratio_n'])} 批</div><div class="k-s">{fc(OV['hi_ratio_cap'])} · 占合计 {OV['hi_ratio_cap']/OV['total_cap']*100:.1f}%</div></div>
    <div class="card sm a"><div class="k-l">大额解禁（单批 ≥100 亿）</div><div class="k-v a">{num(big_n)} 批</div><div class="k-s">单批解禁市值超百亿</div></div>
    <div class="card sm"><div class="k-l">单周最多批次</div><div class="k-v c">{num(pk_n['n'])} 批</div><div class="k-s">{pk_n['range']} · 涉及 {pk_n['codes']} 只个股</div></div>
  </div>

  <div class="grid">
    <div class="panel">
      <div class="p-hd"><span class="bar"></span><h2>未来 90 天按周解禁市值分布</h2>
        <span class="sub">单位 亿元 · 橙红柱 = 解禁高峰周 · 柱下数字为当周批次</span></div>
      <div class="p-bd"><div class="cwrap">{weekly_svg}</div><div class="rstat">{risk_html}</div></div>
    </div>
    <div class="panel">
      <div class="p-hd"><span class="bar r"></span><h2>解禁类型市值占比</h2><span class="sub">按解禁市值</span></div>
      <div class="p-bd"><div class="donut-wrap">{donut_svg}</div><div class="lg">{donut_leg}</div></div>
    </div>
  </div>

  <div class="panel" style="margin-bottom:16px">
    <div class="p-hd"><span class="bar r"></span><h2>解禁市值 TOP15（按最新价估算）</h2>
      <span class="sub">红 = 高比例/大额 · 橙 = 临近解禁 · 青 = 常态</span></div>
    <div class="p-bd"><div class="cwrap">{top_svg}</div></div>
  </div>

  <div class="panel" style="margin-bottom:16px">
    <div class="p-hd"><span class="bar r"></span><h2>代表个股详情</h2>
      <span class="sub">历史解禁轨迹 + 最近分红方案（3 只对比：国资大行 / 次新科技 / 红利蓝筹）</span></div>
    <div class="p-bd"><div class="picks">{picks_html}</div></div>
  </div>

  <div class="panel">
    <div class="p-hd"><span class="bar"></span><h2>全市场待解禁明细（{num(OV['batches'])} 批）</h2>
      <span class="sub">点击表头排序 · 默认按解禁市值降序</span></div>
    <div class="tbar">
      <input id="q" placeholder="搜索代码 / 简称…">
      <select id="fs">
        <option value="">全部风险等级</option>
        <option value="both">🚨 高比例 + 临近</option>
        <option value="high">🔴 高比例 / 大额</option>
        <option value="near">🟠 临近解禁（≤14天）</option>
        <option value="normal">🟢 常态</option>
      </select>
      <select id="fw"><option value="">全部解禁类型</option>{type_opts}</select>
      <button class="btn" id="fbtn">只看预警标的</button>
      <span class="cnt" id="cnt"></span>
    </div>
    <div class="tbox">
      <table class="tbl">
        <thead><tr>
          <th class="c-i">风</th><th>解禁日</th><th>代码</th><th>简称</th><th>解禁类型</th>
          <th class="num">解禁股数</th><th class="num">估算解禁市值</th><th class="num">占流通盘</th>
          <th class="num">占总股本</th><th class="num">最新价</th><th class="num">涨跌幅</th><th>预警</th>
        </tr></thead>
        <tbody id="tbody">{table_rows}</tbody>
      </table>
    </div>
  </div>

  <div class="notes">
    <div class="panel">
      <div class="p-hd"><span class="bar r"></span><h2>关键发现 &amp; 风控提示</h2></div>
      <div class="p-bd"><div class="nlist">
        <div class="nrow"><span class="mk">01</span><span><b>总量：</b>未来 90 天（{M['base']} ~ {M['window_end']}）全市场共 <b>{num(OV['batches'])}</b> 批待解禁，涉及 <b>{num(OV['codes'])}</b> 只个股，合计解禁市值 <b>{fc(OV['total_cap'])}</b>，属年内压力偏重的解禁窗口。</span></div>
        <div class="nrow"><span class="mk">02</span><span><b>节奏极不均匀：</b>高峰周 <b>{OV['peak_week']}</b> 单周解禁 <b>{fc(OV['peak_cap'])}</b>（{OV['peak_n']} 批），是最低周 {lo_w['range']}（{fc(lo_w['cap'])}）的 <b>{OV['peak_cap']/max(lo_w['cap'],1):.0f} 倍</b>；次高峰 {pk2_w['range']}（{fc(pk2_w['cap'])}，{pk2_w['n']} 批）与高峰周构成两个显著压力簇。</span></div>
        <div class="nrow"><span class="mk">03</span><span><b>风险集中在"高比例"：</b>占流通盘 ≥30% 的 <b>{num(OV['hi_ratio_n'])}</b> 批合计 <b>{fc(OV['hi_ratio_cap'])}</b>，占全部解禁市值 <b>{OV['hi_ratio_cap']/OV['total_cap']*100:.1f}%</b>。科创板次新股与北交所个股因流通盘小，解禁比例常超 100%，是冲击弹性最大的部分。</span></div>
        <div class="nrow"><span class="mk">04</span><span><b>类型：原股东限售 + 追加承诺是主力。</b>「原股东+战略配售」{fc(C_ORIG_STRAT)}、「追加承诺限售股」{fc(C_APPEND)}，两者合计 <b>{fc(COMBO)}</b>，占合计解禁市值 <b>{COMBO/OV['total_cap']*100:.1f}%</b>。股权激励类批次最多（<b>{num(C_EQUITY['n'])}</b> 批）但市值仅 {fc(C_EQUITY['cap'])}，实际冲击有限。</span></div>
        <div class="nrow"><span class="mk">05</span><span><b>大市值 ≠ 高减持概率。</b>交通银行（{fc(data['picks'][0]['cap_yi'])}，占流通盘 {data['picks'][0]['ratio']:.1f}%）与中国神华（{fc(data['picks'][2]['cap_yi'])}，占流通盘仅 {data['picks'][2]['ratio']:.1f}%）限售方均为国资，规模大但减持意愿通常低；{data['picks'][1]['name']}（占流通盘 {data['picks'][1]['ratio']:.0f}%）等次新科技股原始股东多为财务投资人，减持概率显著更高。<b>重点跟踪减持计划公告，而非解禁表本身。</b></span></div>
      </div></div>
    </div>
    <div class="panel">
      <div class="p-hd"><span class="bar"></span><h2>预警规则 &amp; 口径说明</h2></div>
      <div class="p-bd"><div class="legend">
        <div class="lg-i"><span class="sw sw-both"></span><span><b>🚨 高比例 + 临近</b>：占流通盘 ≥30% 且 解禁日距今 ≤14 天，双重压力叠加</span></div>
        <div class="lg-i"><span class="sw sw-high"></span><span><b>🔴 高比例 / 大额</b>：占流通盘 ≥30% 或 单批解禁市值 ≥100 亿</span></div>
        <div class="lg-i"><span class="sw sw-near"></span><span><b>🟠 临近解禁</b>：解禁日距今 ≤14 天（未叠加高比例）</span></div>
        <div class="lg-i"><span class="sw sw-normal"></span><span><b>🟢 常态</b>：其余批次</span></div>
        <div class="lg-i"><span class="sw sw-neu"></span><span><b>口径：</b>「解禁股数」单位 万股 / 亿股；「估算解禁市值」= 解禁股数 × 最新价（与东财口径一致）；「占流通盘」= 解禁股数 ÷ 流通股本（东财 <code>FREE_RATIO</code>，可 &gt;100%）；「占总股本」= 解禁股数 ÷ 总股本（<code>TOTALSHARES_RATIO</code>）。</span></div>
        <div class="lg-i"><span class="sw sw-amber"></span><span><b>颜色约定：</b>红涨绿跌（A股习惯）——涨跌幅列 <span class="up">红 = 上涨</span> / <span class="dn">绿 = 下跌</span>。</span></div>
      </div></div>
    </div>
  </div>

  <div class="warnbar">
    <b>使用须知：</b>解禁（限售股上市流通）仅代表股份变得可交易，<b>不等于股东会立即减持</b>。实际抛压取决于限售方性质（国资 / 产业资本 / 财务投资人）、减持新规约束、股价位置与公司公告。请以交易所披露的<b>减持计划公告</b>为准，本页仅作解禁排期与压力分布的线索提示。<br>
    <b>数据口径：</b>解禁数据取自东方财富数据中心 <code>RPT_LIFT_STAGE</code>，筛选条件为解禁日期落在 <b>{M['base']} ~ {M['window_end']}</b>；行情为腾讯财经最新收盘快照；分红取自东方财富 <code>RPT_SHAREBONUS_DET</code>，其中 <code>PRETAX_BONUS_RMB</code> 已按「每 10 股派息」口径换算为每股。北交所个股 <code>920201</code>（百瑞吉）暂无参考价，市值计 0，但仍计入批次与个股数。
  </div>
</div>

<footer>
  <div class="wrap">
    <b>数据来源</b>：东方财富数据中心（限售解禁 <code>RPT_LIFT_STAGE</code> / 分红送转 <code>RPT_SHAREBONUS_DET</code>）· 腾讯财经行情（qt.gtimg.cn）&nbsp;|&nbsp;
    <b>基准日</b>：{M['base']}（扫描窗口 {M['base']} ~ {M['window_end']}）&nbsp;|&nbsp;
    <b>生成时间</b>：{M['generated']}
    <div style="margin-top:7px">
      本页由 WorkBuddy「A股全栈数据」技能（a-stock-data v3.2.3）抓取真实数据生成，资源全内联、可离线打开。金额单位 ¥ / 亿 / 万，股数单位 万股 / 亿股。
    </div>
    <div class="ft-warn" style="margin-top:9px">⚠️ <b>非投资建议，解禁不必然导致下跌。</b>本页内容基于公开数据统计整理，仅供研究参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。</div>
  </div>
</footer>

<script>{JS}</script>
</body>
</html>
"""

OUT = [os.path.join(HERE, "..", "解禁预警雷达.html"),
       deliverable("lockup-radar-90d", "html", M["base"])]
for p in OUT:
    ap = os.path.abspath(p)
    os.makedirs(os.path.dirname(ap), exist_ok=True)
    open(ap, "w", encoding="utf-8").write(HTML)
    print("written:", ap, len(HTML), "bytes")
