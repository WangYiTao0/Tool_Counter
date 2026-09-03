"""无头义务闸门（接入契约 §2.4）：收到无头信号时不弹窗、UTF-8 stdio、退出码报告结果。

本仓是样板，抄它的人会照着写自己工具的无头分支，所以这几条钉的是**义务本身**
而不是 Counter 的业务：

- 无头信号在 → 一次都不碰 ``msui.shell.run``（那会开窗、还会走单实例守卫，
  守卫抢不到锁时会把已有窗口带到前台再返回 0，等于没人看的时候弹窗、还谎报
  成功，见 MSLaunchpad#214）；
- 信号不在 → 照旧开窗，一个字都不变（别为了新分支把手动那条路弄坏了）；
- 冒烟（APP_SMOKE）与无头是**两条**路：冒烟跑的是测试脚本不是业务，两个条件
  合并的实现会让定时路径去跑冒烟，测试里用「同时设两个变量」把它逼出来；
- 数据目录拿不到时退 3（未配置）而不是 0 或 1；
- stdout / stderr 真的被改成 UTF-8 —— Windows 上默认跟系统代码页走，中文会
  变乱码或直接抛 UnicodeEncodeError，而那只有在真机上才看得见。
"""
from __future__ import annotations

import io
from pathlib import Path

import counter
import pytest
from counter import CLICK_INCREMENT, HEADLESS_RUN_LOG_NAME, __version__


def _no_window(monkeypatch) -> list:
    """把开窗那条路换成探针：被调到就是违约，测试要看得见。"""
    opened: list = []
    monkeypatch.setattr(counter, "copy_assets", lambda page_dir: page_dir)
    monkeypatch.setattr(counter, "run", lambda url, **kwargs: opened.append(kwargs))
    return opened


def test_the_headless_signal_opens_no_window(monkeypatch, tmp_path):
    """信号在 → 一扇窗都不开。

    断言的是 ``run`` 一次没被调，不是「窗口 hidden=True」：hidden 那条路仍然
    走单实例守卫，仍然可能把别人的窗带到前台（#214），对无头义务不算数。
    """
    opened = _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()

    assert opened == []


def test_without_the_signal_the_window_still_opens(monkeypatch, tmp_path):
    """信号不在 → 手动那条路一个字没变。防「加了无头分支把开窗弄没了」。"""
    opened = _no_window(monkeypatch)
    monkeypatch.delenv(counter.HEADLESS_SIGNAL_ENV, raising=False)
    monkeypatch.delenv("APP_SMOKE", raising=False)

    counter.main()

    assert len(opened) == 1
    assert opened[0]["single_instance"] == "counter"


