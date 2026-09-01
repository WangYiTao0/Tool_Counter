"""exe 图标生成——全家图标风格约定的可抄样板（msui README「图标」一节）。

约定（一句话版）：**品牌红圆角底板 + 白色简笔符号**，一份 .ico 内含 256/48/32/16 四档。

- 底板：圆角方形，msui token ``--brand``（#db021d），圆角 ≈ 22% 边长；
- 符号：白色、几何简笔、一眼可辨——16px 下不糊的判据是线宽 ≥ 边长 15%；
- 挂法：spec 的 EXE(...) 加一行 ``icon=os.path.join(SPECPATH, "assets", "icon.ico")``。

别的仓照抄本文件，只改 ``draw_symbol``（画自己工具的符号），然后::

    pip install pillow      # 仅生成时用；exe 打包不需要（spec excludes 挡着）
    python assets/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BRAND = "#db021d"  # msui tokens.css 的 --brand（品牌红，图标底板正是品牌用途）
WHITE = "#ffffff"
SIZE = 256  # 基准画布；其余档由 LANCZOS 下采样（简笔几何形缩得住）


def draw_symbol(d: ImageDraw.ImageDraw) -> None:
    """Counter 的符号：三根计数竖条（画「正」字那种 tally 意象）。

    每仓改这一个函数画自己的符号。刻意不用「+」——白十字放红底上像红十字会徽
    （受保护标志），避开。
    """
    top, bottom, thick, gap = 64, 192, 30, 14
    left = (SIZE - 3 * thick - 2 * gap) // 2
    for i in range(3):
        x = left + i * (thick + gap)
        d.rounded_rectangle([x, top, x + thick, bottom], radius=thick // 2, fill=WHITE)


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=56, fill=BRAND)  # 56/248 ≈ 22%
    draw_symbol(d)
    out = Path(__file__).resolve().parent / "icon.ico"
    img.save(out, sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"icon -> {out}")


if __name__ == "__main__":
    main()
