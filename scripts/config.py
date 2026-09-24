# -*- coding: utf-8 -*-
"""基准日（base）与扫描窗口的【单一真源】。

优先级：命令行参数  >  data/_run_params.json  >  DEFAULT_BASE

所有脚本都必须从这里取日期，不要再硬编码任何 YYYY-MM-DD，
也不要再硬编码任何由日期派生出来的文字（如「12-07 ~ 12-18」）。
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))


def find_root(start=None):
    """自动定位项目根目录，兼容两种部署形态：

      A) 正常形态：脚本在 <root>/scripts/ 下
      B) 平铺形态：脚本直接躺在仓库根（GitHub 网页「Upload files」会丢目录层级）

    判据是「哪个候选目录里真的存在 data/ 或 requirements.txt」，
    而不是猜层级数 —— 否则平铺时会静默把 data/ 写到上一层去。
    """
    start = start or HERE
    for c in (start, os.path.abspath(os.path.join(start, ".."))):
        if os.path.isdir(os.path.join(c, "data")) or \
           os.path.isfile(os.path.join(c, "requirements.txt")):
            return c
    return os.path.abspath(os.path.join(start, ".."))


ROOT = find_root()
# 脚本所在目录：平铺时 == ROOT，正常时 == <root>/scripts
SCRIPTS = HERE if os.path.basename(HERE) != os.path.basename(ROOT) else ROOT
DATA = os.path.join(ROOT, "data")
PARAM = os.path.join(DATA, "_run_params.json")

# 首次构建时的基准日。之后每次运行由 _run_params.json 覆盖，
# 所以正常情况下你永远不需要改这一行。
DEFAULT_BASE = "2026-09-23"
WINDOW_DAYS = 90
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _cli_base():
    """从命令行里找第一个形如 YYYY-MM-DD 的参数。"""
    for a in sys.argv[1:]:
        if DATE_RE.match(a):
            return a
    return None


def _read_param():
    if not os.path.exists(PARAM):
        return None
    try:
        with open(PARAM, encoding="utf-8") as f:
            return json.load(f).get("base")
    except Exception:
        return None


def resolve(base=None, days=None):
    """返回 (base, end, days)。end = base + days 天，与「未来 90 天」口径一致。"""
    days = days or WINDOW_DAYS
    if base is None:
        base = _cli_base()
    if base is None:
        base = _read_param()
    base = base or DEFAULT_BASE
    dt = datetime.strptime(base, "%Y-%m-%d")
    return base, (dt + timedelta(days=days)).strftime("%Y-%m-%d"), days


def save(base, end):
    """把本次运行的基准日写入参数文件，供后续步骤读取。"""
    os.makedirs(DATA, exist_ok=True)
    with open(PARAM, "w", encoding="utf-8") as f:
        json.dump({"base": base, "end": end}, f, ensure_ascii=False, indent=1)
    return PARAM


def today():
    return datetime.now().strftime("%Y-%m-%d")


def generate():
    """页面/报告上标注的「生成时间」= 真实运行日期（不是基准日）。"""
    return today()


def slug(base=None):
    return resolve(base)[0]


def deliverable(stem, ext, base=None):
    """统一产出路径：deliverables/a-share/<stem>-<base>.<ext>"""
    return os.path.join(ROOT, "deliverables", "a-share",
                        "{}-{}.{}".format(stem, slug(base), ext))


def mmdd(datestr, delta=0):
    """'2026-12-14' (+delta 天) -> '12-14'。用于把派生日期写进文案。"""
    dt = datetime.strptime(str(datestr)[:10], "%Y-%m-%d") + timedelta(days=delta)
    return dt.strftime("%m-%d")


def load_dashboard():
    """读 dashboard.json（所有展示层共用的数据文件）。"""
    with open(os.path.join(DATA, "dashboard.json"), encoding="utf-8") as f:
        return json.load(f)
