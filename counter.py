"""Counter —— MSToolbox 接入契约 + msui 界面契约的官方样板应用。

本仓是两份契约的活样例，各自只指一处、不复述：

- **接入契约**（miniprog.toml / build.py / publish.yml）：MSToolbox 仓
  docs/接入契约.md；
- **界面契约**（pages/ + msui 三步启动 + js_api 桥）：msui 仓 README，
  https://github.com/WangYiTao0/msui 。

界面按 msui 契约走：页面（pages/index.html）归本仓、只管展示，版式全靠
msui 的骨架约定（body 即容器、主读数挂 .display）；共享样式
tokens.css / base.css 由 ``copy_assets`` 每次启动落进页面目录（不入仓）；
业务留在 Python——计数状态与 CLICK_INCREMENT 都在 :class:`CounterApi`
里，页面经 pywebview 的 js_api 桥来调，应答统一走
:class:`msui.bridge.Serializer` 的忙碌信封。

启动带 ``single_instance="counter"``（值就是 miniprog.toml 的 id）：连点
图标只开一扇窗，第二个进程把已开的那扇带到前台后自己静默退出。这不是本仓
的装饰而是接入契约 §2.1 的硬要求，msui 起 0.7.0 这个参数必填。

发新版时只改下面两个常量附近：`__version__`（窗口标题读它）与
`CLICK_INCREMENT`（每次点击的增量，按钮文字「+N」由页面从状态推导）。

环境变量 APP_SMOKE=1 时隐藏开窗、:class:`msui.testing.SmokeDriver`
自动驾驶一轮（桥往返、点击 +N、样式与版式生效、版本横幅）后自关——
给无人值守冒烟用，全程不上屏。失败收集、finally 销毁窗口、watchdog
超时兜底都由 SmokeDriver 骨架代办。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from msui.bridge import Serializer
from msui.resources import copy_assets
from msui.shell import run
from msui.testing import SmokeDriver

__version__ = "1.5.0"

# 每次点击按钮时数字增加的量。样板仓靠只改这一个数字演示版本更新，
# 行为差异一眼可辨。页面按钮文字「+N」从这里推导（经 get_state 下发），
# 发新版真的只改常量，页面不用跟着改。
CLICK_INCREMENT = 3

# 本仓钉死的 msui 版本，与 requirements.txt 的 wheel URL 一致；升级 msui
# 时两处一起改。冒烟据此断言横幅——证明冻结产物带的确实是钉的这一版，
# 而不只是「随便哪一版落了地」。
MSUI_PINNED = "0.7.0"


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


def make_smoke_script(api: CounterApi, serve_dir: Path):
    """造冒烟脚本（照 msui README §2 的 APP_SMOKE 分支，跑在 pywebview 后台线程）。

    断言六件事：桥通（按钮文字来自 Python 的增量）、点击 +N 显示正确且
    计数确在 Python 侧、样式吃进去（check_token_style：主按钮背景 ==
    --brand）、版式地基生效（body 24px 内边距、.display 居中 48px、+N 按钮
    在操作行里真的居中）、落地 css 横幅钉的就是 MSUI_PINNED、窗口标题带本仓
    版本号。
    失败收集、finally 销毁窗口、watchdog 超时兜底都由 SmokeDriver 代办。
    """

    def smoke_script(drive: SmokeDriver, window) -> None:
        # 1. 桥通：初始渲染后按钮文字 = "+<CLICK_INCREMENT>"（值从 Python 下发）
        got = drive.wait_js(
            window,
            "document.getElementById('add').textContent",
            f"+{CLICK_INCREMENT}",
        )
        drive.check(got == f"+{CLICK_INCREMENT}", f"按钮文字未从 Python 增量推导：{got!r}")

        # 2. 点一次（真实 DOM 事件 → js_api 桥 → Python 计数 → 页面重绘）
        window.evaluate_js("document.getElementById('add').click()")
        shown = drive.wait_js(
            window,
            "document.getElementById('count').textContent",
            str(CLICK_INCREMENT),
        )
        drive.check(
            shown == str(CLICK_INCREMENT),
            f"点击一次后页面显示 {shown!r}，期望 {str(CLICK_INCREMENT)!r}",
        )
        python_count = api.get_state()["data"]["count"]
        drive.check(
            python_count == CLICK_INCREMENT,
            f"Python 侧计数为 {python_count}，期望 {CLICK_INCREMENT}",
        )

        # 3. 样式吃进去了：主按钮实测背景色 == --brand token 解出的 rgb
        drive.check_token_style(window, "button.primary", "backgroundColor", "brand")

        # 4. 版式地基生效：内容不贴窗框（body 非零内边距）、大读数居中吃 48px 档
        pad = drive.wait_js(window, "getComputedStyle(document.body).paddingLeft", "24px")
        drive.check(pad == "24px", f"body 左内边距该是 24px（--space-5），实测 {pad!r}")
        readout = drive.wait_js(
            window,
            "(() => { const d = getComputedStyle(document.querySelector('.display'));"
            " return d.textAlign + ' ' + d.fontSize; })()",
            "center 48px",
        )
        drive.check(readout == "center 48px", f".display 该居中吃 48px 档，实测 {readout!r}")
        # 按钮真的居中了。断言的是**用户能看见的那条不变量**——按钮的水平中心
        # 与它所在操作行的水平中心重合——而不是 justify-content 的字面值：后者
        # 只证明「CSS 里写了这句」，前者才证明「渲染出来真是居中的」。左对齐时
        # 两个中心差着大半个行宽，这条当场红。1px 容差留给亚像素取整。
        centered = drive.wait_js(
            window,
            "(() => { const row = document.querySelector('.actions');"
            " const btn = document.getElementById('add');"
            " if (!row || !btn) return 'missing';"
            " const r = row.getBoundingClientRect(), b = btn.getBoundingClientRect();"
            " const off = (b.left + b.width / 2) - (r.left + r.width / 2);"
            " return Math.abs(off) <= 1 ? 'centered' : 'off:' + off.toFixed(1); })()",
            "centered",
        )
        drive.check(centered == "centered", f"+N 按钮该在操作行里居中，实测 {centered!r}")

        # 5. 落地样式的版本横幅钉住本仓吃的 msui 版本（横幅只证明 css 落地，
        #    「页面吃进去了」由上面 check_token_style 证明，两条各管一半）
        banner = (serve_dir / "tokens.css").read_text(encoding="utf-8").splitlines()[0]
        drive.check(
            banner == f"/* msui {MSUI_PINNED} */",
            f"tokens.css 横幅该是 '/* msui {MSUI_PINNED} */'，实测 {banner!r}",
        )

        # 6. 窗口标题跟随 __version__
        drive.check(
            f"v{__version__}" in window.title,
            f"窗口标题该含 v{__version__}，实测 {window.title!r}",
        )
        print(
            f"冒烟：title={window.title!r} 显示={shown!r} 横幅={banner!r}"
            f" padding={pad!r} display={readout!r}",
            flush=True,
        )

    return smoke_script


def main() -> None:
    serve_dir = copy_assets(page_dir())  # 每次启动覆盖落样式，页面永远跟着装的这版 msui 走
    api = CounterApi()
    driver = (
        SmokeDriver(make_smoke_script(api, serve_dir))
        if os.environ.get("APP_SMOKE") == "1"
        else None
    )
    run(
        serve_dir / "index.html",
        js_api=api,
        title=f"Counter v{__version__}",
        # 连点图标只开一扇窗（msui 起 0.7.0 必填）。值就是 miniprog.toml 的 id，
        # 别另起名字——守卫按它建全局唯一的锁，撞名的两个小程序会互相顶掉窗口。
        single_instance="counter",
        hidden=driver is not None,
        on_ready=driver,
    )
    if driver is not None:
        driver.exit()  # 有失败：逐条打印后退出码 1；全绿：打印「冒烟通过」


if __name__ == "__main__":
    main()
