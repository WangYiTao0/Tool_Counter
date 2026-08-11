"""业务闸门：计数状态住在 Python 侧，页面只经 js_api 桥读它。

这三条钉住的是范式而不是数字本身：
- 初始状态 0、增量来自 CLICK_INCREMENT 常量（按钮文字由页面从 increment
  推导，发新版只改常量的惯例保持）；
- 应答是 msui.bridge.Serializer 的信封 {"busy": False, "data": ...}——
  页面拿到 busy=True 时就地丢弃，不排队；
- 点一次涨一个 CLICK_INCREMENT，状态在 CounterApi 实例里，页面无状态。
"""
from __future__ import annotations

from counter import CLICK_INCREMENT, CounterApi, __version__


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
    assert __version__ == "1.4.0"