def test_smoke_and_headless_are_two_different_paths(monkeypatch, tmp_path):
    """两个变量同时在时，走的是**无头**那条，不是冒烟。

    这一条逼出「把两个环境变量合并成一个条件」的实现：那样写的话定时路径会去
    跑冒烟测试脚本（开窗、跑断言、按断言结果决定退出码），而不是业务。合并的
    实现在这里会调到 ``run``，当场红。
    """
    opened = _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv("APP_SMOKE", "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()

    assert opened == []


def test_a_headless_run_leaves_something_to_check(monkeypatch, tmp_path, capsys):
    """跑完之后数据目录里必然多一行 —— 只看退出码分不出「真跑了」和「什么都没做」。"""
    _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()

    log = tmp_path / HEADLESS_RUN_LOG_NAME
    assert log.exists()
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert f"增量 {CLICK_INCREMENT}" in lines[0]
    assert __version__ in capsys.readouterr().out


def test_a_second_headless_run_appends_rather_than_overwrites(monkeypatch, tmp_path):
    """第二趟追加，不是覆盖：定时任务会跑很多次，每次都该留下痕迹。"""
    _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()
    counter.main()

    lines = (tmp_path / HEADLESS_RUN_LOG_NAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_no_data_dir_exits_with_the_not_configured_code(monkeypatch):
    """拿不到数据目录 → 退出码 **3**（未配置），不是 0 也不是 1。

    契约把 3 单独留给「未配置」：客户端据此在界面上说「请先打开小程序设置
    参数」，而不是把它记成一次失败去打扰用户。退 0 更糟——那会谎报成功。
    """
    _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.delenv(counter.TOOL_DATA_DIR_ENV, raising=False)

    with pytest.raises(SystemExit) as excinfo:
        counter.main()

    assert excinfo.value.code == 3


def test_a_blank_data_dir_counts_as_missing(monkeypatch):
    """变量在但值是空白 = 没拿到。空串当路径用会写到当前目录去。"""
    _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, "   ")

    with pytest.raises(SystemExit) as excinfo:
        counter.main()

    assert excinfo.value.code == 3


def test_stdio_is_switched_to_utf8(monkeypatch):
    """真的调了 ``reconfigure(encoding="utf-8")``，两个流都要。

    这条只能这么验：本机（macOS/Linux）默认就是 UTF-8，光看输出对不对证明不了
    Windows 上也对——那儿默认是系统 ANSI 代码页。所以钉的是「那个调用发生了」。
    """
    asked: list[tuple[str, str]] = []

    class _Stream(io.StringIO):
        def __init__(self, name: str) -> None:
            super().__init__()
            self._name = name

        def reconfigure(self, *, encoding: str) -> None:  # type: ignore[override]
            asked.append((self._name, encoding))

    monkeypatch.setattr(counter.sys, "stdout", _Stream("stdout"))
    monkeypatch.setattr(counter.sys, "stderr", _Stream("stderr"))

    counter._force_utf8_stdio()

    assert asked == [("stdout", "utf-8"), ("stderr", "utf-8")]


def test_forcing_utf8_survives_a_stream_without_reconfigure(monkeypatch):
    """替身流没有 ``reconfigure`` 时不炸 —— 冻结产物里 stdout 可能被换掉。"""
    monkeypatch.setattr(counter.sys, "stdout", io.StringIO())
    monkeypatch.setattr(counter.sys, "stderr", io.StringIO())

    counter._force_utf8_stdio()  # 不抛就算过


def test_the_headless_path_actually_switches_the_encoding(monkeypatch, tmp_path):
    """无头那条路**真的调了** ``_force_utf8_stdio``。

    上面两条验的是那个函数自己做得对，绕过了「谁来调它」这一步——把
    ``run_headless`` 里那句删掉，它们照样全绿，而 Windows 上中文就变乱码了。
    做 mutation 时正是这么漏的（该红没红），所以补这一条把调用本身钉住。
    """
    called: list[bool] = []
    _no_window(monkeypatch)
    monkeypatch.setattr(counter, "_force_utf8_stdio", lambda: called.append(True))
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()

    assert called == [True], "无头路径没有把 stdio 切成 UTF-8"


def test_the_run_log_is_written_as_utf8(monkeypatch, tmp_path):
    """记录文件本身也是 UTF-8（中文「增量」两个字要读得回来）。"""
    _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))

    counter.main()

    raw = (tmp_path / HEADLESS_RUN_LOG_NAME).read_bytes()
    assert raw, "空文件证明不了编码：空字节串在任何编码下都合法"
    assert "增量".encode() in raw
    raw.decode("utf-8")  # 解不出来就抛


def test_the_data_dir_is_created_when_missing(monkeypatch, tmp_path):
    """数据目录不存在时自己建 —— 第一次定时跑可能早于用户第一次打开界面。"""
    _no_window(monkeypatch)
    target = tmp_path / "never-made"
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "1")
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(target))

    counter.main()

    assert (target / HEADLESS_RUN_LOG_NAME).exists()


def test_only_the_exact_signal_value_counts(monkeypatch, tmp_path):
    """信号是 ``"1"`` 才算数：契约写死了这个值，别把 ``"0"`` / ``"false"`` 也当真。"""
    opened = _no_window(monkeypatch)
    monkeypatch.setenv(counter.HEADLESS_SIGNAL_ENV, "0")

    counter.main()

    assert len(opened) == 1, "信号是 '0' 却走了无头路"


def test_data_dir_reads_the_contract_variable(monkeypatch, tmp_path):
    """``data_dir()`` 读的就是契约那个变量名，不是随便一个环境变量。"""
    monkeypatch.setenv(counter.TOOL_DATA_DIR_ENV, str(tmp_path))
    assert counter.data_dir() == Path(str(tmp_path))

    monkeypatch.delenv(counter.TOOL_DATA_DIR_ENV, raising=False)
    assert counter.data_dir() is None


def test_the_contract_variable_names_are_the_ones_the_client_sets():
    """两个变量名一字不差 —— 拼错的话在本机毫无症状，只在真机上「到点什么都没发生」。"""
    assert counter.HEADLESS_SIGNAL_ENV == "MSLAUNCHPAD_SCHEDULED"
    assert counter.TOOL_DATA_DIR_ENV == "MSLAUNCHPAD_DATA_DIR"
