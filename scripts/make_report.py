# -*- coding: utf-8 -*-
"""Step6: 生成配套 Markdown 报告"""
import json, os, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import deliverable          # 带日期的产出路径

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "data")
data = json.load(open(os.path.join(D, "dashboard.json"), encoding="utf-8"))
M, OV, W = data["meta"], data["overview"], data["weeks"]
TM = {t["cat"]: t for t in data["types"]}

def fc(yi):
    if yi >= 10000:
        return f"¥{yi/10000:,.2f}万亿"
    if yi >= 1:
        return f"¥{yi:,.2f}亿"
    return f"¥{yi*10000:,.0f}万"

def fs(wan):
    return f"{wan/10000:,.2f}亿股" if wan >= 10000 else f"{wan:,.1f}万股"

pk = max(W, key=lambda w: w["cap"])
lo = min(W, key=lambda w: w["cap"])
_sorted = sorted(W, key=lambda w: w["cap"], reverse=True)
pk2 = _sorted[1]                        # 次高峰周
pk3 = _sorted[2]                        # 第三高峰周


def _d(s, delta=0):
    """基准日派生的 MM-DD，避免把月份写死在文案里。"""
    return (datetime.strptime(str(s)[:10], "%Y-%m-%d")
            + timedelta(days=delta)).strftime("%m-%d")


RAW_N = len(json.load(open(os.path.join(D, "lockup_raw.json"),
                           encoding="utf-8"))["data"])
FNAME = "lockup-radar-90d-" + M["base"]
hi = OV["hi_ratio_cap"] / OV["total_cap"] * 100
combo = TM["原股东+战略配售"]["cap"] + TM["追加承诺限售股"]["cap"]
eq = TM["股权激励/股改"]

L = []
A = L.append
A("# A股「未来 90 天限售解禁预警雷达」")
A("")
A(f"**日期**：{M['generated']}")
A("**报告类型**：解禁排期数据雷达（全市场扫描 + 可视化）")
A(f"**分析标的/主题**：A股全市场（沪深京）未来 90 天限售解禁，窗口 {M['base']} ~ {M['window_end']}")
A("**参与成员**：主理人（数据工程与可视化）。本任务为「真实数据抓取 + 单页可视化交付」，"
  "非个股/市场/组合/宏观研判，故未调度 7 位分析成员；报告内所有数字均为东财原始字段的统计结果，不含主观投资判断。")
A("")
A("---")
A("")
A("## 📌 TL;DR（一句话核心结论 + 3 行依据）")
A("")
A(f"- **核心结论**：未来 90 天全市场有 **{OV['batches']} 批** 限售股解禁、涉及 **{OV['codes']} 只** 个股、"
  f"合计解禁市值 **{fc(OV['total_cap'])}**；压力高度集中，**{hi:.1f}%** 的市值来自「占流通盘 ≥30%」的 "
  f"{OV['hi_ratio_n']} 批，高峰落在 **{pk['range']}**（{fc(pk['cap'])}，{pk['n']} 批）。")
A(f"- **关键依据**：① 单周峰值 {fc(pk['cap'])} 是最低周（{lo['range']}，{fc(lo['cap'])}）的 "
  f"**{pk['cap']/max(lo['cap'],1):.0f} 倍**，节奏极不均匀；② 「原股东+战略配售」+「追加承诺限售股」合计 "
  f"{fc(combo)}，占 {combo/OV['total_cap']*100:.1f}%，是绝对主力；③ 科创板次新与北交所个股解禁比例常超 100%"
  f"（流通盘小），弹性最大。")
A("- **建议动作**：🟡 观望 —— 不因解禁表做买卖决策，转为「盯公告」：对接近解禁日且高比例的标的，"
  "跟踪其**减持计划公告**与三季报窗口。")
