# GeoVela：大语言模型驱动的桌面 GIS 应用设计与实现报告

> 项目版本：0.2.0  
> 报告日期：2026年11月6日  
> 测试平台：Windows 11；PowerShell 7.6.9；Node.js 24.20.0；npm 11.19.0；Python 3.14.0；Git 2.49.0.windows.1  
> 数据采集与集中测试日期：2026年11月5日

## 摘要

GeoVela 是一个以自然语言为交互入口，融合桌面应用、GIS 地图渲染、Python 空间计算与大语言模型 Agent 的智能地理信息系统。项目采用 Electron、React、TypeScript、MapLibre GL JS 与 Python Sidecar 的混合架构，将空间数据管理、地图可视化、代码执行、工作流、Operation、后台 Worker、运行记录和报告输出集中于同一桌面环境。用户可以用“加载校园 CSV”“按建筑高度三维显示”“分析宿舍到奶茶店的地铁可达性”等自然语言完成 GIS 操作。

项目使用四组真实数据验证完整流程：全国48个代表性城市近7天天气、无锡市1654家奶茶店、江南大学234个校园要素，以及由20处宿舍、无锡地铁、步行网络和275家有效奶茶店构成的5500条可达性结果。测试覆盖点线面、标签、分类与分级符号、三维拉伸、时序统计、POI分析、多网络最短路径、图表与报告生成。结果表明，GeoVela 已形成“数据导入—字段识别—空间处理—地图表达—统计分析—成果输出”的闭环，可用于高校 GIS 教学、课程设计和轻量空间分析。

**关键词**：桌面 GIS；大语言模型；Agent；MapLibre；Electron；空间可达性；三维地图

---

## 1. 项目背景与目标

传统 GIS 软件功能强大，但存在学习曲线陡、参数多、过程分散和成果复现困难等问题。大语言模型可以理解自然语言和生成代码，但若只在聊天框中返回脚本，仍无法可靠管理图层、控制地图状态和沉淀成果。GeoVela 关注的核心问题是：让大语言模型在受控、可追踪的桌面 GIS 中真正执行任务，而不仅是回答 GIS 问题。

项目目标如下：

1. 构建可安装运行的 Windows 桌面应用；
2. 支持 CSV、GeoJSON、Shapefile、KML、GeoTIFF 等常用数据；
3. 用自然语言驱动读取、计算、制图、三维显示和导出；
4. 支持点、线、面、聚合、标签、分类/分级设色和基础三维拉伸；
5. 保存工具调用、代码、产物与异常，使过程可检查；
6. 用多个真实场景验证系统，不以单一演示代替测试；
7. 明确数据来源、坐标系、估算参数和局限。

GeoVela 当前定位不是替代 ArcGIS Pro 或 QGIS，而是探索一种适合学生和非专业用户的自然语言 GIS 工作方式。

## 2. 需求分析

### 2.1 功能需求

- 工程与文件管理：打开工程、浏览目录、预览 CSV/Markdown、管理脚本和输出；
- 地图显示：加载数据、缩放定位、图层开关、排序和透明度控制；
- 地图表达：点线面符号、分类/分级、大小映射、标签、聚合和图例；
- 三维表达：俯视/倾斜切换，并按 `height` 或层数拉伸建筑；
- Agent 对话：理解任务、选择工具、运行 Python、调用地图接口并解释结果；
- 空间分析：缓冲、统计、最短路径、可达性和专题图；
- 成果管理：输出 CSV、GeoJSON、图片、Markdown 报告和运行记录；
- 桌面发布：生成 Windows NSIS 安装程序和免安装目录。

### 2.2 非功能需求

- 易用：中文界面、亲和视觉、操作反馈清晰；
- 可扩展：地图、Agent 工具、Operation、Workflow、Worker 解耦；
- 可追踪：工具、代码、异常、结果均可回看；
- 高性能：密集点聚合、标签按需显示、路线按选择显示；
- 安全：API Key 不入库，危险操作受权限治理；
- 可复现：原始数据、处理中间表、脚本、结果和说明分层保存。

## 3. 总体设计

### 3.1 技术架构

| 层 | 技术 | 职责 |
|---|---|---|
| 桌面容器 | Electron 30 | 窗口、菜单、文件系统、IPC、打包 |
| 前端 | React 18、TypeScript、Vite、Tailwind | UI、编辑器、状态与交互 |
| 地图 | MapLibre GL JS 4 | WebGL地图、图层、标签、三维拉伸 |
| 状态 | Zustand | 地图、图层、聊天、运行记录 |
| 后端 | Python、FastAPI、uvicorn | Agent、工具、空间计算与RPC |
| 通信 | WebSocket、JSON-RPC 2.0 | 前后端双向调用 |
| AI | Function-call Agent、LiteLLM兼容层 | 模型与结构化工具选择 |
| 发布 | electron-vite、electron-builder、NSIS | 构建和Windows安装包 |

```text
用户自然语言
    ↓
React 对话与地图界面
    ↓ WebSocket / JSON-RPC
Python Agent Sidecar
  ├─ 上下文与记忆
  ├─ Function-call循环
  ├─ 文件/脚本/地图/报告工具
  ├─ Python执行进程
  └─ Operation / Workflow / Worker
    ↓ 反向RPC
MapLibre图层、样式、视角、标签与成果
```

Electron 管理桌面生命周期和 Python Sidecar；React 负责界面与地图状态；Python 负责重计算和 Agent 推理。Python 不直接持有 MapLibre 对象，而通过 `rpc.ui.map.*` 让前端更新地图，实现计算与渲染解耦。

### 3.2 Agent机制

模型根据工具 schema 返回结构化 function call；Tool Runtime 完成参数校验、权限判断、执行、结果归一化与归档。Python 代码仍可执行，但只是工具之一，不再依靠解析回复代码块控制整个循环。

一次典型流程为：接收自然语言 → 检查数据字段与坐标 → 清洗/转换 GeoJSON → 添加图层 → 构建样式与标签 → 缩放定位 → 解释结果 → 将工具、脚本和产物写入 RunArchive。

系统区分：Tool（原子函数）、Operation（可复用算法）、Workflow（DAG多步骤编排）、Worker（常驻后台进程）与 Skill（项目知识/流程包），使临时探索能够逐步沉淀为稳定能力。

## 4. 从零开始的实现流程

### 4.1 环境和依赖

