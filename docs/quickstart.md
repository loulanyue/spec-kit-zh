<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 快速开始指南

本指南将帮助你使用 Spec Kit 快速上手规范驱动开发。

> [!NOTE]
> 所有自动化脚本现在都同时提供 Bash（`.sh`）和 PowerShell（`.ps1`）版本。除非显式传入 `--script sh|ps`，否则 `specify-zh` CLI 会根据操作系统自动选择。

## 六步流程

> [!TIP]
> **上下文感知**：Spec Kit 命令会根据当前 Git 分支（例如 `001-feature-name`）自动识别当前活跃功能。要切换到其他规范，只需要切换 Git 分支即可。

### 第 1 步：安装 `specify-cli-zh`

安装 `specify-cli-zh` 后，在终端中使用 `specify-zh` 命令初始化项目：

```bash
# 创建新项目目录
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init <PROJECT_NAME>

# 或者直接在当前目录初始化
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init .
```

如有需要，也可以显式指定脚本类型：

```bash
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://github.com/loulanyue/spec-kit-zh.git specify-zh init <PROJECT_NAME> --script sh  # Force POSIX shell
```

> [!TIP]
> 如果你在国内网络环境下访问 GitHub 较慢，请参考 [china-network.md](./china-network.md) 了解代理配置方案。

### 第 2 步：定义项目章程

在 AI Agent 的聊天界面中，使用 `/speckit.constitution` slash command 为项目建立核心规则与原则。Codex 用户请使用 `/prompts:speckit-constitution`。

> [!TIP]
> 如果你使用的是 Codex，请直接输入 `/prompts:speckit-constitution ...`。
> 不需要使用 `/prompt.speckit.constitution` 或 `/prompts.speckit.constitution` 这类前缀。

```markdown
/prompts:speckit-constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly. We prefer functional programming patterns.
```

### 第 3 步：创建规范

在聊天中使用 `/speckit.specify` slash command 描述你要构建什么。Codex 用户请使用 `/prompts:speckit-specify`。

```markdown
/prompts:speckit-specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### 第 4 步：细化规范

在聊天中使用 `/speckit.clarify` slash command 识别并解决规范中的模糊点。Codex 用户请使用 `/prompts:speckit-clarify`。

```bash
/prompts:speckit-clarify Focus on security and performance requirements.
```

> [!NOTE]
> `clarify` 命令每次会话最多提出 5 个高优先级问题，并将答案直接写回 `spec.md`。你可以多次运行 `clarify` 来完善不同方面的需求。

### 第 5 步：生成技术实施计划

在聊天中使用 `/speckit.plan` slash command 提供你的技术栈与架构选择。Codex 用户请使用 `/prompts:speckit-plan`。

```markdown
/prompts:speckit-plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 第 6 步：拆分任务并实施

在聊天中使用 `/speckit.tasks` slash command 生成可执行的任务清单。Codex 用户请使用 `/prompts:speckit-tasks`。

```markdown
/prompts:speckit-tasks
```

如果需要，也可以先用 `/speckit.analyze` 验证计划。Codex 用户请使用 `/prompts:speckit-analyze`：

```markdown
/prompts:speckit-analyze
```

然后使用 `/speckit.implement` slash command 执行计划。Codex 用户请使用 `/prompts:speckit-implement`。

```markdown
/prompts:speckit-implement
```

> [!TIP]
> **分阶段实施**：对于复杂项目，建议按阶段实施，避免一次性压满 agent 上下文。先完成核心能力并验证可用，再逐步增加功能。

---

## 命令速查表

| 命令（通用） | 命令（Codex CLI） | 说明 |
|-------------|------------------|------|
| `/speckit.constitution` | `/prompts:speckit-constitution` | 定义项目章程与约束 |
| `/speckit.specify` | `/prompts:speckit-specify` | 创建功能规范 |
| `/speckit.clarify` | `/prompts:speckit-clarify` | 澄清规范中的歧义 |
| `/speckit.checklist` | `/prompts:speckit-checklist` | 验证规范质量 |
| `/speckit.plan` | `/prompts:speckit-plan` | 生成技术实施计划 |
| `/speckit.tasks` | `/prompts:speckit-tasks` | 生成可执行任务清单 |
| `/speckit.analyze` | `/prompts:speckit-analyze` | 一致性分析（只读） |
| `/speckit.implement` | `/prompts:speckit-implement` | 按阶段执行实施 |

