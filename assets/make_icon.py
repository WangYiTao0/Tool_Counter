"""Counter 的图标生成（全家图标风格的可抄样板，照 msui README「图标」一节）——一次出两样：exe 用的 icon.ico（四档）与工具列表用的 icon.png（256×256）。

全家风格：**品牌红圆角底板 + 白色简笔符号**。别的仓整份照抄，只改 ``draw_symbol``
（画自己工具的符号），然后在仓根::

    pip install pillow          # 只在生成时用；不进 requirements、不进产物
    python assets/make_icon.py

生成的两份文件入仓；spec 的 EXE(...) 挂 icon.ico，miniprog.toml 的 icon 指向 icon.png。
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BRAND = "#db021d"  # msui tokens.css 的 --brand（图标底板正是品牌用途）
WHITE = "#ffffff"
SIZE = 256  # 基准画布；ico 的其余档由 LANCZOS 下采样
ICO_LAYERS = [(256, 256), (48, 48), (32, 32), (16, 16)]  # ico 里的四档
HERE = Path(__file__).resolve().parent


def draw_symbol(d: ImageDraw.ImageDraw) -> None:
    """Counter 的符号：三根计数竖条（画「正」字那种 tally 意象）。每仓只改这个函数。

    几何简笔、线宽 ≥ 边长 15% 才在 16px 下不糊；刻意不用「+」——白十字放红底上像
    红十字会徽（受保护标志）。
    """
    top, bottom, thick, gap = 64, 192, 30, 14
    left = (SIZE - 3 * thick - 2 * gap) // 2
    for i in range(3):
        x = left + i * (thick + gap)
        d.rounded_rectangle([x, top, x + thick, bottom], radius=thick // 2, fill=WHITE)


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))  # 透明底，圆角外露出背景
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=56, fill=BRAND)  # 56/248 ≈ 22%
    draw_symbol(d)
    img.save(HERE / "icon.ico", sizes=ICO_LAYERS)
    img.save(HERE / "icon.png", optimize=True)
    print(f"icon -> {HERE / 'icon.ico'}, {HERE / 'icon.png'}")


if __name__ == "__main__":
    main()