项目源代码仓库位于：`https://github.com/Elvira-tang/GeoVela`。本地 Git 的 `origin` 也指向该地址。GeoVela 的品牌、GIS 案例、三维功能和 Agent 自优化实验均在该仓库中继续开发。

```powershell
node --version
npm --version
python --version
git --version

git clone https://github.com/Elvira-tang/GeoVela.git
Set-Location GeoVela
npm install
npm run setup:python
npm run dev:electron
```

项目文档要求 Python 3.11+。实测使用 Python 3.14 时要额外确认 GIS 依赖是否提供兼容轮子。若出现 `No module named 'mcp'`，说明 GeoVela 实际启动的 Python 与安装依赖的解释器可能不同；应先确认解释器路径，再在同一环境安装。MCP 是模型上下文协议，并非 CSV 显示本身的必要条件。

### 4.2 前端实现

界面由三部分构成：左侧文件/图层/画布/Worker/Operation/Workflow/运行记录/设置；中央地图、代码、Markdown、数据透视和制图画布；右侧 Agent 对话、工具状态、代码和结果。底部显示坐标系、图层/要素数量与 Python 状态。

MapEngine 负责图层注册、渲染器选择、视角控制、要素识别与导出。CSV 加载流程为：识别编码和字段 → 自动判断经纬度或 WKT → 转换 GeoJSON → 判断几何类型 → 选择 circle/line/fill/symbol/categorized/graduated/cluster/extrusion → 加载 MapLibre → 缩放至范围。

### 4.3 Python与RPC实现

Python Sidecar 提供 WebSocket JSON-RPC 服务、Agent循环、工具注册、Python子进程、Operation、Workflow、Worker及运行归档。Renderer→Python 用于聊天、脚本与运行管理；Python→Renderer 用于添加图层、更新样式、动态数据与交互询问。地图事实以前端 store 为准，计算事实由 Python 输出。

下面以“让用户说一句话，Agent 读取数据并把结果显示到地图”为最小目标，说明如何从已有 GeoVela 仓库逐步理解和实现 Agent。这里的“从零”指从零基础认识并搭建这条功能链；项目现有代码已实现这些模块，不需要重新编写一套框架。建议先跑通现有程序，再沿调用顺序阅读和修改。每完成一步都先验证，再进入下一步。

#### 4.3.1 先认识五个基本概念

| 名词 | 零基础解释 | GeoVela 中的对应物 |
|---|---|---|
| 模型（LLM） | 根据用户的话决定下一步要说什么、调用什么函数；模型本身不能直接操作本机地图 | `agent/llm.py` 接入模型服务 |
| Agent | 把“提问模型—执行工具—把结果交回模型”组织成多轮过程的程序 | `agent/loop/agent_loop.py` |
| Tool（工具） | 预先写好的普通函数，给模型一个名称、用途和参数说明后才能被选择 | `tools/builtin/`、`tools/registry.py` |
| Workspace（工作区） | 本次任务允许使用的项目文件夹，数据、脚本和结果存放于此 | 打开的项目目录及其 `.opengis/` 子目录 |
| RPC | 两个进程互发的结构化消息；例如 Python 请求前端“新增图层” | `rpc/handler.py`、`src/services/pythonClient.ts` |

可把一次请求理解为：**用户提出目标 → Agent 询问模型 → 模型选择工具并给出参数 → GeoVela 校验并执行 → 工具结果交回模型 → 模型继续或给出最终答复**。模型决定“做什么”，工具代码负责“实际做”，前端地图负责“显示什么”。如果模型只返回一段 Python 代码文本，GeoVela 不会把这段文本自动当作命令执行；代码执行必须走明确的工具调用。

#### 4.3.2 先把运行环境接通

在 Windows PowerShell 中进入仓库目录，依次执行 4.1 的安装和启动命令。`npm install` 安装前端与 Electron 依赖；`npm run setup:python` 创建 Python 虚拟环境，并按 `python-backend/pyproject.toml` 安装后端及 GIS 库；`npm run dev:electron` 启动桌面窗口和 Python Sidecar。Windows 下虚拟环境通常在 `%APPDATA%/opengis/venv`，不在仓库内，这解释了为什么直接运行系统 Python 可能报缺包。

**验收**：桌面窗口出现，底部 Python 状态为 ready；在 Settings / Model 填入自己有权使用的模型 Provider、Base URL、Model Name 和 API Key，点击 Test Connection，再发送“你好”。若只要查看地图，可先不配置模型；要验证 Agent 则必须有可用的模型连接。不要把 API Key 写入报告、脚本或版本库。

#### 4.3.3 打开一个工作区，并沿消息链找到入口

通过 File / Open Workspace 选一个测试文件夹，把少量 CSV 或 GeoJSON 放进去。聊天输入框位于 `src/features/chat/ChatView.tsx`；发送动作进入 `src/stores/chatStore.ts`，其中 `pythonClient.send('chat.user_message', ...)` 会带上文字、会话 ID 和工作区路径。`src/services/pythonClient.ts` 经 WebSocket 发出 JSON-RPC 请求，Python 的 `rpc/handler.py` 接收 `chat.user_message`，建立本轮 Agent 运行。会话 ID 让连续提问共用上下文；工作区路径限定本轮读取数据和保存结果的位置。

**验收**：发送“列出工作区中的文件”后，对话区能看到回复或工具活动；若提示后端未连接，先检查 Python ready 与虚拟环境，再排查模型设置。这里不要急着添加 GIS 算法，先让纯文本问答和文件读取稳定运行。

#### 4.3.4 给 Agent 装配模型、配置和工具

`agent/governance/profile.py` 中的 `AgentProfile.gis_build()` 是默认配置，规定工具组、权限级别和运行预算；`agent/agent_factory.py` 的 `build_agent_loop(...)` 将模型调用、工具表、工作区上下文与执行器组装成一轮 Agent；`agent/factory_common.py` 负责按 Profile 过滤工具，并将工具说明转换成模型能识别的 function-call schema。工具说明不仅告诉模型“有这个函数”，还规定函数名、参数类型和必填项。`AgentProfile` 是配置，不是另一个模型。

初学者先保持默认 `gis-build` 配置，确认 `core` 工具组可见。若模型回答“我不能访问地图/文件”，应检查工具是否注册、是否属于当前 Profile 的工具组，而不是只改提示词。具体新增工具流程另见 `docs/adding-a-new-tool.md`。

#### 4.3.5 从一个只读工具练习 function call

