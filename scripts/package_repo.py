# -*- coding: utf-8 -*-
"""打包「可上传到 GitHub 的完整仓库内容」，供 Actions 自动更新使用。

为什么要打这个包：
  GitHub Actions 要在仓库里跑 scripts/run_all.py，所以仓库必须包含
  scripts/ 与 .github/；只有 index.html 的话工作流跑不起来。

产出：deploy_repo/
    index.html            当前看板（Pages 首页）
    README.md             仓库说明（含报告）
    .nojekyll             可选
    scripts/*.py          流水线脚本（Actions 需要）
    .github/workflows/    工作流定义
    requirements.txt      Actions 安装依赖用

不打包：data/、backup/、deliverables/、deploy/（都是产物，Actions 会自己生成）
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "deploy_repo")

# 需要脚本但不需要的辅助文件（一次性诊断工具，不必上传）
SKIP_SCRIPTS = {
    "_sim_actions.py", "_audit_wf.py", "_test_offline.py", "_test_gitcommit.py",
    "_t_bat.py", "_patch_lib.py", "_p1_css_tokens.py", "_p2_css_vars.py",
    "_p3_svg_class.py", "_p4_html_js.py", "_p5_verify.py", "_p6_fix_probe.py",
    "_p7_readme_head.py", "_v.log", "_test_dual_layout.py",
    "shots.mjs", "shots_light.mjs", "verify.mjs", "diag320.mjs",   # 本地测试用，Actions 不跑
    "analyze.py", "probe_lockup.py",                                # 早期探测脚本，不参与流水线
}
SKIP_DIRS = {"__pycache__"}

if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

written = []


def put(src, rel, ignore=None):
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(src):
        shutil.copytree(src, dst, ignore=ignore)
    else:
        shutil.copy2(src, dst)
    written.append((rel, os.path.getsize(dst) if os.path.isfile(dst) else -1))


# 1) 页面与说明（来自 deploy/，即已构建好的版本）
for n in ("index.html", "README.md"):
    p = os.path.join(ROOT, "deploy", n)
    if os.path.exists(p):
        put(p, n)
    else:
        print("!! 缺少 deploy/%s，请先跑 scripts/run_all.py" % n)
put(os.path.join(ROOT, "deploy", ".nojekyll"), ".nojekyll")

# 2) 流水线脚本（Actions 要用）
def keep(name):
    return name not in SKIP_SCRIPTS and not name.endswith(".pyc")


put(os.path.join(ROOT, "scripts"), "scripts",
    ignore=shutil.ignore_patterns(*SKIP_SCRIPTS, *SKIP_DIRS, "*.pyc"))

# 3) 工作流
put(os.path.join(ROOT, ".github"), ".github",
    ignore=shutil.ignore_patterns(*SKIP_DIRS))

# 4) 依赖清单（便于 Actions 与本地一致）
req = os.path.join(ROOT, "requirements.txt")
with open(req, "w", encoding="utf-8") as f:
    f.write("requests>=2.31\n")
put(req, "requirements.txt")

# 5) 空目录占位：让 Actions 跑完后结构完整（git 不跟踪空目录，用 .gitkeep）
for d in ("data", "backup"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
    with open(os.path.join(OUT, d, ".gitkeep"), "w") as f:
        f.write("")
    written.append((d + "/.gitkeep", 0))

# 6) 操作指引（纯文本，双击就能看，避免网页上传再踩「不能拖文件夹」的坑）
#    模板存放在 docs/，不随 deploy_repo/ 被清空。
guide_src = os.path.join(ROOT, "docs", "上传操作指引.txt")
if os.path.exists(guide_src):
    put(guide_src, "上传操作指引.txt")

print("=" * 66)
print("打包完成：", os.path.relpath(OUT, ROOT))
print("=" * 66)
total = 0
for rel, size in sorted(written):
    if size >= 0:
        total += size
        print("   %-46s %8s B" % (rel, "{:,}".format(size) if size else "-"))
    else:
        print("   %-46s %8s" % (rel + "/", "(dir)"))

n = sum(len(fs) for _, _, fs in os.walk(OUT))
print("-" * 66)
print("文件数: %d   总字节: %s" % (n, "{:,}".format(total)))
print("""
上传方法（GitHub 网页）：
  ★ 先读同目录下的「上传操作指引.txt」，一步步照做即可。
  ★ 核心：GitHub 网页「Upload files」【不能拖文件夹】，会丢目录层级。
     要在网页上建目录，必须用「Add file -> Create new file」，
     并在文件名框里直接敲斜杠，例如：
         .github/workflows/refresh-lockup-radar.yml
     斜杠会自动变成目录层级。这是 GitHub 官方支持的方式。
  页面本身不受影响：没有 .github/ 也能看，只是 Actions 跑不起来。
""")