---

## 详细示例：构建 Taskify

下面是一个完整的团队效率平台构建示例：

### 第 1 步：定义章程

初始化项目章程，建立基本规则。通用写法是 `/speckit.constitution`，Codex CLI 对应 `/prompts:speckit-constitution`：

```markdown
/speckit.constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

### 第 2 步：使用 `/speckit.specify` 定义需求

如果你使用 Codex CLI，请将下列命令前缀替换为 `/prompts:speckit-specify`。

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

使用 `/speckit.clarify` 交互式解决规范中的模糊点；如果你使用 Codex CLI，请改用 `/prompts:speckit-clarify`。你也可以补充必须纳入的细节。

```bash
/speckit.clarify I want to clarify the task card details. For each task in the UI for a task card, you should be able to change the current status of the task between the different columns in the Kanban work board. You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task card, assign one of the valid users.
```

你也可以继续用 `/speckit.clarify` 追加更多细节：

```bash
/speckit.clarify When you first launch Taskify, it's going to give you a list of the five users to pick from. There will be no password required. When you click on a user, you go into the main view, which displays the list of projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns. You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can delete any comments that you made, but you can't delete comments anybody else made.
```

### 第 4 步：验证规范

使用 `/speckit.checklist` 验证规范检查清单；如果你使用 Codex CLI，请改用 `/prompts:speckit-checklist`：

```bash
/speckit.checklist
```

### 第 5 步：使用 `/speckit.plan` 生成技术计划

如果你使用 Codex CLI，请将命令替换为 `/prompts:speckit-plan`。

请尽量明确技术栈和技术要求：

```bash
/speckit.plan We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API, tasks API, and a notifications API.
```

### 第 6 步：定义任务

使用 `/speckit.tasks` 生成可执行的任务清单；如果你使用 Codex CLI，请改用 `/prompts:speckit-tasks`：

```bash
/speckit.tasks
```

### 第 7 步：验证并实施

先让 AI Agent 用 `/speckit.analyze` 审查实施计划；如果你使用 Codex CLI，请改用 `/prompts:speckit-analyze`：

```bash
/speckit.analyze
```

最后执行实现；如果你使用 Codex CLI，请改用 `/prompts:speckit-implement`：

```bash
/speckit.implement
```

> [!TIP]
> **分阶段实施**：对于像 Taskify 这样的大项目，建议按阶段实施（例如第 1 阶段：项目/任务基础结构；第 2 阶段：Kanban 能力；第 3 阶段：评论与分配）。这样可以避免上下文过载，并支持每个阶段单独验证。

---

## 常见踩坑

初次使用 Spec Kit 时，以下是最容易犯的错误：

| 踩坑 | 原因 | 解决方式 |
|---|---|---|
| 斜杠命令不显示 | Agent 未重启，或文件路径不对 | 完全重启 IDE；运行 `specify-zh codex-sync` |
| AI 输出的规范质量很差 | 直接用 `/specify` 而跳过了 `/clarify` | 先运行 `/speckit.clarify` 充分澄清需求 |
| `init` 报错"目录非空" | 在已有代码的目录运行了 `init` | 追加 `--here --force` 参数 |
| 任务清单过于粗粒度 | `spec.md` 验收标准不够具体 | 回到 `/speckit.clarify` 补充可测试的验收条件 |
| `implement` 输出偏离预期 | 跳过了 `analyze` 一致性检查步骤 | 在 `implement` 前先运行 `/speckit.analyze` |
| 章程更新后旧规范仍然有效 | `constitution.md` 已改但规范未同步 | 重新运行 `/speckit.specify` 或手动更新受影响的规范 |

> [!TIP]
> 遇到疑难问题，可查阅 [常见问题与排错](./troubleshooting.md) 或在 [GitHub Issues](https://github.com/loulanyue/spec-kit-zh/issues) 提问。

---

## 下一步

- 阅读 [完整方法论](../spec-driven.md) 获取更深入的说明，包括 FAQ 章节
- 查看仓库中的 [更多模板与示例](../templates)
- 遇到问题？参考 [常见问题与排错](./troubleshooting.md)
- 国内网络访问慢？查看 [国内网络加速指引](./china-network.md)
- 想接入国内大模型？查看 [国内大模型接入指南](./domestic-llm.md)
- 浏览 [GitHub 上的源码](https://github.com/loulanyue/spec-kit-zh)