最小练习是在 `python-backend/opengis_backend/tools/builtin/` 增加一个只读函数，例如返回 CSV 的数据行数：读取表头后逐行计数，返回 `{"row_count": 234}` 一类结构化结果。文件中用 `@tool` 装饰器声明唯一名称、用途、参数、返回值和 `group="core"`；函数参数必须与声明一致。`tools/registry.py` 启动时自动发现 `builtin/` 中的模块，不需要手工解析模型回复。若工具涉及文件、地图等副作用，还应在 `agent/execution/tool_capabilities.py` 声明能力和副作用，并按实际操作设置权限。

例如在 `tools/builtin/count_csv_rows_tool.py` 中写入以下最小示例（路径相对于 `python-backend/opengis_backend/`）：

```python
import csv
from pathlib import Path

from opengis_backend.tools.context import ToolContext
from opengis_backend.tools.registry import tool


@tool(
    name="count_csv_rows",
    display_name="Count CSV Rows",
    description="Count data rows in a CSV file in the current workspace.",
    category="statistics",
    params=[{"name": "relative_path", "type": "string", "description": "CSV path relative to workspace"}],
    returns="dict containing row_count (integer)",
    needs_context=True,
    group="core",
)
def count_csv_rows(ctx: ToolContext, relative_path: str) -> dict:
    root = Path(ctx.meta["workspace_path"]).resolve()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() != ".csv":
        raise ValueError("Choose a CSV file inside the workspace")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return {"row_count": sum(1 for _ in csv.DictReader(stream))}
```

这里 `relative_path` 是模型填写的参数，`ctx.meta["workspace_path"]` 由 GeoVela 在本轮运行时注入；路径检查阻止读取工作区外的文件。`utf-8-sig` 可兼容带 BOM 的 UTF-8 CSV，`DictReader` 先读取表头，因此返回值只统计数据行。保存文件后重启开发程序，让工具自动发现重新加载；在工作区放入 `sample.csv`，向 Agent 发送“调用 count_csv_rows 统计 sample.csv 的数据行数”，应在工具结果里看到 `row_count`。如果工作区尚未打开，先完成 4.3.3，否则此示例没有工作区路径可用。

初学时可先阅读已有 `tools/builtin/read_file_tool.py` 和 `tools/builtin/display.py`，照其结构理解：**schema 是给模型看的函数说明，函数体是电脑实际执行的代码，Tool Runtime 是中间的校验与执行入口**。让 Agent 回答“这个 CSV 有多少条数据”，并与表格软件显示的行数比较；同时检查是否把表头误算作数据行。不要让模型自己猜行数。

#### 4.3.6 看懂 Agent 循环，而不是只看最终回复

模型一次回答可以是普通文字，也可以包含结构化 tool call。`agent/loop/agent_loop.py` 将调用交给 `agent/loop/loop_kernel.py` 和 `agent/execution/tool_runtime.py`：解析参数、检查权限、执行工具、收集结果，再把结果追加到上下文供模型下一轮判断。模型不再调用工具、达到预算或用户取消时，本轮结束。可用以下**教学伪代码**记忆流程，它不是仓库中可直接运行的完整源码：

```text
messages = [用户任务]
重复，直到结束或达到预算：
    reply = 模型(messages, 可用工具的 schema)
    如果 reply 是最终文字：返回给用户
    对 reply 中的每个 tool call：
        校验参数和权限
        result = 执行已注册的工具
        把工具结果加入 messages，并记录到运行归档
```

**验收**：对话中能看到“工具开始→工具结果→最终解释”的顺序。工具出错时应显示具体错误，让 Agent 决定是否修正参数或报告失败；不能把工具报错当作任务成功。

#### 4.3.7 把 GIS 结果真正送到地图

GIS 计算输出通常是带坐标和属性的 GeoJSON。坐标应先核对坐标系；经纬度数据通常是 EPSG:4326，GeoJSON 点坐标顺序为 `[经度, 纬度]`。已有 `tools/builtin/display.py` 提供地图相关工具，其新增图层请求通过 `rpc.ui.map.add_layer_from_geojson` 发回前端；`src/services/rpc/handlers/map/` 接收请求，`src/features/map/engine/MapEngine.ts` 负责实际渲染。Python 不直接修改 MapLibre 对象。添加后再用 `list_layers` 读取前端真实图层状态，核对图层是否出现、要素数与可见性，而不是只凭“工具调用成功”判断地图已正确显示。

一个适合入门的练习是：在工作区放一份含 `longitude`、`latitude`、`name` 的小 CSV，请 Agent 识别字段、转换为点 GeoJSON、加到地图并缩放定位。先用 3～5 行手工可核对的数据，确认经纬度没有写反，再换到报告中的校园或 POI 数据。

#### 4.3.8 保存证据、定位失败、完成最小验收

一次 Agent 运行结束后，查看工作区 `.opengis/runs/<run_id>/`；`python-backend/opengis_backend/runs/archive.py` 负责保存工具调用、模型用量、错误和产物等记录。建议按“输入文件→工具参数→工具结果→地图状态→输出文件”顺序检查。常见故障可据此定位：模型无回复先查连接与 Key；`No module named ...` 先查实际启动的虚拟环境；有 GeoJSON 但地图空白先查几何、坐标和图层可见性；任务完成却没有文件则查工作区路径和写入权限。

最小验收标准是：同一份小数据能被读取，Agent 调用过明确工具，地图确实出现正确位置的图层，最终回复与文件/图层一致，运行归档可回看。然后运行 `npm run typecheck`、`npm run test`，并用 GeoVela 虚拟环境执行相关 Python 测试。前端与 Python 测试分别覆盖各自代码，不能互相替代。

#### 4.3.9 在可靠基线之上加入自优化

自优化的第一步不是让 Agent 改写自己的源代码，而是先固定任务和评分规则。`agent/evolution/harness_pro_lite.py` 从默认 `gis-build` 生成 Baseline、Lite、Medium、Heavy 四种 Profile；Baseline 原样保留，其他候选只改运行预算和提示词后缀，继承相同的权限和工具组。`agent/evolution/benchmark.py` 对每个候选运行相同任务，用本地程序核对 `result.json`，并记录通过率、Token、耗时、工具次数和错误数。`select_representatives(...)` 先要求通过率不低于 Baseline，再按“通过率越高越好、平均 Token 越少越好”筛 Pareto 前沿，并选择代表配置。这里的 Token 是成本代理指标，不等于实际账单金额；耗时和错误数会报告，但当前 Pareto 判定没有把它们作为优化目标。

