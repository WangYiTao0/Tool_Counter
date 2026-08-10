"""Counter —— MSToolbox 接入契约 + msui 界面契约的官方样板应用。

本仓是两份契约的活样例，各自只指一处、不复述：

- **接入契约**（miniprog.toml / build.py / publish.yml）：MSToolbox 仓
  docs/接入契约.md；
- **界面契约**（pages/ + msui 三步启动 + js_api 桥）：msui 仓 README，
  https://github.com/WangYiTao0/msui 。

界面按 msui 契约走：页面（pages/index.html）归本仓、只管展示；共享样式
tokens.css / base.css 由 ``copy_assets`` 每次启动落进页面目录（不入仓）；
业务留在 Python——计数状态与 CLICK_INCREMENT 都在 :class:`CounterApi`
里，页面经 pywebview 的 js_api 桥来调，应答统一走
:class:`msui.bridge.Serializer` 的忙碌信封。

发新版时只改下面两个常量附近：`__version__`（窗口标题读它）与
`CLICK_INCREMENT`（每次点击的增量，按钮文字「+N」由页面从状态推导）。

环境变量 APP_SMOKE=1 时隐藏开窗、自动驾驶一轮（点一次按钮、核对显示与
样式、核对落地样式的版本横幅）后自关——给无人值守冒烟用，全程不上屏。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from msui.bridge import Serializer
from msui.resources import copy_assets
from msui.shell import run

__version__ = "1.3.0"

# 每次点击按钮时数字增加的量。样板仓靠只改这一个数字演示版本更新，
# 行为差异一眼可辨。页面按钮文字「+N」从这里推导（经 get_state 下发），
# 发新版真的只改常量，页面不用跟着改。
CLICK_INCREMENT = 3


class CounterApi:
    """js_api 桥对象：计数状态住在这里（Python 侧），页面无状态。

    pywebview 对每次前端调用各开一个后台线程（官方文档明说 not
    thread-safe），所以两个入口都包在同一把 :class:`Serializer` 里：
    抢不到锁立即回 ``{"busy": True, ...}``，绝不排队——连点丢弃，
    不会攒成一队 +N。
    """

    def __init__(self) -> None:
        self._count = 0
        self._serial = Serializer()

    def _state(self) -> dict:
        return {"count": self._count, "increment": CLICK_INCREMENT}

    def get_state(self) -> dict:
        """页面加载后取初始状态（计数 + 增量，按钮文字由页面从增量推导）。"""
        return self._serial.run(self._state)

    def click(self) -> dict:
        """点一次按钮：Python 侧计数 += CLICK_INCREMENT，返回新状态。"""

        def _do() -> dict:
            self._count += CLICK_INCREMENT
            return self._state()

        return self._serial.run(_do)


def page_dir() -> Path:
    """页面目录：冻结态在 _MEIPASS/pages（spec 收进去的），源码态在本文件旁。"""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "pages"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent / "pages"


def _wait_js(window, script: str, expected: str, deadline: float) -> str:
    """轮询 evaluate_js 直到结果等于 expected 或超时；返回最后一次结果。"""
    result = ""
    while time.monotonic() < deadline:
        result = window.evaluate_js(script)
        if result == expected:
            return result
        time.sleep(0.2)
    return result


def _smoke(api: CounterApi, serve_dir: Path, failures: list[str]):
    """冒烟自动驾驶（on_ready 钩子，跑在 pywebview 后台线程）。

    断言四件事：桥通（按钮文字来自 Python 的增量）、点击 +N 显示正确且
    计数确在 Python 侧、样式生效（主按钮 computedStyle 背景 == --brand
    token 解出的色）、落地 css 首行带 msui 版本横幅。失败塞 failures，
    主线程等 run() 返回后据此定退出码。
    """

    def _run(window) -> None:
        deadline = time.monotonic() + 15
        try:
            # 1. 桥通：初始渲染后按钮文字 = "+<CLICK_INCREMENT>"（值从 Python 下发）
            got = _wait_js(
                window,
                "document.getElementById('add').textContent",
                f"+{CLICK_INCREMENT}",
                deadline,
            )
            if got != f"+{CLICK_INCREMENT}":
                failures.append(f"按钮文字未从 Python 增量推导：{got!r}")

            # 2. 点一次（真实 DOM 事件 → js_api 桥 → Python 计数 → 页面重绘）
            window.evaluate_js("document.getElementById('add').click()")
            shown = _wait_js(
                window,
                "document.getElementById('count').textContent",
                str(CLICK_INCREMENT),
                deadline,
            )
            if shown != str(CLICK_INCREMENT):
                failures.append(
                    f"点击一次后页面显示 {shown!r}，期望 {str(CLICK_INCREMENT)!r}"
                )
            python_count = api.get_state()["data"]["count"]
            if python_count != CLICK_INCREMENT:
                failures.append(f"Python 侧计数为 {python_count}，期望 {CLICK_INCREMENT}")

            # 3. 样式生效：主按钮实测背景色 == tokens 里 --brand 解出的色
            style = window.evaluate_js(
                """
                (() => {
                  const el = document.getElementById('add');
                  const brand = getComputedStyle(document.documentElement)
                    .getPropertyValue('--brand').trim();
                  const probe = document.createElement('div');
                  probe.style.color = brand || 'transparent';
                  document.body.appendChild(probe);
                  const expected = getComputedStyle(probe).color;
                  probe.remove();
                  return getComputedStyle(el).backgroundColor + '|' + expected;
                })()
                """
            )
            actual, _, expected = (style or "|").partition("|")
            if not expected or actual != expected:
                failures.append(f"主按钮背景 {actual!r} != --brand 解出的 {expected!r}")

            # 4. 落地样式的版本横幅：首行 /* msui X.Y.Z */
            banner = (serve_dir / "tokens.css").read_text(encoding="utf-8").splitlines()[0]
            if not banner.startswith("/* msui "):
                failures.append(f"tokens.css 首行不是 msui 版本横幅：{banner!r}")
            print(f"冒烟：title={window.title!r} 显示={shown!r} 横幅={banner!r}", flush=True)
        except Exception as exc:  # 冒烟自身炸了也要算失败并关窗
            failures.append(f"冒烟异常：{exc!r}")
        finally:
            window.destroy()

    return _run


def main() -> None:
    serve_dir = copy_assets(page_dir())  # 每次启动覆盖落样式，页面永远跟着装的这版 msui 走
    api = CounterApi()
    smoke = os.environ.get("APP_SMOKE") == "1"
    failures: list[str] = []
    run(
        serve_dir / "index.html",
        js_api=api,
        title=f"Counter v{__version__}",
        hidden=smoke,
        on_ready=_smoke(api, serve_dir, failures) if smoke else None,
    )
    if smoke:
        if failures:
            for line in failures:
                print(f"冒烟失败：{line}", flush=True)
            sys.exit(1)
        print("冒烟通过", flush=True)


if __name__ == "__main__":
    main()
