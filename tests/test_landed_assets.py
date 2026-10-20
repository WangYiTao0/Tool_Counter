"""落地副本对账：copy_assets 落进 pages/ 的每一份都得挡在 git 外、挡在产物外。

期望值取 ``msui.resources.ASSET_NAMES``（msui 自己说它落哪几份），不在这里
写死——0.10.0 起多了 tokens-light.css，写死两份的测试会继续绿，而副本已经
以未跟踪文件出现、一次整目录 add 就进了仓。升级 msui 时这里红了，就去补
pages/.gitignore 与 Tool_Counter.spec，别把期望改回写死的清单。
"""
from __future__ import annotations

import re
from pathlib import Path

from msui.resources import ASSET_NAMES

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pages_gitignore_lists_every_landed_asset():
    ignored = {
        line.strip()
        for line in (REPO_ROOT / "pages" / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    missing = set(ASSET_NAMES) - ignored
    assert not missing, f"pages/.gitignore 缺：{sorted(missing)}"


def test_spec_filters_every_landed_asset_out_of_the_bundle():
    spec = (REPO_ROOT / "Tool_Counter.spec").read_text(encoding="utf-8")
    m = re.search(r"parts\[-1\] in \(([^)]*)\)", spec)
    assert m, "Tool_Counter.spec 里找不到 _is_landed_css 的文件名元组"
    filtered = set(re.findall(r'"([^"]+)"', m.group(1)))
    missing = set(ASSET_NAMES) - filtered
    assert not missing, f"Tool_Counter.spec 的副本过滤缺：{sorted(missing)}"
