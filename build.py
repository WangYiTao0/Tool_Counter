"""最小 PyInstaller onedir 打包脚本。

在 Windows CI 上被 `.github/workflows/publish.yml` 以 `python build.py` 调用,
把 counter.py 打成 dist/Tool_Counter/Tool_Counter.exe(文件夹模式,不是
onefile——接入契约 §2 要求 onedir)。产物目录名必须与 miniprog.toml 里的
entry 声明一致。

不写 .spec 文件:命令行参数已经够用,一个 spec 文件对样板仓来说是多余的
复杂度。小程序不需要 Velopack ——自更新是 MSToolbox 本体客户端的事,小程序
只管把 onedir 产物发布到发布仓,由客户端下载启动。
"""

import subprocess
import sys


def main() -> int:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onedir",
        "--windowed",
        "--name",
        "Tool_Counter",
        "counter.py",
    ]
    result = subprocess.run(args)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
