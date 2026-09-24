# -*- coding: utf-8 -*-
"""★ 一条命令跑完全流程（手工刷新用这个）

用法（在项目根目录 D:\\解禁预警 下）：
    python scripts/run_all.py                   基准日 = 今天，窗口 = 今天 + 90 天
    python scripts/run_all.py 2026-12-23        指定基准日
    python scripts/run_all.py --no-package      跳过 deploy/ 打包

流程：自动备份 → 抓取解禁 → 抓取行情 → 组装数据 → 渲染 HTML → 生成报告 → 打包 deploy/
任一环节失败立即中止，并提示用哪个备份目录回滚。
"""
import json
import os
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_root(start):
    """自动定位项目根目录。

    兼容两种部署形态：
      A) scripts/ 子目录（本地正常形态）：本文件在 <root>/scripts/run_all.py
      B) 全部平铺在仓库根（GitHub 网页上传丢目录时）：本文件在 <root>/run_all.py

    判据是「哪个方向的 data/ 或 README.md 存在」而不是猜层数，
    这样无论脚本被放到哪里都不会写错路径。
    """
    cands = [start, os.path.abspath(os.path.join(start, ".."))]
    for c in cands:
        if os.path.isdir(os.path.join(c, "data")) or \
           os.path.isfile(os.path.join(c, "requirements.txt")):
            return c
    return os.path.abspath(os.path.join(start, ".."))


ROOT = _find_root(HERE)
SCRIPTS = HERE if os.path.basename(HERE) != os.path.basename(ROOT) else ROOT
sys.path.insert(0, HERE)
from config import resolve, save, today, DATA, DATE_RE   # noqa: E402

PY = sys.executable
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")

STEPS = [
    ("fetch_lockup.py", "抓取全市场未来 90 天解禁排期"),
    ("fetch_quotes.py", "抓取行情快照 + 代表股历史解禁/分红"),
    ("build_data.py", "组装看板数据 dashboard.json"),
    ("render_html.py", "渲染单文件 HTML 雷达"),
    ("make_report.py", "生成配套 Markdown 报告"),
]


def backup(base):
    """把现有产物快照到 backup/<基准日>/，抓取失败时可整体回滚。"""
    snap = os.path.join(ROOT, "backup", base)
    if os.path.exists(snap):
        return snap, False
    os.makedirs(snap, exist_ok=True)
    for rel in ("解禁预警雷达.html", "data", "deliverables"):
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            continue
        dst = os.path.join(snap, rel)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    return snap, True


def run(script, label, i, total):
    print("\n--- [{}/{}] {} ---".format(i, total, label))
    # 优先用同级目录（平铺形态），退回 scripts/ 子目录（正常形态）
    path = os.path.join(SCRIPTS, script)
    if not os.path.exists(path):
        path = os.path.join(HERE, "scripts", script)
    r = subprocess.run([PY, path], cwd=ROOT, env=ENV)
    return r.returncode


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    do_pkg = "--no-package" not in sys.argv

    raw = args[0] if args else today()
    if not DATE_RE.match(raw):
        print("基准日格式不对：{}（应为 YYYY-MM-DD）".format(raw))
        return 2
    base, end, days = resolve(raw)

    print("=" * 68)
    print("解禁预警雷达 · 全流程  |  基准日 {}  窗口 {} ~ {}（{} 天）".format(
        base, base, end, days))
    print("=" * 68)

    snap, made = backup(base)
    rel = os.path.relpath(snap, ROOT)
    print("[备份] {} → {}".format("现有产物已快照" if made else "已存在，未重复备份", rel))

    save(base, end)

    total = len(STEPS) + (1 if do_pkg else 0)
    for i, (script, label) in enumerate(STEPS, 1):
        if run(script, label, i, total) != 0:
            print("\n!! {} 失败。备份在 {}，可拷回项目根目录回滚。".format(script, rel))
            return 1

    if do_pkg and run("package_deploy.py", "打包成可上传 GitHub 的 deploy/",
                      len(STEPS) + 1, total) != 0:
        return 1

    # ---------- 收尾自检 ----------
    with open(os.path.join(DATA, "dashboard.json"), encoding="utf-8") as f:
        d = json.load(f)
    M, OV = d["meta"], d["overview"]

    print("\n" + "=" * 68)
    outputs = [os.path.join(ROOT, "解禁预警雷达.html"),
               os.path.join(ROOT, "deliverables", "a-share",
                            "lockup-radar-90d-{}.html".format(base)),
               os.path.join(ROOT, "deliverables", "a-share",
                            "lockup-radar-90d-{}.md".format(base))]
    if do_pkg:
        outputs.append(os.path.join(ROOT, "deploy", "index.html"))
    for p in outputs:
        print("{:<4}{}".format("OK" if os.path.exists(p) else "缺失",
                               os.path.relpath(p, ROOT)))

    ok_base = M["base"] == base and M["window_end"] == end
    print("-" * 68)
    print("基准日自检：{}  (meta.base={} / meta.window_end={})".format(
        "一致" if ok_base else "不一致 !!", M["base"], M["window_end"]))
    print("本次数据：{} 批 · {} 只个股 · 合计 ¥{:,.2f} 亿 · 高峰周 {}".format(
        OV["batches"], OV["codes"], OV["total_cap"], OV["peak_week"]))
    print("=" * 68)
    print("完成。下一步：把 deploy/ 里的 3 个文件覆盖上传到 GitHub 仓库根目录。")
    return 0 if ok_base else 1


if __name__ == "__main__":
    sys.exit(main())