零基础复现时先运行无需调用模型的专项测试；在 PowerShell 中从仓库根目录执行：

```powershell
Set-Location python-backend
& (Join-Path $env:APPDATA 'opengis\venv\Scripts\python.exe') -m unittest discover -s tests -p test_harness_pro_lite.py
Set-Location ..
```

从 `python-backend` 目录运行可确保优先导入当前源码；若从仓库根目录运行而虚拟环境装有旧版包，可能出现找不到 `agent.evolution`。随后阅读 `benchmark.py` 中的任务定义和 `validate_result(...)`，确认真值由数据计算而来。真正运行模型基准需使用本机设置文件、会产生模型调用费用，并可能向所选模型服务发送任务数据；先确认数据使用范围。基准运行后只比较同一模型、同一任务集、相同重复次数和独立工作区的候选结果。对应论文及本项目采用程度见第 11 节与文末参考文献。

### 4.4 三维模式

将 `THREE_D_MODE_AVAILABLE` 设为 `true`，为复选框实现真实 `onChange`：勾选调用 `mapEngine.setPreset3DMode(true)`，取消恢复俯视。三维包含视角倾斜和要素拉伸两部分；只有 pitch/bearing 不会让建筑自动立体，Polygon 还必须用 fill-extrusion 并提供 `height`。

校园95栋建筑中仅1栋含OSM原生层数，其余为按类型估算，因此三维图只能用于教学表达，不能作为测绘成果。

### 4.5 品牌与桌面化

将包名、窗口标题、可执行文件、安装包和文案统一为 GeoVela。Logo 结合地球、空间网络和智能助手形象，采用适合大学生的亲和风格，并替换应用、窗口、安装程序和界面资源。

品牌替换要同步检查 `package.json`、`electron-builder.yml` 的 `productName`、应用ID、README、资源图标、安装目录和GitHub说明，否则仓库名虽为GeoVela，页面仍可能出现OpenGIS。

### 4.6 构建、测试与发布

```powershell
npm run typecheck
npm run test
npm run lint
npm run build
npm run dist:win
```

当前本地已生成 `dist/win-unpacked/GeoVela.exe` 和 `dist/GeoVela-0.2.0-win-x64.exe`。按当前 `electron-builder.yml` 重新打包时，Windows 目标同时包含 NSIS 安装版和 portable 免安装版，文件名应分别带有 `-setup.exe` 和 `-portable.exe`。若日志停在 `output file is locked for writing`，通常是GeoVela、Electron、安装器、资源管理器预览、杀毒或索引程序占用了输出文件。关闭相关进程并确认文件释放后重试。`no signing info identified` 表示未配置代码签名，不影响本地构建，但对外分发会增加SmartScreen提示。

推送前用 `git remote -v` 确认远端为 `https://github.com/Elvira-tang/GeoVela.git`，并避免提交API Key、`node_modules`、虚拟环境、缓存和大体积临时日志。

### 4.7 GitHub版本检查结果

截至2026年11月6日，本报告对应的本地最新版已提交并推送到 `https://github.com/Elvira-tang/GeoVela` 的 `main` 分支。推送内容包括 Agent 自优化实现与评测、真实 GIS 数据和成果、桌面应用改造以及本完整报告。公开前已检查本次新增报告和基准汇总文件，未发现 API Key；基准汇总中的本机绝对工作区路径已改成仓库内相对路径。

源代码同步与安装包发布是两件不同的工作。其他人可以从 `main` 分支获取源代码，但普通用户使用的 Windows 安装版和 portable 版仍应单独上传到 GitHub Releases。后续每次发布可用 `git status --short --branch` 检查本地分支是否与 `origin/main` 同步，并在 Releases 中标注版本号、操作系统、文件校验值和已知限制。

### 4.8 其他用户如何安装和使用桌面程序

#### 4.8.1 普通用户：使用安装包

普通用户不需要安装 Node.js、npm 或 Git。项目维护者应将最新安装包发布到上述 GitHub 仓库的 Releases 页面；如果 Releases 中尚无与源码版本对应的安装包，应由维护者直接提供经过测试的安装文件，并明确安装包的构建日期和对应提交。

Windows 用户的使用流程如下：

1. 下载与系统架构相符的 `GeoVela-<版本>-win-x64-setup.exe`；若不想安装，可下载 `GeoVela-<版本>-win-x64-portable.exe`。当前仓库版本为0.2.0。
2. 双击安装版，选择安装目录并完成安装；portable 版可直接运行。程序尚未配置代码签名时，Windows SmartScreen 可能显示“未知发布者”，用户应先核对文件确实来自项目仓库或项目维护者。
3. 首次启动需要准备 Python 后端。程序会检查 Python 3.11+；若电脑没有合适版本，会尝试下载 Python 3.12.8，再创建用户目录中的虚拟环境并安装 GIS 依赖。此过程需要网络连接、足够磁盘空间，时间取决于网络速度。
4. 等待启动页完成 Python 安装并看到 `Python ready`。如果下载或依赖安装失败，点击重试，并检查网络、代理、杀毒软件和磁盘权限。
5. 打开 Settings / Model，填写自己有权使用的 Provider、Protocol、Base URL、API Key 和 Model Name，再点击 Test Connection。只浏览本地地图时可以不配置模型；使用自然语言 Agent 必须配置可用模型。API Key 只应保存在自己的电脑上，不能发给其他人或提交到 GitHub。
6. 通过 File / Open Workspace 选择一个工作目录，再导入 CSV、GeoJSON、Shapefile、KML 或 GeoTIFF 等数据。建议为每个实验单独建立文件夹，因为运行记录、脚本、Workflow、Operation 和地图状态会保存在该工作区的 `.opengis/` 目录中。
7. 在右侧对话框输入明确任务，例如“读取 `data.csv`，识别经纬度字段，把点显示到地图，并按类别着色”。完成后同时检查地图、对话中的工具结果和 `.opengis/runs/` 运行记录。

卸载桌面程序不会自动等同于删除所有工作区数据。用户自己选择的工程目录、导出的图件和 `.opengis/` 运行记录应在确认无用后另行处理。用户级 Python 环境位于应用数据目录下；如果要彻底清理，应先备份需要的脚本和结果。

#### 4.8.2 开发者：从源码运行

需要修改代码的开发者安装 Node.js 18+、Python 3.11+ 和 Git，然后执行4.1中的克隆、`npm install`、`npm run setup:python` 和 `npm run dev:electron`。开发者源码运行与普通用户安装包是两条不同路径：前者用于调试和二次开发，后者用于直接使用桌面程序。

