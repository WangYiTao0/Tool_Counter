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
