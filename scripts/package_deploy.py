# -*- coding: utf-8 -*-
"""把看板打包成可直接上传 GitHub Pages 的 deploy/ 文件夹。

产出：
    deploy/index.html    看板本体（改名，Pages 默认首页）
    deploy/README.md      仓库说明 + 完整文字报告
    deploy/.nojekyll      跳过 Jekyll，纯静态直出
"""
import json
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from config import deliverable, load_dashboard   # noqa: E402

DEPLOY = os.path.join(ROOT, "deploy")


def fc(yi):
    if yi >= 10000:
        return "¥{:,.2f}万亿".format(yi / 10000)
    if yi >= 1:
        return "¥{:,.2f}亿".format(yi)
    return "¥{:,.0f}万".format(yi * 10000)


d = load_dashboard()
M, OV = d["meta"], d["overview"]
base = M["base"]

src_html = os.path.join(ROOT, "解禁预警雷达.html")
src_md = deliverable("lockup-radar-90d", "md", base)
for p in (src_html, src_md):
    if not os.path.exists(p):
        print("!! 缺少输入文件：{}".format(p))
        sys.exit(1)

os.makedirs(DEPLOY, exist_ok=True)
shutil.copy2(src_html, os.path.join(DEPLOY, "index.html"))
open(os.path.join(DEPLOY, ".nojekyll"), "w").close()

with open(src_md, encoding="utf-8") as f:
    report = f.read()

head = """# A股「未来 90 天限售解禁预警雷达」

> **在线看板**：打开本仓库的 Pages 网址（首页即 `index.html`）
> **数据基准日**：{base}　|　**扫描窗口**：{base} ~ {window_end}　|　**生成时间**：{generated}
> **本次覆盖**：{batches} 批解禁 · {codes} 只个股 · 合计 {cap}

## 这是什么

一个**单文件** HTML 看板，把 A 股（沪深京）全市场未来 90 天的限售股解禁排期做成可视化雷达：
按周解禁市值分布、解禁类型占比、解禁市值 TOP 榜、可排序/可搜索/可筛选的 {batches} 行明细，
以及代表性个股的历史解禁记录与最近分红。

**关键特性**：CSS / JS / 图表 / 数据**全部内联**，因此断网也能双击打开、
手机与电脑看到的完全一致，且不会因为数据接口故障变成白屏。

代价也很明确：**页面是数据快照，不是实时数据**。刷新网页不会重新抓取，
数字永远停在上面的「数据基准日」。要更新请看下面的「如何刷新数据」。

## 目录结构

| 文件 | 说明 |
|---|---|
| `index.html` | 看板本体（GitHub Pages 首页），资源全内联，可直接双击打开 |
| `README.md` | 本说明 + 完整文字报告 |
| `.nojekyll` | 可选（以点开头，资源管理器默认隐藏）。让 GitHub Pages 跳过 Jekyll 处理；漏传不影响构建，因为本仓库没有以下划线开头的文件 |

页面右上角有 **白天 / 黑夜切换按钮**：默认黑夜（暗色风控预警风），点一下切白天，选择会记在浏览器里、
下次打开保持。两种模式的文字对比度与图表配色都经过 headless 浏览器实测校验，切换后无不可读内容。

> 文字报告中提到的 `data/*.json`、`scripts/*.py` 是**本地产线文件**，未随本页上传。

## 如何刷新数据（在本地项目目录 `D:\\解禁预警` 执行）

**最简单：双击项目根目录的 `刷新数据.bat`。** 它会自动找到可用的 Python、补装缺失的依赖、
跑完整条流水线，最后把新生成的本机页面打开；跑完后照屏幕提示上传即可。

> 想先确认环境没问题（不联网、不改任何文件）：在项目目录开一个终端，跑
> `刷新数据.bat check`。
> 想指定基准日：把日期当参数传进去，如 `刷新数据.bat 2026-12-23`。

**或者用命令行**（与双击完全等价，任选其一）：

```
python scripts/run_all.py
```

它会自动：备份现有产物 → 抓取最新的全市场解禁排期与行情 → 重建单文件看板 → 重新打包本文件夹。
然后把 `deploy/` 里的 `index.html` 与 `README.md` **覆盖上传**到 GitHub 仓库根目录，网址即刷新为最新数据。

指定基准日（例如补做某一天）：

```
python scripts/run_all.py 2026-12-23
```

## 如何开启 GitHub Pages

仓库 → **Settings** → **Pages** → Source 选 `Deploy from a branch` → 分支选 `main`、目录选 `/ (root)` → Save。
稍等约 1 分钟，网址形如 `https://<用户名>.github.io/<仓库名>/`。

> 提示：GitHub 免费账号只能为**公开仓库**启用 Pages。

---

""".format(base=base, window_end=M["window_end"], generated=M["generated"],
           batches=OV["batches"], codes=OV["codes"], cap=fc(OV["total_cap"]))

with open(os.path.join(DEPLOY, "README.md"), "w", encoding="utf-8") as f:
    f.write(head + report)

for n in ("index.html", "README.md", ".nojekyll"):
    p = os.path.join(DEPLOY, n)
    print("written: {}  {:,} bytes".format(os.path.relpath(p, ROOT), os.path.getsize(p)))
