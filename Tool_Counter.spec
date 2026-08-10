# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir spec（照抄 msui 仓 examples/minimal/app.spec，只改入口
# 与 name）。关键点：对 msui 的资源与元数据**零配置**——tokens.css /
# base.css / dist-info 全由 msui 包自带的 pyinstaller40 hook 收齐。
# datas 只声明自己持有的页面目录。
# name 必须是 Tool_Counter：产物目录 dist/Tool_Counter/ 与 miniprog.toml
# 的 entry = "Tool_Counter.exe" 都钉在这个名字上（接入契约 §2）。
import os

a = Analysis(
    [os.path.join(SPECPATH, "counter.py")],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(SPECPATH, "pages"), "pages")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# 开发机上冒烟落地过的 tokens.css / base.css 副本（gitignored、但在盘上）
# 会被 pages/ 整目录收集顺手带进产物——纯冗余：运行时 copy_assets 每次启动
# 都无条件覆盖，产物里那两份副本永远不会被用到。按目的地路径剔掉；CI 的
# 干净 checkout 本来就没有它们，此过滤不改变 CI 产物。
def _is_landed_css(dest: str) -> bool:
    parts = dest.replace("\\", "/").split("/")
    return parts[0] == "pages" and parts[-1] in ("tokens.css", "base.css")

a.datas = [entry for entry in a.datas if not _is_landed_css(entry[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Tool_Counter",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # 窗口程序；冒烟只看退出码，不需要控制台
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Tool_Counter",
)