## 5. 数据来源与统计

所有集中测试数据位于 `Data/`，采集时间为2026年11月5日。除注明外统一为WGS84（EPSG:4326）；高德原始GCJ-02坐标经公开偏移算法转换。

| 数据集 | 规模 | 来源 | 测试目标 |
|---|---:|---|---|
| 全国近7天天气 | 343行，48城市×7天 | Open-Meteo API | 时序汇总、气象符号、未来3天外推 |
| 无锡奶茶POI | 1654家，49个品牌/独立门店 | 高德POI API | 大规模点、品牌/价格分类、报告 |
| 江南大学校园 | 234要素 | OSM Overpass+高德补名 | 点线面、标签、分类、3D |
| 宿舍—地铁—奶茶 | 5500条OD | OSM、高德、本地计算 | 复合网络、可达性、路线、报告 |

### 5.1 天气数据

`Weather7Days_20261105/data/china_weather_last7days.csv` 包含2026-10-30至2026-11-05的温度、降水、降雪、风速、风向、日照和WMO天气代码。Open-Meteo 数据为再分析/网格模型与站点融合结果，并非具体站点原始观测；温度约±1℃，降水为网格估计。

每城只有7条记录，未来3天只能作为统计外推。推荐Holt指数平滑或加权移动平均，不适合用如此少的数据训练LSTM、XGBoost或SARIMA，也不能称为专业数值天气预报。

### 5.2 无锡奶茶POI

按无锡7个区县、通用关键词和27个品牌从高德交叉检索并按POI ID去重，得到1654家。字段涵盖名称、品牌、地址、行政区、商圈、GCJ-02/WGS84坐标、电话、评分、消费和营业时间。高德单查询存在约200条上限，关键词补采只能减少而不能完全消除遗漏；缺失评分/电话不能按0处理。

### 5.3 江南大学校园

校园CSV共234行：建筑95、道路61、体育休闲34、设施26、出入口9、景点3、用地2、节点4。主数据来自OSM Overpass，使用WKT保存点线面；高德POI补齐名称并新增20栋OSM未覆盖建筑。GeoVela将CSV拆成点、线、面和3D建筑图层。11栋小附属建筑无名称，另有浩苑公寓位置需要人工复核。

### 5.4 可达性数据

无锡地铁数据含98站、101条相邻/换乘边、176个出入口，覆盖1、2、3、4和S1号线。步行网络含38885节点、43461边和9.6MB GraphML，范围约31.44–31.56°N、120.22–120.34°E。参数为步行75m/min、进出站各2min、换乘3min、地铁35km/h、宿舍接驳上限2500m。

手写Dijkstra/多源Dijkstra输出：45条宿舍到站记录、5850条站到门店记录和20宿舍×275门店=5500条最优OD结果。

```text
全程 = 宿舍→出入口步行 + 进站2min + 地铁/换乘
     + 出站2min + 出入口→奶茶店步行
```

5500条结果平均59.9min，中位58.8min，范围16.6–143.4min；30/45/60/90min内占比为5.8%/27.4%/52.9%/92.2%。两端步行合计约67%，是主要成本。地铁时间使用直线距离与35km/h估算，未完整包含候车、安检和拥堵。

## 6. GeoVela中的实现效果

### 6.1 天气专题

系统读取城市坐标并汇总七日平均温度、温差、累计降水、最大风速和天气类型，形成全国点图。早期多个同心圆叠加较拥挤，优化后采用连续温度色带、适中点径、雨滴/天气图标、城市标签和按日期独立图层。未来三天分别输出Day1、Day2、Day3，可单独开关并明确标注“统计估计”。

### 6.2 奶茶店POI

1654个点完成加载、定位、属性查询、品牌分类和价格分级。全市尺度使用聚合或小点径，放大后显示单店；不一次显示全部名称，只标注筛选门店或点击弹窗。项目已生成综合图、行政区/品牌统计图和Markdown报告，验证地图到统计报告的闭环。

### 6.3 校园二维/三维

校园数据形成建筑面、道路、设施、出入口等约13个专题图层。二维模式展示轮廓、路网和功能分区；三维模式按高度拉伸建筑。名称通过独立symbol图层显示，并设置白色光晕、偏移与碰撞检测。测试中“点含义不清”和“建筑无名称”分别源于图例缺失、标签字段未映射，后续用分类图例、标签和弹窗改善。

### 6.4 可达性专题

系统成功呈现宿舍、奶茶店、地铁站、换乘站和路线，并生成宿舍汇总、POI分级、TOP5路线与报告。早期线路全红且一次显示约100条，遮挡严重，还出现跨图长直线。优化为：进站步行蓝色虚线、地铁段按线路色的粗实线和白色描边、出站步行橙色虚线；默认每宿舍只显示最优1条，TOP5默认隐藏；宿舍和入选门店显示永久标签；地铁按相邻站序列或真实轨道绘制，不能直接连起终点。

报告结果显示滨湖区包含全部40家Ⅰ级门店；Ⅰ+Ⅱ级共113家，占275家的41.0%。这验证了GeoVela对“网络计算+地图表达+统计解释”的综合能力。

### 6.5 成果沉淀

各工程保存 `.opengis/runs/`、`script/`、`output/`、`assets/plots/` 和报告。用户可回看代码、耗时、工具和错误，并复用CSV、GeoJSON、PNG和Markdown，比一次性聊天结果更适合课程复现和答辩检查。

## 7. 创新点

1. **自然语言与真实地图状态闭环**：Agent不仅生成脚本，还能读取图层状态、执行计算、加图层、改样式并验证结果。
2. **前端渲染与Python计算解耦**：MapLibre留在前端，复杂计算在Python，双向JSON-RPC兼顾交互与生态。
3. **Function-call、权限与归档统一**：schema约束参数，权限、结果压缩、错误反馈和前端展示共用执行通路。
4. **探索向复用演进**：临时代码可沉淀为Operation，多步骤任务成为Workflow，实时任务成为Worker。
5. **多尺度真实数据验证**：全国城市点、城市POI、校园点线面/3D、步行与地铁网络覆盖多种GIS问题。
6. **面向学生的产品设计**：中文自然语言、亲和Logo和即时地图反馈降低门槛，同时保留代码、字段和参数，避免黑箱。

## 8. 测试与评价

