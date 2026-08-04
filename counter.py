"""Counter —— MSToolbox 接入契约的官方样板应用。

这是「MSToolbox 小程序接入契约」的活样例:一个纯 tkinter 计数器,只做一件
事——点击按钮让数字 +1。本仓的目的不是这个应用本身,而是演示一个小程序仓
要满足接入契约(见 MSToolbox 仓 docs/接入契约.md)需要具备哪些东西:
`miniprog.toml`、`build.py`、`.github/workflows/publish.yml`、README。

发新版时只改下面两个常量附近:`__version__`(窗口标题读它)与
`CLICK_INCREMENT`(每次点击的增量)。
"""

import tkinter as tk

__version__ = "1.2.0"

# 每次点击按钮时数字增加的量。样板仓的三个版本(v1.0.0/v1.1.0/v1.2.0)
# 只靠改这一个数字演示两轮更新,行为差异一眼可辨。
CLICK_INCREMENT = 3


def main() -> None:
    count = 0

    root = tk.Tk()
    root.title(f"Counter v{__version__}")

    label = tk.Label(root, text=str(count), font=("Segoe UI", 32))
    label.pack(padx=40, pady=20)

    def on_click() -> None:
        nonlocal count
        count += CLICK_INCREMENT
        label.config(text=str(count))

    # 按钮文字从增量常量推导:v1.1.0 把 CLICK_INCREMENT 改成 2 时,
    # 按钮自动变「+2」——发新版真的只改常量,不用记得来改这里。
    button = tk.Button(
        root, text=f"+{CLICK_INCREMENT}", command=on_click, font=("Segoe UI", 14)
    )
    button.pack(padx=40, pady=(0, 20))

    root.mainloop()


if __name__ == "__main__":
    main()
