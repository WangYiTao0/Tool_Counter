"""最小 PyInstaller onedir 打包脚本。

在 Windows CI 上被 `.github/workflows/publish.yml` 以 `python build.py` 调用,
按 Tool_Counter.spec 把 counter.py + pages/ 打成
dist/Tool_Counter/Tool_Counter.exe(文件夹模式,不是 onefile——接入契约 §2
要求 onedir)。产物目录名必须与 miniprog.toml 里的 entry 声明一致。

改用 .spec 文件的原因:页面目录 pages/ 要按 msui 契约收进产物
(datas 只声明本仓自己的 pages/,msui 的样式与元数据由包自带 hook 零配置
收齐——见 msui 仓 README「打包成冻结产物」一节),spec 是 PyInstaller 表达
datas 的正规位置。小程序不需要 Velopack——自更新是 MSLaunchpad 本体客户端
的事,小程序只管把 onedir 产物发布到发布仓,由客户端下载启动。
"""

import subprocess
import sys


def main() -> int:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "Tool_Counter.spec",
        "--noconfirm",
        "--distpath",
        "dist",
        "--workpath",
        "build",
    ]
    result = subprocess.run(args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
