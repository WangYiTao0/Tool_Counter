# Tool_Counter

## 本仓是什么

本仓是**两份契约的官方活样例**：一个计数器小程序（数字 + 一个「+N」按钮），
除了演示「怎么接入 MSToolbox」与「怎么用 msui 做界面」之外没有别的用途。
想接入的同事把本仓当成能直接照抄的标准答案，而不是从契约文字里自己拼装第一版。

两份契约各指一处，本 README 不复述细则：

1. **MSToolbox 接入契约**（怎么打包、发布、被客户端分发）——见 MSToolbox 仓的
   [`docs/接入契约.md`](https://github.com/WangYiTao0/MSToolbox/blob/master/docs/接入契约.md)。
   对应本仓：`miniprog.toml`、`build.py` + `Tool_Counter.spec`、
   `.github/workflows/publish.yml`。
2. **msui 界面契约**（怎么开窗、页面与共享样式怎么组织、js_api 桥怎么写）——见
   [msui 仓 README](https://github.com/WangYiTao0/msui)（五步从零到跑起来）。
   对应本仓：`requirements.txt` 里那行钉版本 wheel URL、`counter.py` 的
   三步启动与 `CounterApi` 桥、`pages/`、`tests/test_style_gate.py`。

## 本仓演示的范式

- **业务在 Python、页面只管展示**：计数状态与 `CLICK_INCREMENT` 都在
  `counter.py` 的 `CounterApi` 里，页面经 pywebview 的 js_api 桥来调，
  应答走 `msui.bridge.Serializer` 的忙碌信封（连点丢弃、不排队）。
- **样式零手写**：`pages/index.html` 只写语义化标签，长相全来自 msui 启动时
  落进来的 `tokens.css` / `base.css`（不入仓，见 `pages/.gitignore`）；
  `tests/test_style_gate.py` 的闸门盯着对比度与游离色值。
- **打包对 msui 零资源配置**：`Tool_Counter.spec` 的 `datas` 只声明本仓自己的
  `pages/`，msui 的样式与元数据由包自带 hook 收齐。
- **无人值守冒烟**：`APP_SMOKE=1` 隐藏开窗、自动点一次按钮核对显示/样式/
  msui 版本横幅后自关（照 msui examples 的做法扩展了断言）。

## 本地开发

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt pytest
.venv/bin/python -m pytest          # 闸门测试
APP_SMOKE=1 .venv/bin/python counter.py   # 隐藏冒烟（不上屏）
.venv/bin/python counter.py         # 真开窗看一眼
```

## 发版清单

1. 改 `counter.py` 里的 `__version__` 常量与 `CLICK_INCREMENT` 常量。
2. `git commit`。
3. 打 tag，格式 **`v<版本号>`**（如 `v1.3.0`），`git push` 该 tag 触发 CI。
   注意这是**本仓**的 tag；发布仓那边形如 `counter-v1.3.0` 的 release 标签
   由 CI 自动拼出来，不用你管（两层格式别混，接入契约 §2 写了）。
4. CI 跑绿、产物发到发布仓后，**提醒维护者**在本机补跑一次
   `mstoolbox-publish`（先 `--dry-run` 看一眼再真发）——CI 只把产物传到
   发布仓，不会自动更新 catalog，业务端要等 catalog 刷新才能看到新版本。