| 维度 | 内容 | 标准 |
|---|---|---|
| 安装启动 | 安装包、首次启动、Python | 应用打开，Python ready |
| 文件解析 | CSV/WKT/GeoJSON/Markdown | 中文、字段、几何正确 |
| 地图 | 点线面、缩放、图层、标签 | 位置和样式正确 |
| 3D | 倾斜、拉伸、恢复俯视 | 开关与地图一致 |
| Agent | 理解、工具、异常反馈 | 完成任务并解释 |
| 分析 | 汇总、分类、路径、预测 | 结果可复核、口径明确 |
| 性能 | 1654点、38885节点 | 不因无节制标签而卡顿 |
| 输出 | CSV/GeoJSON/PNG/Markdown | 文件可打开、引用有效 |
| 打包 | build、dist:win | 生成exe和NSIS包 |

已验证四个Data工程均能在GeoVela中加载；校园可拆分点线面与3D；奶茶POI可分类/分级并产出报告；天气可汇总和做实验性三日外推；复合网络可输出5500条OD、汇总和路线；Agent可运行Python、操作地图并归档。

典型问题包括：Python解释器不一致导致缺少mcp；经纬度字段不标准导致识别失败；没有symbol图层便不会显示名称；同色大点/线路造成视觉混乱；直接连起终点产生长直线；大量路线和标签降低性能；输出文件占用导致打包等待；未签名安装包被安全软件重点检查。

## 9. 额外注意事项

### 9.1 数据与坐标

- GCJ-02与WGS84不能混用，否则会偏移；
- 距离/面积不应直接在EPSG:4326上用平面公式；
- CSV建议UTF-8 BOM；原始、处理、输出三层分开；
- 估算高度、速度、换乘时间和预测必须标注来源与方法。

### 9.2 可视化

- 颜色要表达语义；密集点使用聚合、筛选或缩放控制；
- 标签使用光晕、偏移和碰撞避让，只标重要对象；
- 图例必须解释符号、线型、颜色、大小和等级；
- 避免一次绘制5500条OD线，按选择对象动态显示。

### 9.3 算法与结论

- 7天数据不足以训练复杂天气模型；
- Dijkstra结果依赖网络连通性、吸附阈值和边权；
- 35km/h地铁速度不是官方时刻；
- 可达性只代表时间便利，不代表品质、价格和偏好；
- 重复宿舍点、缺失值和停业POI应发布前复核。

### 9.4 软件发布

- Node 24/Python 3.14较新，依赖异常时优先测试项目推荐的LTS组合；
- 对外发布应配置Windows代码签名；
- API Key只保存在环境变量或安全配置；
- `.gitignore`排除密钥、缓存、日志、依赖和临时构建物。

## 10. 可复现工作流

```text
专题名称_日期/
├─ data/
│  ├─ raw/          # 原始数据，不修改
│  └─ processed/    # 清洗、坐标统一、模型输入
├─ script/          # 采集、处理、分析脚本
├─ output/          # CSV、GeoJSON和统计结果
├─ figures/         # 地图与统计图
├─ assets/plots/    # Agent生成图
└─ README.md        # 来源、字段、参数与局限
```

标准过程：定义问题 → 获取数据 → 记录来源 → 检查编码/坐标 → 清洗去重 → 转换空间格式 → 加载GeoVela → 选择算法 → 验证中间结果 → 设置样式 → 输出统计/图件 → 编写局限 → 归档脚本和运行记录。

## 11. 不足与展望

当前不足包括：复杂样式仍需要较详细提示；3D主要是2.5D拉伸；真实时刻、公交、骑行、路况尚未完整接入；大数据图层需进一步分块和瓦片化；模型可能因字段猜测或依赖缺失失败；自动化测试、签名和跨平台发布仍需加强；第三方API存在属性缺失和数量限制。

后续可增加字段映射向导、样式编辑器、矢量瓦片、按视口加载、多模式交通、官方时刻、长期天气序列与滚动验证、3D地形/纹理、数据质量评分、坐标系检测、可视化回归测试、代码签名和自动更新。

### 11.1 Agent Harness 自我改进第一版

项目已实现受控的 HarnessPro-Lite 原型，将 Agent 自我改进限定在声明式 Profile 配置层，不允许候选方案自动改写 Python 执行器、权限逻辑或工具实现。第一版包含以下机制：

本实验的直接参考是 Pan 等人的 HarnessPro 论文 [1]。论文将 harness 定义为管理模型与环境交互的运行层，范围包括提示词、工具与 Skill、上下文与记忆、Hook 和验证规则；它通过多次执行轨迹进行诊断，由专门的分析、规划、编辑与测试生成 Agent 递归修改候选 harness，再以任务通过率和执行成本建立 Pareto 前沿，输出 Lite、Medium 和 Heavy 三种部署模式。GeoVela 采用了其中“性能门槛、性能—成本 Pareto 过滤、归一化加权平方距离选择三档代表方案”的核心思想，但第一版没有实现论文的完整多 Agent 递归编辑和无标签测试生成，因此准确名称为受 HarnessPro 启发的 `HarnessPro-Lite` 原型，而不是论文方法的完整复现。

1. 从 `gis-build` 种子 Profile 产生 Baseline、Lite、Medium 和 Heavy 四类候选；
2. 四类候选继承相同的权限级别和工具组，仅调整模型轮次、代码步数、工具步数、总工作步数和提示词后缀；
3. 按任务聚合正确率、Token、延迟、工具调用数和错误数；
4. 先应用 Baseline 正确率门槛，再删除性能—成本上被支配的候选；
5. 通过归一化加权平方距离，从 Pareto 前沿选出成本优先、平衡和性能优先三种代表 Profile；
6. 提供 JSON 命令行入口，可从真实评测观测数据生成可审计的选择报告。

第一版新增 6 项专项测试，全部通过，覆盖 Profile 安全继承、指标聚合、正确率门槛、Pareto 过滤、三档代表选择、真实数据任务加载和精确结果校验。Python 编译检查、`git diff --check` 和 TypeScript 类型检查通过。当时全量前端测试为 153/155 通过，两项失败为原有 RPC handler 数量期望和栅格 URL 参数校验不一致，与本模块无关。当时全量后端发现 60 项测试，52 项通过；6 项因非 GeoVela 虚拟环境的 Python 3.14 缺少 `litellm` 无法导入，2 项为原有 Memory Harness 断言失败。

### 11.2 真实 GIS 基准与模型评测管线

下一阶段管线已接入三类本地真实数据，每类任务要求 Agent 生成机器可校验的 `result.json`：

