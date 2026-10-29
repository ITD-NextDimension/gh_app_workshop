# 从一个想法，到一个工作助理

[简体中文](README.md) | [繁體中文](README.traditional.md)

## GitHub Copilot App 动手实验 · Python 版

欢迎加入虚构的「晨光创意工作室」。你不是程序员，而是负责团队活动、产品传播和每周安排的业务同事。接下来的四次委托，会带你从“把需求说清楚”走到“让多个 Agent 分工协作”。

**这里的 Copilot 是 GitHub Copilot App，不是 Microsoft 365 Copilot。** 不要求计算机专业背景，但需要按步骤打开终端、复制命令，并核对执行结果。

**课程总时长：3 小时（180 分钟）**，四个 Lab 按 35 + 45 + 45 + 55 分钟安排。

| Lab | 建议时间 | 你的委托 | 新学到的 App 能力 | 交付作品 |
|---|---:|---|---|---|
| [Lab 1](Lab1/README.md) | 35 分钟 | 为团队做一个中国象棋小游戏 | 本地文件夹、会话、模型、Autopilot、反馈与验证 | HTML 游戏 + Python 规则引擎 |
| [Lab 2](Lab2/README.md) | 45 分钟 | 为 Surface 做一段产品短片 | 提供资料、Plan 审阅、切换 Autopilot、约束输出 | edge-tts 中文女声 + HyperFrames CLI 2 分钟 9:16 MP4；**不构建播放界面** |
| [Lab 3](Lab3/README.md) | 45 分钟 | 向同事讲清微软财报 | SDK、单 Agent、来源约束、分析视图 | Power BI 风格财报页面 + Python 单 Agent |
| [Lab 4](Lab4/README.md) | 55 分钟 | 把邮件和会议整理成本周待办 | 多 Agent 分工、Canvas 扩展、权限与持久化 | Python 工作助理 + Canvas 薄适配器 |
| **合计** | **180 分钟（3 小时）** |  |  |  |

四个 Lab 的目标模型都是 **GPT-6 Luna**，SDK 中的准确 ID 是 `gpt-6-luna`。不能用页面上写着模型名称，来代替实际模型调用证明。本课程的真实调用记录保存在各 Lab 的 `Code/` 中。

## 课程演示范围

每个 Lab 都配有可运行的 Python 代码和明确的验收步骤；公开页面使用虚构练习数据和经过筛选的作品截图。

| 范围 | 课程内容 |
|---|---|
| Lab 1 | Python 象棋规则引擎与浏览器小游戏；按步骤检查走棋、悔棋和重开 |
| Lab 2 | edge-tts 中文女声与 HyperFrames CLI；目标为 1080×1920、30fps、120 秒成片 |
| Lab 3 | 基于 Microsoft FY2025 年报数据的 Python 分析和交互式经营观察室 |
| Lab 4 | 用明确标注的虚构邮件与日历资料练习多 Agent、排程和 Canvas 工作流 |
| 个人账户资料 | 真实邮箱、日历和账户登录只属于学员本地授权实操；不包含在公开演示中 |
| Canvas | SDK 协议、扩展注册和 App 原生侧栏是不同验收面；请按当前 App 能力分别检查 |

公开页面只发布课程说明、源码和筛选后的教学截图。本机运行日志、个人账户资料和私人截图不属于课程公开材料。

## 开始前：只准备一次

### 1. 准备工具

在自己的电脑上安装 GitHub Copilot App，并用有 Copilot 权限的账号登录。确认模型选择器中有 **GPT-6 Luna**。如果没有，请先解决账号或组织的模型权限，**不要悄悄换成另一个模型继续当作本实验通过**。

还需要 Python 3.11+、Copilot CLI，以及 Lab 2 专用的 Node.js 22+ 和 FFmpeg。不同系统与工具版本可能有差异，开始前请运行版本预检命令。

打开系统终端，进入本课程文件夹。后文出现的命令，除明确写出 `cd` 的片段外，**都在包含本 README 的课程根目录执行**。

