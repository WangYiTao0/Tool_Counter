"""业务闸门：计数状态住在 Python 侧，页面只经 js_api 桥读它。

这三条钉住的是范式而不是数字本身：
- 初始状态 0、增量来自 CLICK_INCREMENT 常量（按钮文字由页面从 increment
  推导，发新版只改常量的惯例保持）；
- 应答是 msui.bridge.Serializer 的信封 {"busy": False, "data": ...}——
  页面拿到 busy=True 时就地丢弃，不排队；
- 点一次涨一个 CLICK_INCREMENT，状态在 CounterApi 实例里，页面无状态；
- 启动报上的单实例 id 就是 miniprog.toml 的 id（连点图标只开一扇窗）。
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import counter
from counter import CLICK_INCREMENT, CounterApi, __version__

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_initial_state_lives_in_python():
    api = CounterApi()
    assert api.get_state() == {
        "busy": False,
        "data": {"count": 0, "increment": CLICK_INCREMENT},
    }


def test_click_adds_increment_python_side():
    api = CounterApi()
    api.click()
    reply = api.click()
    assert reply["busy"] is False
    assert reply["data"]["count"] == 2 * CLICK_INCREMENT
    # 状态确实在 Python 侧：新查询读到的是同一份计数，不靠页面回传
    assert api.get_state()["data"]["count"] == 2 * CLICK_INCREMENT


def test_version_bumped():
    assert __version__ == "1.5.0"


def test_startup_reports_the_id_from_miniprog_toml(monkeypatch):
    """启动报上的单实例 id **就是 miniprog.toml 那个 id**，一字不差。

    断言的不是「传了个非空值」：守卫按 id 建全局唯一的锁，随手另起一个名字
    照样能跑、什么都不报错，但两个仓一旦撞名就会互相顶掉窗口——点 B 弹出 A，
    而这只有用户看得见。所以这里比的是两份来源的字面值，写死一处就红。

    只跑到 `run()` 门口就截住：`copy_assets` 与 `run` 都换成探针，测试绝不
    落文件、绝不开窗。
    """
    meta = tomllib.loads((REPO_ROOT / "miniprog.toml").read_text(encoding="utf-8"))
    seen: dict = {}
    monkeypatch.setattr(counter, "copy_assets", lambda page_dir: page_dir)
    monkeypatch.setattr(counter, "run", lambda url, **kwargs: seen.update(kwargs))

    counter.main()

    assert seen["single_instance"] == meta["id"]