| 任务 | 数据规模 | 校验目标 |
|---|---:|---|
| 校园要素汇总 | 234 条 | 总行数及“类别”精确计数 |
| 无锡奶茶 POI 汇总 | 1654 条 | 总行数及“区县”精确计数 |
| 宿舍—地铁—奶茶可达性 | 5500 条 | 总行数及 `total_min` 最小值 |

评分器由本地程序直接从 CSV 计算真值，对 JSON 类型、字段和数值进行精确比较，不使用 LLM 主观判分。每次运行同时从 `.opengis/runs` 归档聚合 Token、墙钟时间、工具调用数和错误数。计划执行 4 个 Profile × 3 个任务，共 12 次真实模型运行。

在获得数据外发授权后，2026 年 11 月 6 日使用 GeoVela 已配置的 `deepseek-flash` 完成 4 个 Profile × 3 个任务，共 12 次真实 Agent 运行。有效运行的实测结果如下：

| Profile | 通过率 | 平均 Token | 平均耗时 | 平均工具调用 | 平均错误 |
|---|---:|---:|---:|---:|---:|
| Baseline | 100% | 47,340 | 8.64 s | 6.00 | 0 |
| Lite | 100% | 45,097 | 7.90 s | 6.00 | 0 |
| Medium | 100% | 51,279 | 9.30 s | 6.67 | 0 |
| Heavy | 100% | 42,749 | 8.00 s | 6.00 | 0 |

第二轮优化审计发现，原实现错误地将优化提示词后缀也添加到 Baseline，使得对照组不再是原始 `gis-build` Profile。该基线污染已修复：Baseline 现在直接保留种子 Profile 的对象、提示词、元数据、权限和工具组，仅 Lite、Medium 和 Heavy 接受优化规则。表中数值为修正后重新执行的 12 次真实运行，已替代受污染的初步结果。

相对修正后的真实 Baseline，Heavy 在保持 100% 通过率的同时，平均 Token 降低 9.7%，平均耗时降低 7.4%，工具调用数保持不变。Lite 的平均 Token 和耗时分别降低 4.7% 和 8.5%。Medium 的成本反而高于 Baseline，说明更大的预算不会自动带来收益。因四个 Profile 的通过率相同且 Heavy 的 Token 最低，修正后的 Pareto 前沿仅包含 Heavy，故当前 Lite、Medium 和 Heavy 三个选择目标都返回 Heavy 候选。这是当前小样本的数据结论，不表示应在所有 GIS 任务上固定使用 Heavy。

首次启动基准时，GeoVela 虚拟环境缺少项目 `pyproject.toml` 已声明的 `mcp` 依赖，12 个任务均在模型调用前失败且 Token 为 0。修复依赖后已覆盖重跑，该基础设施失败不计入上表成绩。本轮仅有三个确定性汇总任务且每个 Profile 只运行一次，可证明优化后的 Profile 在基础任务上能降低开销，但尚不能证明 Heavy 在复杂 GIS 任务上的性能优势。后续应增加坐标系转换、空间连接、网络路径、地图状态验证和故障恢复任务，并进行多次重复运行。完整机器可读结果保存于 `benchmark-results/harness-pro-lite-corrected-20261106/benchmark_report.json`。

### 11.3 复杂 GIS 任务与重复运行评测

为检验第一版在更接近真实 GIS 工作流中的表现，第三轮将基准扩展为五类复杂任务，并对每个 Profile—任务组合独立运行两次：

| 任务 | 核心要求 | 确定性校验 |
|---|---|---|
| 坐标转换 | EPSG:4326 转 EPSG:3857 | 与 `pyproj` 真值比较，坐标精确到 0.001 |
| 空间连接 | 1654 个 POI 与无锡区县多边形连接 | 比较匹配数及各区县精确计数 |
| 网络最短路径 | 43461 条步行边上的无向 Dijkstra | 比较端点、路径距离和节点数 |
| 错误恢复 | 识别缺失、非数字和超范围坐标 | 精确校验 1654 条有效、3 条拒绝 |
| 地图状态 | 必须调用 `list_layers` 读取实时状态 | 模拟前端 RPC，比较图层数、可见数和顺序 |

评测共执行 4 个 Profile × 5 个任务 × 2 次重复，即 40 次真实 `deepseek-flash` Agent 运行。每次重复使用独立工作区和对话 ID，避免上一次生成文件或上下文污染后续结果。

| Profile | 通过数 | 通过率 | 平均 Token | 平均耗时 | 平均工具调用 | 平均错误 |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 8/10 | 80% | 108,068 | 26.96 s | 14.60 | 0.20 |
| Lite | 6/10 | 60% | 43,179 | 10.78 s | 8.00 | 0.00 |
| Medium | 7/10 | 70% | 73,059 | 20.03 s | 11.60 | 0.00 |
| Heavy | 8/10 | 80% | 100,893 | 27.53 s | 14.20 | 0.20 |

复杂基准呈现了基础任务中看不到的性能—成本权衡。Heavy 与 Baseline 同为 80% 通过率，平均 Token 降低 6.6%，平均工具调用降低 2.7%，但平均耗时增加 2.1%。以当前选择器的“正确率 + Token”双目标计算，Heavy 在性能不下降时成本更低，因此成为唯一 Pareto 前沿候选。

Lite 的 Token 和耗时分别比 Baseline 降低 60.0% 和 60.0%，但通过率下降 20 个百分点：空间连接和网络路径均出现一次在写入结果前达到预算边界，错误恢复两次均未完成。Medium 通过率为 70%，平均 Token 降低 32.4%，平均耗时降低 25.7%，但网络路径仍有一次过早收口。这些结果说明对复杂 GIS 任务使用固定低预算会牺牲可靠性，后续应按任务类型或执行轨迹动态提升预算，而不是在 Lite 中使用统一的 10 步上限。

重复运行同样证明单次评测不足以代表稳定性。例如 Baseline 的空间连接两次均通过，但第二次使用的 Token、耗时和工具调用明显高于第一次。网络任务也存在类似方差。因此后续正式评测应至少运行三次并报告标准差。

#### 错误恢复契约的定向优化

40 次评测中，四个 Profile 在错误恢复任务上均能算出 1654 条有效和 3 条拒绝，但 Baseline、Medium 和 Heavy 会在 `result.json` 中追加数千条明细、来源路径和诊断元数据，因而不符合精确 schema；Lite 则常在写入前达到预算上限。针对该失败完成两项优化：