A("")
A("---")
A("")
A("## 🎯 核心结论卡片")
A("")
A("| 项目 | 内容 |")
A("|------|------|")
A(f"| 待解禁批次 | {OV['batches']} 批（{OV['max_days']} 个自然日） |")
A(f"| 涉及个股 | {OV['codes']} 只（沪深京全市场） |")
A(f"| 合计解禁市值 | {fc(OV['total_cap'])} |")
A(f"| 解禁高峰周 | {pk['range']} · {fc(pk['cap'])} · {pk['n']} 批 |")
A(f"| 最近 14 天内解禁 | {OV['near14_n']} 批 · {fc(OV['near14_cap'])} |")
A(f"| 高比例解禁（占流通盘 ≥30%） | {OV['hi_ratio_n']} 批 · {fc(OV['hi_ratio_cap'])}（占合计 {hi:.1f}%） |")
A(f"| 大额解禁（单批 ≥100 亿） | {sum(1 for i in data['items'] if i['cap_now_yi'] >= 100)} 批 |")
A("| 投资建议 | 🟡 观望（数据线索，非交易信号） |")
A("")
A("---")
A("")
A("## 一、未来 90 天按周解禁分布")
A("")
A("| 周区间 | 批次 | 解禁市值 | 涉及个股 |")
A("|--------|------|----------|----------|")
for w in W:
    mark = " 🔴高峰" if w["monday"] == pk["monday"] else (" ⚪最低" if w["monday"] == lo["monday"] else "")
    A(f"| {w['range']}{mark} | {w['n']} | {fc(w['cap'])} | {w['codes']} |")
A("")
A(f"> 高峰周 **{pk['range']}** 单周 {fc(pk['cap'])}；次高峰 **{pk2['range']}** {fc(pk2['cap'])}"
  f"（{pk2['n']} 批）；第三为 **{pk3['range']}** {fc(pk3['cap'])}（{pk3['n']} 批）。"
  f"这三周合计 {fc(pk['cap'] + pk2['cap'] + pk3['cap'])}，占窗口内全部解禁市值的 "
  f"{(pk['cap'] + pk2['cap'] + pk3['cap']) / OV['total_cap'] * 100:.1f}%。")
A("")
A("## 二、解禁类型市值占比")
A("")
A("| 解禁类型 | 批次 | 解禁市值 | 占比 |")
A("|----------|------|----------|------|")
for t in data["types"]:
    A(f"| {t['cat']} | {t['n']} | {fc(t['cap'])} | {t['cap']/OV['total_cap']*100:.1f}% |")
A("")
A("## 三、解禁市值 TOP20 重点预警名单")
A("")
A("| # | 代码 | 简称 | 解禁日 | 距今 | 解禁类型 | 解禁股数 | 估算解禁市值 | 占流通盘 | 占总股本 | 风险 |")
A("|---|------|------|--------|------|----------|----------|--------------|----------|----------|------|")
RK = {"both": "🚨 高比例+临近", "high": "🔴 高比例/大额", "near": "🟠 临近", "normal": "🟢 常态"}
for i, t in enumerate(data["top"][:20], 1):
    it = next(x for x in data["items"] if x["code"] == t["code"] and x["date"] == t["date"])
    A(f"| {i} | {t['code']} | {t['name']} | {t['date']} | {it['days']}天 | {t['cat']} | "
      f"{fs(it['shares_wan'])} | {fc(t['cap'])} | {t['ratio']:.1f}% | {it['total_ratio_pct']:.2f}% | {RK[t['risk']]} |")
A("")
A("## 四、代表个股详情（历史解禁 + 最近分红）")
A("")
for p in data["picks"]:
    A(f"### {p['name']}（{p['code']}）")
    A("")
    A(f"- 最新价 **{p['px']:.2f} 元**；PE(TTM) {p['pe_ttm']:.1f} / PB {p['pb']:.2f}；"
      f"流通市值 {fc(p['float_mcap_yi'])} / 总市值 {fc(p['mcap_yi'])}")
    A(f"- **本次解禁**：{p['date']}（距今 {p['days']} 天）· {fs(p['shares_wan'])} · "
      f"{fc(p['cap_yi'])} · 占流通盘 **{p['ratio']:.2f}%** · 占总股本 {p['total_ratio']:.2f}% · {p['type']}")
    A(f"- 近 12 个月已实施分红 **{p['div_count']}** 次，TTM 每股派息 {p['ttm_div']:.3f} 元，"
      f"对应股息率 **{p['ttm_yield']:.2f}%**" if p["ttm_yield"] else
      f"- 近 12 个月无已实施分红记录（上市未满完整会计年度或无派息）")
    A("")
    A("| 历史解禁日 | 解禁股数 | 解禁市值 | 占流通盘 | 类型 |")
    A("|---|---|---|---|---|")
    for h in p["hist"][:6]:
        A(f"| {h['date']} | {fs(h['shares_wan'])} | {fc(h['cap_yi'])} | {h['ratio']:.1f}% | {h['type']} |")
    A("")
    if p["divs"]:
        A("| 除权日 | 分配方案 | 报告期 | 进度 |")
        A("|---|---|---|---|")
        for d in p["divs"][:6]:
            A(f"| {d['date']} | {d['plan']} | {d['report']} | {d['progress']} |")
        A("")
