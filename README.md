# Tool_Counter

## 本仓是什么

本仓是 MSToolbox 小程序接入契约的**官方样板仓**——一个纯 tkinter 计数器,
除了演示「怎么接入 MSToolbox」之外没有别的用途。想把自己的工具接入
MSToolbox 的同事,可以把本仓当成能直接照抄的活样例,而不是从契约文字里
自己拼装第一版。

完整规则见 MSToolbox 仓的
[`docs/接入契约.md`](https://github.com/WangYiTao0/MSToolbox/blob/master/docs/接入契约.md)。

## 照抄接入步骤

把自己的工具接入 MSToolbox,大致就是把本仓这四样东西复制到自己仓里,
改成自己工具的值:

1. **应用本身**——对照 `counter.py`。单文件也好、多文件也好,零第三方
   依赖不是硬要求,但要用 PyInstaller 能 `--onedir` 打出来。
2. **`miniprog.toml`**——照抄本仓的 [`miniprog.toml`](./miniprog.toml),
   把 `id` / `name` / `category` / `entry` 四个字段改成自己工具的值。
   `id` 一旦发布不可改,字符集见契约 §3。
3. **`build.py`**——照抄本仓的 [`build.py`](./build.py),把
   `--name` 和入口脚本换成自己的,让产物目录名与 `miniprog.toml` 里的
   `entry` 对得上。同时补一份 `requirements.txt`(至少含 `pyinstaller`),
   CI 的 `Install deps` 步骤要用。
4. **`.github/workflows/publish.yml`**——从 MSToolbox 仓的
   [`templates/publish.yml`](https://github.com/WangYiTao0/MSToolbox/blob/master/templates/publish.yml)
   逐字复制,**只改 `env` 里的 `TOOL_ID` 和 `DIST_DIR`** 这两行,其余一个
   字符都不要动。如果模板套不上自己的工具,回 MSToolbox 仓改模板,不要
   在自己仓里改造这份副本。

## 发版清单

1. 改 `counter.py` 里的 `__version__` 常量与 `CLICK_INCREMENT` 常量。
2. `git commit`。
3. 打 tag,格式 `counter-v<版本号>`(如 `counter-v1.0.0`),`git push` 该
   tag 触发 CI。
4. CI 跑绿、产物发到发布仓后,**提醒维护者**在本机补跑一次
   `mstoolbox-publish`(先 `--dry-run` 看一眼再真发)——CI 只把产物传到
   发布仓,不会自动更新 catalog,业务端要等 catalog 刷新才能看到新版本。
