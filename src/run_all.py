"""
一键运行：采集 → 派生/图 → 站点数据 → PPT → 打印 PDF。
日常更新只需要跑这个文件。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
STEPS = [
    ("采集 · 项目 A 固收", ["src/finance_fetch.py"]),
    ("采集 · 项目 B 英国", ["src/gtm_fetch.py"]),
    ("派生 / 校验 / 图表 / 看板 / 站点数据", ["src/build_all.py"]),
    ("PPTX（可编辑）", ["src/make_ppt.py"]),
    ("打印版 PDF", ["src/make_print.py"]),
]

if __name__ == "__main__":
    full = "--full" in sys.argv
    for name, cmd in STEPS:
        args = [PY, str(ROOT / cmd[0])]
        if full and cmd[0] in ("src/finance_fetch.py", "src/gtm_fetch.py"):
            args.append("--full")
        print(f"\n=== {name} ===", flush=True)
        r = subprocess.run(args, cwd=ROOT)
        if r.returncode != 0:
            print(f"!!! {name} 失败（退出码 {r.returncode}）——后续步骤仍然继续，"
                  f"已发布内容不会被覆盖。", flush=True)
    print("\n=== 完成。检查 checks/validation.json 与 data/run.log ===")
