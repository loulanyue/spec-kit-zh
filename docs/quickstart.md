# 快速开始指南

本指南将帮助你使用 Spec Kit 快速上手规范驱动开发。

> [!NOTE]
> 所有自动化脚本现在都同时提供 Bash（`.sh`）和 PowerShell（`.ps1`）版本。除非显式传入 `--script sh|ps`，否则 `specify` CLI 会根据操作系统自动选择。

## 六步流程

> [!TIP]
> **上下文感知**：Spec Kit 命令会根据当前 Git 分支（例如 `001-feature-name`）自动识别当前活跃功能。要切换到其他规范，只需要切换 Git 分支即可。

### 第 1 步：安装 Specify

在终端中运行 `specify` CLI 命令来初始化项目：

```bash
# 创建新项目目录
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <PROJECT_NAME>

# 或者直接在当前目录初始化
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init .
```

如有需要，也可以显式指定脚本类型：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify init <PROJECT_NAME> --script sh  # Force POSIX shell
```

### 第 2 步：定义项目章程

在 AI Agent 的聊天界面中，使用 `/speckit.constitution` slash command 为项目建立核心规则与原则。你应当把项目的具体原则作为参数提供进去。

```markdown
/speckit.constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly. We prefer functional programming patterns.
```

### 第 3 步：创建规范

在聊天中使用 `/speckit.specify` slash command 描述你要构建什么。重点是说明 **做什么** 和 **为什么做**，而不是技术栈。

```markdown
/speckit.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### 第 4 步：细化规范

在聊天中使用 `/speckit.clarify` slash command 识别并解决规范中的模糊点。你也可以把希望重点澄清的方向作为参数传入。

```bash
/speckit.clarify Focus on security and performance requirements.
```

### 第 5 步：生成技术实施计划

在聊天中使用 `/speckit.plan` slash command 提供你的技术栈与架构选择。

```markdown
/speckit.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 第 6 步：拆分任务并实施

在聊天中使用 `/speckit.tasks` slash command 生成可执行的任务清单。

```markdown
/speckit.tasks
```

如果需要，也可以先用 `/speckit.analyze` 验证计划：

```markdown
/speckit.analyze
```

然后使用 `/speckit.implement` slash command 执行计划。

```markdown
/speckit.implement
```

> [!TIP]
> **分阶段实施**：对于复杂项目，建议按阶段实施，避免一次性压满 agent 上下文。先完成核心能力并验证可用，再逐步增加功能。

## 详细示例：构建 Taskify

下面是一个完整的团队效率平台构建示例：

### 第 1 步：定义章程

初始化项目章程，建立基本规则：

```markdown
/speckit.constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

### 第 2 步：使用 `/speckit.specify` 定义需求

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up.
```

### 第 3 步：细化规范

使用 `/speckit.clarify` 交互式解决规范中的模糊点。你也可以补充必须纳入的细节。

```bash
/speckit.clarify I want to clarify the task card details. For each task in the UI for a task card, you should be able to change the current status of the task between the different columns in the Kanban work board. You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task card, assign one of the valid users.
```

你也可以继续用 `/speckit.clarify` 追加更多细节：

```bash
/speckit.clarify When you first launch Taskify, it's going to give you a list of the five users to pick from. There will be no password required. When you click on a user, you go into the main view, which displays the list of projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns. You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can delete any comments that you made, but you can't delete comments anybody else made.
```

### 第 4 步：验证规范

使用 `/speckit.checklist` 验证规范检查清单：

```bash
/speckit.checklist
```

### 第 5 步：使用 `/speckit.plan` 生成技术计划

请尽量明确技术栈和技术要求：

```bash
/speckit.plan We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API, tasks API, and a notifications API.
```

### 第 6 步：定义任务

使用 `/speckit.tasks` 生成可执行的任务清单：

```bash
/speckit.tasks
```

### 第 7 步：验证并实施

先让 AI Agent 用 `/speckit.analyze` 审查实施计划：

```bash
/speckit.analyze
```

最后执行实现：

```bash
/speckit.implement
```

> [!TIP]
> **分阶段实施**：对于像 Taskify 这样的大项目，建议按阶段实施（例如第 1 阶段：项目/任务基础结构；第 2 阶段：Kanban 能力；第 3 阶段：评论与分配）。这样可以避免上下文过载，并支持每个阶段单独验证。

## 关键原则

- **明确表达** 你要构建什么，以及为什么构建
- **规范阶段不要过早陷入技术栈**
- **在实施前持续迭代和细化** 规范
- **在编码前先验证** 计划质量
- **让 AI Agent 处理** 更多实现细节

## 下一步

- 阅读 [完整方法论](../spec-driven.md) 获取更深入的说明
- 查看仓库中的 [更多模板与示例](../templates)
- 浏览 [GitHub 上的源码](https://github.com/loulanyue/spec-kit-zh)
