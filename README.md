# DST Zhipu AI NPC Talk

这是一个私人使用的《饥荒联机版》服务器模组原型：常见非 Boss 生物会定时从本机代理获取一句智谱 AI 生成的中文短台词。API Key 只放在代理进程里，不写进 Lua 模组。

## 目录

- `ai_npc_talk_mod/`：放进 DST 的 `mods` 目录后启用。
- `proxy/zhipu_dst_proxy.py`：本机 HTTP 代理，监听 `127.0.0.1:8765`。
- `proxy/zhipu_proxy_gui.py`：图形版代理启动器源码，Windows 和 macOS 共用。
- `dist/DST-Zhipu-Proxy.exe`：打包后给房主使用的图形版代理程序。
- `dist-macos/DST-Zhipu-Proxy.app`：在 Mac 上打包后给房主使用的图形版代理程序。
- `build_macos_app.command`：macOS `.app` 构建脚本，需要在 Mac 上运行。

## 启动代理（Windows 图形版）

房主或专用服务器机器运行 `DST-Zhipu-Proxy.exe`：

1. 双击打开程序。
2. 输入自己的智谱 API Key。
3. 点击“启动代理”。
4. 点击“测试连接”，确认模型显示为 `glm-5.1` 且 API Key 已加载。
5. 保持窗口打开，再启动或进入 DST 世界。

这个图形程序不会把 API Key 写入磁盘；停止代理或关闭窗口后，Key 会从当前进程清除。

## 启动代理（macOS 图形版）

房主或专用服务器机器运行 `DST-Zhipu-Proxy.app`：

1. 双击打开程序。
2. 如果 macOS 提示来自未知开发者，在“系统设置 > 隐私与安全性”里允许打开，或右键程序选择“打开”。
3. 输入自己的智谱 API Key。
4. 点击“启动代理”。
5. 点击“测试连接”，确认模型显示为 `glm-5.1` 且 API Key 已加载。
6. 保持窗口打开，再启动或进入 DST 世界。

macOS 版同样不会保存 API Key；停止代理或关闭窗口后，Key 会从当前进程清除。

## 备用：Python 脚本启动

在 PowerShell 里进入本目录后运行：

```powershell
$env:ZHIPU_API_KEY="你的智谱API Key"
python .\proxy\zhipu_dst_proxy.py
```

检查代理：

```powershell
Invoke-WebRequest http://127.0.0.1:8765/health
```

检查一次台词生成，并显示智谱错误详情：

```powershell
Invoke-WebRequest "http://127.0.0.1:8765/say?npc=rabbit&entity=test-rabbit-1&event=idle&season=autumn&phase=day&day=0&cave=0&debug=1"
```

如果没有设置 `ZHIPU_API_KEY`，代理仍会返回本地备用台词，方便测试模组是否能正常工作。

可选环境变量：

- 模型固定为 `glm-5.1`，不需要设置 `ZHIPU_MODEL` 或 `DST_AI_ZHIPU_MODEL`。
- `DST_AI_PROXY_PORT`：默认 `8765`。
- `DST_AI_MIN_TALK_CHARS`：默认 `10`，也就是台词至少 10 个中文字符。
- `DST_AI_MAX_TALK_CHARS`：默认 `20`，也就是台词最多 20 个中文字符。
- `DST_AI_CACHE_SECONDS`：默认 `120`。缓存按单个 NPC 的 `entity` 区分，不同猪人或兔人不会共享同一句缓存台词。
- `DST_AI_MIN_API_INTERVAL`：默认 `4` 秒，防止短时间大量请求。

## 重新编译 Windows 图形版代理

开发机需要先安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

然后在本目录运行：

```powershell
python -m PyInstaller --noconsole --onefile --name DST-Zhipu-Proxy --paths proxy proxy/zhipu_proxy_gui.py
```

编译结果会生成在：

```text
dist\DST-Zhipu-Proxy.exe
```

## 编译 macOS 图形版代理

PyInstaller 不能在 Windows 上交叉编译 macOS `.app`，所以这一步必须在 Mac 上运行。

在 Mac 上安装 Python 3 后，把整个项目文件夹复制到 Mac，然后在终端进入本目录运行：

```zsh
chmod +x build_macos_app.command
./build_macos_app.command
```

编译结果会生成在：

```text
dist-macos/DST-Zhipu-Proxy.app
```

如果只是给自己用，可以直接打开这个 `.app`。如果要发给朋友，建议把 `DST-Zhipu-Proxy.app` 压缩成 zip 后发送。

## 安装模组

把 `ai_npc_talk_mod` 整个文件夹复制到 DST 安装目录的 `mods` 文件夹，例如：

```text
...\Steam\steamapps\common\Don't Starve Together\mods\ai_npc_talk_mod
```

然后在创建或配置世界时启用服务器模组 `AI NPC Talk - Zhipu Private`。

## 注意

- 代理必须运行在开服机器上；专用服务器就放在专用服务器机器上运行。
- 客机不需要运行代理，也不需要智谱 API Key；客机只需要安装同一个本地模组。
- 模组只请求 `http://127.0.0.1:8765/say`。如果当前 DST 版本连本机 `QueryServer` 都拦截，实时生成就无法稳定工作，只能改成预生成或缓存台词。
- 模组不会修改原始台词表，也不会覆盖 NPC 脑行为；代理失败时会自动说本地备用台词。
- 代理对支持思考模式的模型会显式设置 `thinking.type = disabled`，因为 NPC 短台词不需要长推理，能减少延迟和额外输出。
