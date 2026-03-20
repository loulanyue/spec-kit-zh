<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>🌱 Spec Kit ZH</h1>
    <h3><em>更快地构建高质量软件。</em></h3>
</div>

<p align="center">
    <strong>一个开源工具包，让你专注于产品场景与可预期的结果，而不是从零开始凭感觉拼凑每一个实现细节。</strong>
</p>

<p align="center">
    <a href="https://github.com/loulanyue/spec-kit-zh/actions/workflows/release.yml"><img src="https://github.com/loulanyue/spec-kit-zh/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/loulanyue/spec-kit-zh/stargazers"><img src="https://img.shields.io/github/stars/loulanyue/spec-kit-zh?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/loulanyue/spec-kit-zh/blob/main/LICENSE"><img src="https://img.shields.io/github/license/loulanyue/spec-kit-zh" alt="License"/></a>
    <a href="https://github.com/loulanyue/spec-kit-zh/tree/main/docs"><img src="https://img.shields.io/badge/docs-Repository-blue" alt="Documentation"/></a>
</p>

---

## 目录

- [🤔 什么是规范驱动开发？](#-什么是规范驱动开发)
- [⚡ 快速开始](#-快速开始)
- [📽️ 视频概览](#️-视频概览)
- [🚶 社区演练项目](#-社区演练项目)
- [🤖 支持的 AI 代理](#-支持的-ai-代理)
- [🔧 specify-zh 命令参考](#-specify-zh-命令参考)
- [📚 核心理念](#-核心理念)
- [🌟 开发阶段](#-开发阶段)
- [🎯 实验目标](#-实验目标)
- [🔧 前置要求](#-前置要求)
- [📖 延伸阅读](#-延伸阅读)
- [📋 详细流程](#-详细流程)
- [🔍 故障排除](#-故障排除)
- [💬 支持](#-支持)
- [🙏 致谢](#-致谢)
- [📄 许可证](#-许可证)

## 🤔 什么是规范驱动开发？

规范驱动开发（Spec-Driven Development）**重新定义**了软件开发的起点。过去几十年里，代码一直是开发过程中的主角，而规范常常只是编码开始前临时搭起来的脚手架。规范驱动开发改变了这一点：**规范本身变得可执行**，它不再只是指导实现，而是可以直接驱动计划、任务拆解与最终实现。

## ⚡ 快速开始

### 1. 安装 `specify-cli-zh`

请选择你偏好的安装方式：

#### 方式 1：持久化安装（推荐）

安装一次，全局可用：

```bash
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
```

安装完成后即可直接使用：

```bash
# 创建新项目
specify-zh init <PROJECT_NAME>

# 或在现有项目中初始化
specify-zh init . --ai claude
# 或者
specify-zh init --here --ai claude

# 检查本机工具环境
specify-zh check
```

`specify-cli-zh` 默认安装的命令名是 `specify-zh`，这样可以避免与其他已安装的 `specify` 命令冲突。

升级 Specify 请参阅 [升级指南](./docs/upgrade.md)。快速升级命令如下：

```bash
uv tool install specify-cli-zh --force --from git+https://github.com/loulanyue/spec-kit-zh.git
```

#### 方式 2：一次性使用

无需安装，直接运行：

```bash
# 创建新项目
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init <PROJECT_NAME>

# 或在现有项目中初始化
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init . --ai claude
# 或者
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init --here --ai claude
```

**持久化安装的优势：**

- 工具会保留在 PATH 中，随时可用
- 不需要额外维护 shell 别名
- 可以使用 `uv tool list`、`uv tool upgrade`、`uv tool uninstall` 做更完整的工具管理
- shell 配置更简洁

### 2. 建立项目原则

在项目目录中启动你的 AI 助手。初始化完成后，助手中就会提供 `/speckit.*` 命令。

使用 **`/speckit.constitution`** 创建项目的治理原则与开发准则，它们会贯穿后续所有规范、计划与实现阶段。

```bash
/speckit.constitution 创建强调代码质量、测试标准、用户体验一致性与性能要求的项目原则
```

### 3. 创建规格说明

使用 **`/speckit.specify`** 描述你要构建什么。此阶段应重点说明**做什么**与**为什么做**，而不是技术栈。

```bash
/speckit.specify 构建一个帮助我管理照片相册的应用。相册按日期分组，可在主页拖拽重排；相册之间不允许嵌套；每个相册中的照片以平铺预览方式展示。
```

### 4. 创建技术实施计划

使用 **`/speckit.plan`** 补充技术栈与架构选择。

```bash
/speckit.plan 应用使用 Vite，并尽量减少外部依赖。优先使用原生 HTML、CSS 与 JavaScript。图片不上传到远端，元数据保存在本地 SQLite 数据库中。
```

### 5. 分解任务

使用 **`/speckit.tasks`** 将实施计划转成可执行的任务清单。

```bash
/speckit.tasks
```

### 6. 执行实现

使用 **`/speckit.implement`** 按计划执行任务并完成功能实现。

```bash
/speckit.implement
```

如需查看完整分步说明，请阅读 [Spec-Driven Development 全流程指南](./spec-driven.md)。

## 📽️ 视频概览

想快速了解 Spec Kit 的工作方式？可以先看这个[视频概览](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)：

[![Spec Kit video header](/media/spec-kit-video-header.jpg)](https://www.youtube.com/watch?v=a9eR1xsfvHg&pp=0gcJCckJAYcqIYzv)

## 🚶 社区演练项目

下面这些社区项目展示了规范驱动开发在不同场景中的实际用法：

- **[Greenfield .NET CLI tool](https://github.com/mnriem/spec-kit-dotnet-cli-demo)**：从空目录出发，构建一个 .NET 单文件时区工具 CLI，完整覆盖 constitution、specify、plan、tasks 以及多轮 implement 流程。

- **[Greenfield Spring Boot + React platform](https://github.com/mnriem/spec-kit-spring-react-demo)**：从零构建一个 LLM 性能分析平台，包含 REST API、图表、迭代跟踪，并演示 clarify 和跨文档一致性分析流程。

- **[Brownfield ASP.NET CMS extension](https://github.com/mnriem/spec-kit-aspnet-brownfield-demo)**：在已有 ASP.NET CMS 项目中追加两个功能，展示 spec-kit 如何适配已有代码库，而不要求项目一开始就有现成规范或 constitution。

## 🤖 支持的 AI 代理

| 代理                                                                                 | 支持情况 | 说明                                                                                                                                        |
| ------------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Kiro CLI](https://kiro.dev/docs/cli/)                                               | ✅      | 使用 `--ai kiro-cli`，别名为 `--ai kiro`                                                                                                   |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | 基于 IDE 的 agent，支持 slash commands                                                                                                     |
| [Jules](https://jules.google.com/)                                                   | ✅      |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Tabnine CLI](https://docs.tabnine.com/main/getting-started/tabnine-cli)             | ✅      |                                                                                                                                           |
| [Mistral Vibe](https://github.com/mistralai/mistral-vibe)                            | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |
| [Antigravity (agy)](https://antigravity.google/)                                     | ✅      |                                                                                                                                           |
| Generic                                                                              | ✅      | 自定义代理接入方式。对未内置支持的代理，可通过 `--ai generic --ai-commands-dir <path>` 注入命令模板                                       |

## 🔧 specify-zh 命令参考

`specify-zh` 命令支持以下能力与参数：

### 命令

| 命令 | 说明 |
| ---- | ---- |
| `init`  | 使用最新模板初始化一个新的 Specify 项目 |
| `check` | 检查本机是否安装所需工具（如 `git`、`claude`、`gemini`、`cursor-agent`、`codex`、`kiro-cli`、`qodercli`、`vibe` 等） |

### `specify-zh init` 参数与选项

| 参数/选项        | 类型     | 说明 |
| ---------------- | -------- | ---- |
| `<project-name>` | 参数     | 新项目目录名（使用 `--here` 时可省略，也可以用 `.` 表示当前目录） |
| `--ai` | 选项 | 要接入的 AI 助手：`claude`、`gemini`、`copilot`、`cursor-agent`、`qwen`、`opencode`、`codex`、`windsurf`、`kilocode`、`auggie`、`roo`、`codebuddy`、`amp`、`shai`、`kiro-cli`（别名 `kiro`）、`agy`、`bob`、`qodercli`、`vibe` 或 `generic` |
| `--ai-commands-dir` | 选项 | 代理命令文件目录（与 `--ai generic` 配合使用，例如 `.myagent/commands/`） |
| `--script` | 选项 | 使用脚本类型：`sh`（bash/zsh）或 `ps`（PowerShell） |
| `--ignore-agent-tools` | 标志 | 跳过对 Claude Code 等 AI 工具的检查 |
| `--no-git` | 标志 | 跳过 git 仓库初始化 |
| `--here` | 标志 | 直接在当前目录初始化，而不是新建目录 |
| `--force` | 标志 | 当前目录非空时强制合并/覆盖并跳过确认 |
| `--skip-tls` | 标志 | 跳过 SSL/TLS 校验（不推荐） |
| `--debug` | 标志 | 开启详细调试输出，便于排查问题 |
| `--github-token` | 选项 | 用于 GitHub API 请求的令牌（也可通过 `GH_TOKEN` / `GITHUB_TOKEN` 环境变量传入） |
| `--ai-skills` | 标志 | 将 Prompt.MD 模板安装到代理专属的 `skills/` 目录中（需要配合 `--ai`） |

### 示例

```bash
# 基础项目初始化
specify-zh init my-project

# 指定 AI 助手初始化
specify-zh init my-project --ai claude

# 使用 Cursor 初始化
specify-zh init my-project --ai cursor-agent

# 使用 Qoder 初始化
specify-zh init my-project --ai qodercli

# 使用 Windsurf 初始化
specify-zh init my-project --ai windsurf

# 使用 Kiro CLI 初始化
specify-zh init my-project --ai kiro-cli

# 使用 Amp 初始化
specify-zh init my-project --ai amp

# 使用 SHAI 初始化
specify-zh init my-project --ai shai

# 使用 Mistral Vibe 初始化
specify-zh init my-project --ai vibe

# 使用 IBM Bob 初始化
specify-zh init my-project --ai bob

# 使用 Antigravity 初始化
specify-zh init my-project --ai agy

# 初始化未内置支持的代理（generic / bring your own agent）
specify-zh init my-project --ai generic --ai-commands-dir .myagent/commands/

# 强制使用 PowerShell 脚本
specify-zh init my-project --ai copilot --script ps

# 在当前目录初始化
specify-zh init . --ai copilot
# 或者使用 --here
specify-zh init --here --ai copilot

# Force merge into current (non-empty) directory without confirmation
specify-zh init . --force --ai copilot
# or
specify-zh init --here --force --ai copilot

# Skip git initialization
specify-zh init my-project --ai gemini --no-git

# Enable debug output for troubleshooting
specify-zh init my-project --ai claude --debug

# Use GitHub token for API requests (helpful for corporate environments)
specify-zh init my-project --ai claude --github-token ghp_your_token_here

# Install agent skills with the project
specify-zh init my-project --ai claude --ai-skills

# Initialize in current directory with agent skills
specify-zh init --here --ai gemini --ai-skills

# Check system requirements
specify-zh check
```

### Available Slash Commands

After running `specify-zh init`, your AI coding agent will have access to these slash commands for structured development:

#### Core Commands

Essential commands for the Spec-Driven Development workflow:

| Command                 | Description                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| `/speckit.constitution` | Create or update project governing principles and development guidelines |
| `/speckit.specify`      | Define what you want to build (requirements and user stories)            |
| `/speckit.plan`         | Create technical implementation plans with your chosen tech stack        |
| `/speckit.tasks`        | Generate actionable task lists for implementation                        |
| `/speckit.implement`    | Execute all tasks to build the feature according to the plan             |

#### Optional Commands

Additional commands for enhanced quality and validation:

| Command              | Description                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `/speckit.clarify`   | Clarify underspecified areas (recommended before `/speckit.plan`; formerly `/quizme`)                                                |
| `/speckit.analyze`   | Cross-artifact consistency & coverage analysis (run after `/speckit.tasks`, before `/speckit.implement`)                             |
| `/speckit.checklist` | Generate custom quality checklists that validate requirements completeness, clarity, and consistency (like "unit tests for English") |

### Environment Variables

| Variable          | Description                                                                                                                                                                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SPECIFY_FEATURE` | Override feature detection for non-Git repositories. Set to the feature directory name (e.g., `001-photo-albums`) to work on a specific feature when not using Git branches.<br/>\*\*Must be set in the context of the agent you're working with prior to using `/speckit.plan` or follow-up commands. |

## 📚 Core Philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "*what*" before the "*how*"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## 🌟 Development Phases

| Phase                                    | Focus                    | Key Activities                                                                                                                                                     |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **0-to-1 Development** ("Greenfield")    | Generate from scratch    | <ul><li>Start with high-level requirements</li><li>Generate specifications</li><li>Plan implementation steps</li><li>Build production-ready applications</li></ul> |
| **Creative Exploration**                 | Parallel implementations | <ul><li>Explore diverse solutions</li><li>Support multiple technology stacks & architectures</li><li>Experiment with UX patterns</li></ul>                         |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively</li><li>Modernize legacy systems</li><li>Adapt processes</li></ul>                                                                |

## 🎯 Experimental Goals

Our research and experimentation focus on:

### Technology independence

- Create applications using diverse technology stacks
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-centric development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & iterative processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- [Supported](#-supported-ai-agents) AI coding agent.
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter issues with an agent, please open an issue so we can refine the integration.

## 📖 Learn More

- **[Complete Spec-Driven Development Methodology](./spec-driven.md)** - Deep dive into the full process
- **[Detailed Walkthrough](#-detailed-process)** - Step-by-step implementation guide

---

## 📋 Detailed Process

<details>
<summary>Click to expand the detailed step-by-step walkthrough</summary>

You can use the `specify-cli-zh` distribution through the `specify-zh` command to bootstrap your project. Run:

```bash
specify-zh init <project_name>
```

Or initialize in the current directory:

```bash
specify-zh init .
# or use the --here flag
specify-zh init --here
# Skip confirmation when the directory already has files
specify-zh init . --force
# or
specify-zh init --here --force
```

![specify-zh bootstrapping a new project in the terminal](./media/specify_cli.gif)

You will be prompted to select the AI agent you are using. You can also proactively specify it directly in the terminal:

```bash
specify-zh init <project_name> --ai claude
specify-zh init <project_name> --ai gemini
specify-zh init <project_name> --ai copilot

# Or in current directory:
specify-zh init . --ai claude
specify-zh init . --ai codex

# or use --here flag
specify-zh init --here --ai claude
specify-zh init --here --ai codex

# Force merge into a non-empty current directory
specify-zh init . --force --ai claude

# or
specify-zh init --here --force --ai claude
```

The `specify-zh` command will check if you have Claude Code, Gemini CLI, Cursor CLI, Qwen CLI, opencode, Codex CLI, Qoder CLI, Tabnine CLI, Kiro CLI, or Mistral Vibe installed. If you do not, or you prefer to get the templates without checking for the right tools, use `--ignore-agent-tools` with your command:

```bash
specify-zh init <project_name> --ai claude --ignore-agent-tools
```

### **STEP 1:** Establish project principles

Go to the project folder and run your AI agent. In our example, we're using `claude`.

![Bootstrapping Claude Code environment](./media/bootstrap-claude-code.gif)

You will know that things are configured correctly if you see the `/speckit.constitution`, `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, and `/speckit.implement` commands available.

The first step should be establishing your project's governing principles using the `/speckit.constitution` command. This helps ensure consistent decision-making throughout all subsequent development phases:

```text
/speckit.constitution Create principles focused on code quality, testing standards, user experience consistency, and performance requirements. Include governance for how these principles should guide technical decisions and implementation choices.
```

This step creates or updates the `.specify/memory/constitution.md` file with your project's foundational guidelines that the AI agent will reference during specification, planning, and implementation phases.

### **STEP 2:** Create project specifications

With your project principles established, you can now create the functional specifications. Use the `/speckit.specify` command and then provide the concrete requirements for the project you want to develop.

> [!IMPORTANT]
> Be as explicit as possible about *what* you are trying to build and *why*. **Do not focus on the tech stack at this point**.

An example prompt:

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up. For each task in the UI for a task card,
you should be able to change the current status of the task between the different columns in the Kanban work board.
You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task
card, assign one of the valid users. When you first launch Taskify, it's going to give you a list of the five users to pick
from. There will be no password required. When you click on a user, you go into the main view, which displays the list of
projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns.
You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are
assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly
see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can
delete any comments that you made, but you can't delete comments anybody else made.
```

After this prompt is entered, you should see Claude Code kick off the planning and spec drafting process. Claude Code will also trigger some of the built-in scripts to set up the repository.

Once this step is completed, you should have a new branch created (e.g., `001-create-taskify`), as well as a new specification in the `specs/001-create-taskify` directory.

The produced specification should contain a set of user stories and functional requirements, as defined in the template.

At this stage, your project folder contents should resemble the following:

```text
└── .specify
    ├── memory
    │  └── constitution.md
    ├── scripts
    │  ├── check-prerequisites.sh
    │  ├── common.sh
    │  ├── create-new-feature.sh
    │  ├── setup-plan.sh
    │  └── update-claude-md.sh
    ├── specs
    │  └── 001-create-taskify
    │      └── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### **STEP 3:** Functional specification clarification (required before planning)

With the baseline specification created, you can go ahead and clarify any of the requirements that were not captured properly within the first shot attempt.

You should run the structured clarification workflow **before** creating a technical plan to reduce rework downstream.

Preferred order:

1. Use `/speckit.clarify` (structured) – sequential, coverage-based questioning that records answers in a Clarifications section.
2. Optionally follow up with ad-hoc free-form refinement if something still feels vague.

If you intentionally want to skip clarification (e.g., spike or exploratory prototype), explicitly state that so the agent doesn't block on missing clarifications.

Example free-form refinement prompt (after `/speckit.clarify` if still needed):

```text
For each sample project or project that you create there should be a variable number of tasks between 5 and 15
tasks for each one randomly distributed into different states of completion. Make sure that there's at least
one task in each stage of completion.
```

You should also ask Claude Code to validate the **Review & Acceptance Checklist**, checking off the things that are validated/pass the requirements, and leave the ones that are not unchecked. The following prompt can be used:

```text
Read the review and acceptance checklist, and check off each item in the checklist if the feature spec meets the criteria. Leave it empty if it does not.
```

It's important to use the interaction with Claude Code as an opportunity to clarify and ask questions around the specification - **do not treat its first attempt as final**.

### **STEP 4:** Generate a plan

You can now be specific about the tech stack and other technical requirements. You can use the `/speckit.plan` command that is built into the project template with a prompt like this:

```text
We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use
Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API,
tasks API, and a notifications API.
```

The output of this step will include a number of implementation detail documents, with your directory tree resembling this:

```text
.
├── CLAUDE.md
├── memory
│  └── constitution.md
├── scripts
│  ├── check-prerequisites.sh
│  ├── common.sh
│  ├── create-new-feature.sh
│  ├── setup-plan.sh
│  └── update-claude-md.sh
├── specs
│  └── 001-create-taskify
│      ├── contracts
│      │  ├── api-spec.json
│      │  └── signalr-spec.md
│      ├── data-model.md
│      ├── plan.md
│      ├── quickstart.md
│      ├── research.md
│      └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

Check the `research.md` document to ensure that the right tech stack is used, based on your instructions. You can ask Claude Code to refine it if any of the components stand out, or even have it check the locally-installed version of the platform/framework you want to use (e.g., .NET).

Additionally, you might want to ask Claude Code to research details about the chosen tech stack if it's something that is rapidly changing (e.g., .NET Aspire, JS frameworks), with a prompt like this:

```text
I want you to go through the implementation plan and implementation details, looking for areas that could
benefit from additional research as .NET Aspire is a rapidly changing library. For those areas that you identify that
require further research, I want you to update the research document with additional details about the specific
versions that we are going to be using in this Taskify application and spawn parallel research tasks to clarify
any details using research from the web.
```

During this process, you might find that Claude Code gets stuck researching the wrong thing - you can help nudge it in the right direction with a prompt like this:

```text
I think we need to break this down into a series of steps. First, identify a list of tasks
that you would need to do during implementation that you're not sure of or would benefit
from further research. Write down a list of those tasks. And then for each one of these tasks,
I want you to spin up a separate research task so that the net results is we are researching
all of those very specific tasks in parallel. What I saw you doing was it looks like you were
researching .NET Aspire in general and I don't think that's gonna do much for us in this case.
That's way too untargeted research. The research needs to help you solve a specific targeted question.
```

> [!NOTE]
> Claude Code might be over-eager and add components that you did not ask for. Ask it to clarify the rationale and the source of the change.

### **STEP 5:** Have Claude Code validate the plan

With the plan in place, you should have Claude Code run through it to make sure that there are no missing pieces. You can use a prompt like this:

```text
Now I want you to go and audit the implementation plan and the implementation detail files.
Read through it with an eye on determining whether or not there is a sequence of tasks that you need
to be doing that are obvious from reading this. Because I don't know if there's enough here. For example,
when I look at the core implementation, it would be useful to reference the appropriate places in the implementation
details where it can find the information as it walks through each step in the core implementation or in the refinement.
```

This helps refine the implementation plan and helps you avoid potential blind spots that Claude Code missed in its planning cycle. Once the initial refinement pass is complete, ask Claude Code to go through the checklist once more before you can get to the implementation.

You can also ask Claude Code (if you have the [GitHub CLI](https://docs.github.com/en/github-cli/github-cli) installed) to go ahead and create a pull request from your current branch to `main` with a detailed description, to make sure that the effort is properly tracked.

> [!NOTE]
> Before you have the agent implement it, it's also worth prompting Claude Code to cross-check the details to see if there are any over-engineered pieces (remember - it can be over-eager). If over-engineered components or decisions exist, you can ask Claude Code to resolve them. Ensure that Claude Code follows the [constitution](base/memory/constitution.md) as the foundational piece that it must adhere to when establishing the plan.

### **STEP 6:** Generate task breakdown with /speckit.tasks

With the implementation plan validated, you can now break down the plan into specific, actionable tasks that can be executed in the correct order. Use the `/speckit.tasks` command to automatically generate a detailed task breakdown from your implementation plan:

```text
/speckit.tasks
```

This step creates a `tasks.md` file in your feature specification directory that contains:

- **Task breakdown organized by user story** - Each user story becomes a separate implementation phase with its own set of tasks
- **Dependency management** - Tasks are ordered to respect dependencies between components (e.g., models before services, services before endpoints)
- **Parallel execution markers** - Tasks that can run in parallel are marked with `[P]` to optimize development workflow
- **File path specifications** - Each task includes the exact file paths where implementation should occur
- **Test-driven development structure** - If tests are requested, test tasks are included and ordered to be written before implementation
- **Checkpoint validation** - Each user story phase includes checkpoints to validate independent functionality

The generated tasks.md provides a clear roadmap for the `/speckit.implement` command, ensuring systematic implementation that maintains code quality and allows for incremental delivery of user stories.

### **STEP 7:** Implementation

Once ready, use the `/speckit.implement` command to execute your implementation plan:

```text
/speckit.implement
```

The `/speckit.implement` command will:

- Validate that all prerequisites are in place (constitution, spec, plan, and tasks)
- Parse the task breakdown from `tasks.md`
- Execute tasks in the correct order, respecting dependencies and parallel execution markers
- Follow the TDD approach defined in your task plan
- Provide progress updates and handle errors appropriately

> [!IMPORTANT]
> The AI agent will execute local CLI commands (such as `dotnet`, `npm`, etc.) - make sure you have the required tools installed on your machine.

Once the implementation is complete, test the application and resolve any runtime errors that may not be visible in CLI logs (e.g., browser console errors). You can copy and paste such errors back to your AI agent for resolution.

</details>

---

## 🔍 Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```

## 💬 Support

For support, please open a [GitHub issue](https://github.com/loulanyue/spec-kit-zh/issues/new). We welcome bug reports, feature requests, and questions about using Spec-Driven Development.

## 🙏 Acknowledgements

This project is heavily influenced by and based on the work and research of [John Lam](https://github.com/jflam).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