1. 在进化提示词中增加“用户指定精确 schema 时只输出要求的键，禁止附加数组、诊断和元数据”；
2. 将任务契约明确为仅允许 `valid_rows` 和 `rejected_rows` 两个整数键。

定向复测共执行 4 个 Profile × 2 次重复，结果如下：

| Profile | 优化前 | 优化后 | 平均 Token | 平均耗时 |
|---|---:|---:|---:|---:|
| Baseline | 0/2 | 2/2 | 87,053 | 26.13 s |
| Lite | 0/2 | 1/2 | 47,230 | 12.49 s |
| Medium | 0/2 | 2/2 | 90,973 | 20.04 s |
| Heavy | 0/2 | 2/2 | 156,076 | 37.88 s |

Baseline 同样从 0/2 提升到 2/2，说明主要改进来自更严格、无歧义的任务契约，不能将全部收益归因于 Harness 提示词。Medium 在保持 2/2 的前提下比 Heavy 减少 41.7% Token 和 47.1% 耗时；Lite 仍有一次未能写入结果，进一步证明其固定低预算不适合错误恢复。

复杂基准的完整结果保存于 `benchmark-results/harness-pro-complex-r2b-20261106/benchmark_report.json`，错误恢复定向复测保存于 `benchmark-results/harness-pro-error-recovery-r2-20261106/benchmark_report.json`。

### 11.4 HarnessPro论文与GeoVela实现的对应关系

| HarnessPro论文 [1] | GeoVela当前实现 | 差异与限制 |
|---|---|---|
| 从基础 harness 开始，按 epoch 递归改进 | 从 `gis-build` 生成一次固定候选集 | 尚未让入选候选进入下一 epoch 自动继续演化 |
| 多次 rollout 后由 Trajectory Analyzer 诊断失败与冗余 | 保存工具、错误、Token 和耗时，并人工审计失败轨迹 | 没有独立的自动轨迹分析 Agent |
| Planner 按不同性能—成本目标提出修改计划，Editor 修改完整 harness | 预先设置 Lite、Medium、Heavy 的预算和统一提示词后缀 | 不自动改写 Tool、Skill、Hook、记忆或执行器源代码 |
| Test Synthesizer 在无官方测试条件下生成固定测试 | 从真实 GIS 数据直接计算确定性真值并精确核对 `result.json` | GeoVela 不是论文的 label-free 设置，但评分更容易复核 |
| 成本使用不同类别 Token 的实际价格计算 | 使用总 Token 作为 provider-neutral 成本代理 | 不能直接解释为真实金额；不同模型价格不可由 Token 数直接横比 |
| 通过率低于初始 harness 的候选被淘汰，再删除 Pareto-dominated 候选 | 以 Baseline 通过率为门槛，对通过率和平均 Token 做 Pareto 过滤 | 这一核心选择逻辑与论文方向一致 |
| 用归一化加权平方距离选择 Lite、Medium、Heavy | 使用性能权重0.05、0.5和0.95选择三类代表 Profile | 小样本前沿只有一个候选时，三种模式可能返回同一 Profile |
| 在独立训练、验证、测试集合上报告多基准结果 | 当前使用基础与复杂 GIS 任务，并进行有限重复运行 | 尚未形成严格的数据集划分和论文规模的跨基准实验 |

因此，本报告不能声称“完整实现了 HarnessPro”。更准确的结论是：GeoVela 依据 HarnessPro [1] 实现了一个安全、可审计的 GIS 场景简化原型，并通过真实数据检验性能—成本权衡。11.2—11.3 的表格和 `benchmark_report.json` 是本项目实验结果，不能用论文结果替代；任务集、模型或评分规则变化后，应重新建立 Baseline 并复测全部候选。

## 12. 结论

GeoVela 完成了从开源GIS原型到具有独立名称、Logo、Windows安装包、三维能力和真实案例的桌面应用改造。Electron/React提供桌面与交互，MapLibre负责空间渲染，Python/Agent负责数据处理与分析，JSON-RPC将模型决策转化为可见、可检查的地图操作。

四组数据证明，GeoVela不仅能“把CSV显示在地图上”，还能够处理多类型几何、专题样式、标签、3D建筑、时序统计、POI分析和多网络可达性，并将结果沉淀为脚本、GeoJSON、图表和报告。项目最有价值之处是连接自然语言、空间计算、地图状态与运行归档，使学生以较低门槛完成完整GIS工作流，同时保留数据来源、字段、算法、参数和局限。

## 参考文献（Agent自优化实验）

[1] Pan Z, Feng Z, Cen Y, et al. HarnessPro: Recursive Harness Self-Improvement with Pareto Optimization for Performance-Cost Trade-offs[EB/OL]. arXiv:2610.26770v2, 2026-10-20. https://arxiv.org/abs/2610.26770

> 本实验的自优化候选生成、性能门槛、Pareto 过滤以及 Lite/Medium/Heavy 代表方案选择，直接参考文献 [1]。报告中不再用一般性的 Agent 或提示词优化论文替代本实验的直接方法来源。

## 附录A：常用命令

```powershell
npm install
npm run setup:python
npm run dev:electron
npm run typecheck
npm run test
npm run lint
npm run build
npm run dist:win
```

## 附录B：主要目录

| 路径 | 内容 |
|---|---|
| `electron/` | Electron主进程、IPC与生命周期 |
| `src/` | React界面、MapEngine、渲染器、状态、RPC |
| `python-backend/opengis_backend/` | Agent、Tool、Operation、Workflow、Worker |
| `resources/` | 图标与应用资源 |
| `Data/Weather7Days_20261105/` | 天气与预测成果 |
| `Data/MilkTea_Wuxi_20261105/` | 奶茶POI与空间分析 |
| `Data/CampusMap_Jiangnan_20261105/` | 校园二维/三维成果 |
| `Data/Dorm_MilkTea_Metro_Accessibility_20261105/` | 网络、可达性与专题报告 |
| `Data/数据集来源说明.md` | 统一来源、字段与局限 |

## 附录C：答辩展示建议

建议5—8分钟按以下顺序：主界面与品牌 → 自然语言加载校园CSV → 二维/三维切换与建筑标签 → 奶茶POI聚合/分类 → 宿舍地铁奶茶可达性 → 自动生成图表/报告 → 说明来源、估算参数和局限。重点突出“自然语言驱动真实地图”“Python计算与前端地图双向联动”“四类真实数据验证”“运行过程可追踪”。