A("---")
A("")
A("## ✅ 行动清单")
A("")
A("| # | 行动 | 触发条件 | 时间窗 |")
A("|---|------|---------|--------|")
A(f"| 1 | 建立「高比例 + 临近」双条件观察池（共 "
  f"{sum(1 for i in data['items'] if i['float_ratio_pct'] >= 30 and i['days'] <= 14)} 批），逐一核对是否已有减持计划公告 | 立即 | 本周内 |")
A(f"| 2 | 对 {pk['range']} 高峰周（{fc(pk['cap'])}）涉及的 {pk['codes']} 只个股提前排雷，确认限售方性质 | 解禁前 30 天 | {_d(pk['monday'], -30)} 起 |")
A(f"| 3 | 逐只在交易所公告中检索「减持计划」/「股份减持」关键词，以公告替代解禁表做判断 | 解禁前 15 天 | 滚动 |")
A(f"| 4 | 关注次高峰压力簇（{pk2['range']}，{fc(pk2['cap'])}）叠加财报披露期的双重扰动 | {_d(pk2['monday'])} 起 | 至 {_d(pk2['monday'], 6)} |")
A(f"| 5 | 对大额解禁（≥100 亿）标的核对限售方身份（国资 / 产业资本 / 财务投资人） | 立即 | 本周内 |")
A("")
A("## ⚠️ 风险提示 & 关键观察指标")
A("")
A("- **后续需要验证**：解禁后限售方的实际减持行为（大宗交易折价率、龙虎榜机构席位、股东户数变化）；"
  "以及是否出现「解禁前抢跑」的成交量放大。")
A("- **可能证伪信号**：若高比例解禁标的在解禁日前后无异常成交量放大、且无减持公告，"
  "说明限售方无减持意愿，本页的压力提示应视为中性。")
A(f"- **本页口径限制**：「估算解禁市值」按最新价推算（非解禁当日实际市值），市场波动会使其变化；"
  f"北交所 920201（百瑞吉）暂无参考价，市值计 0，仅计入批次与个股数。")
A("")
A("## 📚 数据来源 & 成员产出索引")
A("")
A(f"- 数据源：{M['src_lockup']}；{M['src_quote']}；{M['src_div']}")
A("- 采集方式：WorkBuddy「A股全栈数据」技能（a-stock-data v3.2.3）内嵌端点，东财请求统一串行限流（间隔 ≥1s + 抖动）")
A(f"- 原始快照：`data/lockup_raw.json`（{RAW_N} 条全量）、`data/quotes_raw.json`、`data/picks_detail.json`")
A(f"- 视觉交付：[`{FNAME}.html`]({FNAME}.html)")
A("- 页面交互：支持 **白天 / 黑夜双模式**（右上角按钮切换，选择会记住；主题在首屏前定下，无闪烁）")
A("")
A("---")
A("")
A("> ⚠️ 以上内容由 AI 基于公开信息整理生成，仅供参考，不构成任何投资建议或个股推荐。投资有风险，决策需谨慎。")
A("> 解禁不必然导致下跌。")
A("")

OUT = deliverable("lockup-radar-90d", "md", M["base"])
open(os.path.abspath(OUT), "w", encoding="utf-8").write("\n".join(L))
print("written:", os.path.abspath(OUT), len("\n".join(L)), "chars")
