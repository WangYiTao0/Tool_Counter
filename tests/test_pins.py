"""钉版本对账：msui 的版本在本仓写了三处，升级时必须一起改。

requirements.txt 的 wheel URL 里出现两次（路径段 ``v X.Y.Z`` + 文件名
``msui-X.Y.Z-``），counter.py 里还有冒烟用的 ``MSUI_PINNED``。只改了其中
一处的话，CI 装的是一版、冒烟期望的是另一版，或者 URL 自相矛盾直接 404。
这里比的是三处字面值彼此一致，不读安装元数据（那只会回显装了哪版、永远绿）。
"""
from __future__ import annotations

import re
from pathlib import Path

from counter import MSUI_PINNED

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_requirements_and_smoke_pin_the_same_msui():
    line = next(
        raw for raw in (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if raw.startswith("msui")
    )
    m = re.search(r"/download/v([\d.]+)/msui-([\d.]+)-py3-none-any\.whl$", line)
    assert m, f"requirements.txt 的 msui 行不是钉版本 wheel URL：{line!r}"
    assert m.group(1) == m.group(2) == MSUI_PINNED, (
        f"路径段 v{m.group(1)} / 文件名 {m.group(2)} / MSUI_PINNED {MSUI_PINNED} 三处不一致"
    )