```bash
python3 --version
copilot --version
node --version
ffmpeg -version
ffprobe -version
```

如 Copilot CLI 尚未登录，运行 `copilot login` 并在它打开的官方页面完成登录。不要把密码或令牌粘贴到提示词、代码或截图中。App 和 SDK 的登录状态需要分别确认，不能假设一个成功就代表另一个也成功。

### 2. 建立 Python 环境

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt --index-url https://packagefeedproxy.microsoft.io/pypi/simple/
python -m playwright install chromium
python tools/probe.py
```

Windows PowerShell 的前两条改为：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 组织策略禁止激活，不要修改组织策略；可直接使用 `.\.venv\Scripts\python.exe` 替代后文的 `python`。

**通过条件：** `verification/capabilities.json` 中有 `gpt-6-luna`，命令没有认证错误。若提示权限或登录错误，先处理错误再继续。

### 3. 在 App 打开课程

在 App 的 **Sessions** 旁点 **+**，选择 **Open local folder**，打开整个课程根目录。四个 Lab 按顺序做，每个 Lab 新建一个会话，并在提示词中约束只修改相应 Lab 的 `Code/`。

这是本地文件夹实验，**没有自动创建 Git 分支或隔离 worktree**。不要让多个会话同时修改同一文件。App 标签和按钮随版本变化时，以 [官方会话文档](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions) 和当前 `/` 命令列表为准。

## 四个词，先弄明白

| 名词 | 用日常工作理解 |
|---|---|
| Plan | 先交方案；你看清楚做什么、用什么资料、如何验收，再批准 |
| Autopilot | 方案明确后，让助理连续执行；不代表可以忽略账号权限、数据保护或组织政策 |
| Agent / SDK | Agent 是带职责的助理；SDK 是让 Python 程序调用它的工具箱，不是另一个聊天窗口 |
| Canvas | App 旁边的交互工作面；它的网页渲染内容和 Canvas 注册协议不是同一回事 |

**Python 统一约定：** 后端、计算、Agent、采集、排程、测试与运行入口使用 Python。浏览器交互仍需要少量 HTML/CSS/JavaScript。HyperFrames 官方引擎依赖 Node.js；App 扩展的官方入口必须是 `extension.mjs`。Lab 4 的该入口仅做注册和转发，不在 JavaScript 中实现业务逻辑。

## 目录与证据

```text
Lab1/README.md    Lab1/Code/    Lab1/screenshots/
Lab2/README.md    Lab2/Code/    Lab2/screenshots/
Lab3/README.md    Lab3/Code/    Lab3/screenshots/
Lab4/README.md    Lab4/Code/    Lab4/screenshots/
tools/           共享 Python 工具
tests/           业务规则测试
```

`01-execution-record.png` 是 **真实 JSON 记录渲染后的浏览器截图**，不是伪造的 App 模式选择截图。各 README 每步都会注明图片的性质；需要学员补拍的 App 原生图片单独列出，不能用运行记录替换。

公开 Pages 构建只复制各 Lab 的虚构演示截图；本机验收报告及个人账户截图不会发布。

## 讲师复核

核心依赖安装完成后，可以重复执行：

```bash
python -m pytest -q tests/test_labs.py
python Lab4/Code/canvas_smoke.py
python tools/verify.py
```

第三条会启动短期本地服务、验证四个作品、保存截图，然后关闭自己启动的服务；**不是启动后就永久在线**。学员体验时请按各 Lab 的 `app.py` 命令启动，并保持终端开启。

真实扩展的验证见 Lab 4，需要先从当前 `extensions_manage guide` 获取 SDK 路径。`tools/verify.py` 不读取真实 Outlook，不自动重跑收费模型调用，也不把私人数据写进截图。

模型调用、网络下载与视频渲染会消耗时间和额度。已有 `generation.json`、`story.json`、`analysis.json`、`plan.json` 是此次运行结果；重新调用时措辞可能不同，验收应看约束与功能，不要求逐字相同。
