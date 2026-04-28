<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# Spec Kit 工程逻辑详解（中文版）

## 1. 工程定位

`spec-kit` 不是单一工具，而是一套围绕 Spec-Driven Development（规格驱动开发，SDD）构建的工程化组合：
- 一个 CLI 分发包：`specify-cli-zh`
- 一组模板：规格、计划、任务、清单、命令模板
- 一组脚本：负责创建特性、检查前置条件、生成计划骨架、更新 agent 上下文
- 一套扩展机制：允许以插件形式追加命令与 hook
- 一组测试：验证 agent 配置、扩展系统、skills 安装等关键约束

它的核心目标不是“帮你写代码”，而是把“需求 -> 设计 -> 任务 -> 实现”变成一个可追踪、可自动化、可被不同 AI agent 复用的标准流程。

## 2. 仓库的核心组成

从工程结构看，`spec-kit` 主要由 5 层组成。

### 2.1 CLI 层

入口在 `src/specify_cli/__init__.py`，通过 `pyproject.toml` 暴露命令：

```toml
[project.scripts]
specify-zh = "specify_cli:main"
```

这意味着用户安装后实际使用的是：

```bash
specify-zh init ...
specify-zh check
```

CLI 是工程编排器，负责：
- 接收用户参数
- 识别目标 AI agent
- 下载或展开模板
- 生成 agent 命令目录
- 安装可选的 AI skills
- 调用脚本完成初始化与后续流程

### 2.2 模板层

模板位于 `templates/`，分两类：

1. 文档模板
- `spec-template.md`
- `plan-template.md`
- `tasks-template.md`
- `checklist-template.md`
- `constitution-template.md`
- `agent-file-template.md`

2. 命令模板
- `templates/commands/specify.md`
- `plan.md`
- `tasks.md`
- `implement.md`
- `clarify.md`
- `analyze.md`
- `checklist.md`
- `constitution.md`
- `taskstoissues.md`

这些命令模板不是普通说明文档，而是发给 AI agent 执行的“提示词协议”。它们定义了每个命令的目标、前置脚本、输入、输出、约束和执行步骤。

### 2.3 脚本层

脚本位于 `scripts/bash/` 与 `scripts/powershell/`，两套实现分别服务 POSIX Shell 和 PowerShell 环境。核心脚本包括：
- `create-new-feature.*`
- `check-prerequisites.*`
- `setup-plan.*`
- `update-agent-context.*`
- `common.*`

这一层承担真正的文件系统和分支操作，是“把提示词落到真实仓库状态”的关键。

### 2.4 扩展层

扩展系统实现在 `src/specify_cli/extensions.py`，并配套：
- `extensions/catalog.json`
- `extensions/catalog.community.json`
- `extensions/template/`
- 扩展规范文档和开发指南

它的作用是让 `spec-kit` 保持核心最小，同时允许外部模块增加命令、hook 和能力，而不把所有需求都塞进主仓库。

### 2.5 测试层

测试位于 `tests/`，当前重点覆盖：
- agent 配置一致性
- 扩展 manifest 校验与 registry 行为
- AI skills 安装逻辑
- 不同 agent 的目录映射是否一致

这说明该项目非常重视“多 agent 支持的配置一致性”和“可扩展机制的约束完整性”。

## 3. 核心工程思路

这个工程的设计逻辑可以概括为一句话：

> 用统一模板定义工作流，用脚本维护特性上下文，用 agent 适配层把同一套流程投射到不同 AI 编码工具中。

也就是说，`spec-kit` 的主线不是“语言框架适配”，而是“开发流程标准化 + 多 agent 分发”。

它默认认为一个功能开发应该经历如下阶段（Codex CLI 中对应写法为 `/prompts:speckit-*`）：

1. 建立项目原则：`/speckit.constitution`
2. 写需求规格：`/speckit.specify`
3. 补足澄清：`/speckit.clarify`
4. 生成技术计划：`/speckit.plan`
5. 生成任务清单：`/speckit.tasks`
6. 做一致性分析：`/speckit.analyze`
7. 执行实现：`/speckit.implement`
8. 需要时把任务转成 GitHub Issues：`/speckit.taskstoissues`

这套流程把“需求、设计、执行”拆成多个显式中间产物，而不是让 AI 一次性从一句话直接生成代码。

## 4. CLI 的工作逻辑

### 4.1 `specify-cli-zh` 是分发包，`specify-zh` 是初始化命令，不是完整工作流执行器

CLI 的职责主要在“初始化工程”和“准备 agent 环境”，而不是直接完成所有文档生成。

从 `README.md` 与代码可以看出，CLI 的核心命令主要是：
- `specify-zh init`
- `specify-zh check`

其中：
- `init` 负责把 `spec-kit` 模板和 agent 命令落到目标项目里
- `check` 负责检查 Git、agent CLI 等基础工具是否可用

真正的业务流程推进，大多是在初始化后，由 AI agent 通过命令模板继续执行。大多数 agent 使用 `/speckit.xxx`，而 Codex CLI 使用 `/prompts:speckit-xxx`。

### 4.2 `AGENT_CONFIG` 是多 agent 支持的单一事实源

`src/specify_cli/__init__.py` 中的 `AGENT_CONFIG` 是整个 agent 适配体系的核心配置。它为每个 agent 定义：
- 展示名称
- 命令文件所在目录
- 命令子目录名
- 是否要求 CLI
- 安装地址

例如不同 agent 的命令目录并不一致：
- Claude：`.claude/commands/`
- Gemini：`.gemini/commands/`
- Copilot：`.github/agents/`
- Codex：`.codex/prompts/`
- Windsurf：`.windsurf/workflows/`
- Tabnine：`.tabnine/agent/commands/`

这说明工程设计上并没有强迫所有 agent 使用同一目录规范，而是用一个中心配置表兼容它们的原生约定。

### 4.3 为什么强调“使用真实 CLI 名称做 key”

项目在 `AGENTS.md` 中特别强调：agent key 必须使用真实可执行名，而不是随便起别名。

原因很工程化：
- 工具检查依赖 `shutil.which()`
- 发布脚本、上下文更新脚本、帮助文案都要复用这套 key
- 如果 key 和真实 CLI 名称不一致，就会出现大量特殊映射逻辑

所以这个项目的一个核心设计原则是：

> 所有 agent 元数据集中管理，并尽量消灭“例外分支”。

## 5. 项目初始化逻辑

### 5.1 `specify-zh init` 的本质

`specify-zh init` 的本质是把一套通用 SDD 工程骨架注入目标仓库。它通常会做这些事：
- 选择脚本类型（sh 或 ps）
- 选择 AI agent
- 创建 `.specify/` 目录与模板
- 生成对应 agent 的命令文件
- 可选初始化 Git
- 可选安装 AI skills

初始化结束后，目标项目就具备了继续运行 `/speckit.specify`、`/speckit.plan` 等命令的条件；如果使用 Codex CLI，则对应为 `/prompts:speckit-specify`、`/prompts:speckit-plan` 等。

### 5.2 初始化后项目为什么是“模板 + agent 命令”的组合

这是 `spec-kit` 的一个重要设计取向。

它不是把所有逻辑都塞到 Python CLI 里，而是拆成两层：
- Python 只负责“安装和分发”
- 真正的工作流规则写在模板命令里

好处是：
- 便于支持不同 agent
- 便于团队直接阅读和修改命令模板
- 模板升级不一定需要重写 Python 逻辑
- 工作流本身更透明

## 6. Feature 工作流如何落地

这一部分是整个工程最关键的逻辑。

### 6.1 Feature 目录是状态载体

`scripts/bash/common.sh` 定义了一组关键路径：
- `FEATURE_DIR`
- `FEATURE_SPEC`
- `IMPL_PLAN`
- `TASKS`
- `RESEARCH`
- `DATA_MODEL`
- `QUICKSTART`
- `CONTRACTS_DIR`

也就是说，`spec-kit` 不是把状态存在数据库或隐藏缓存里，而是把每个功能的生命周期状态直接映射成一组文件。

典型路径形态是：

```text
specs/
  001-some-feature/
    spec.md
    plan.md
    tasks.md
    research.md
    data-model.md
    quickstart.md
    contracts/
```

这是一种“文档即状态机”的设计。

### 6.2 分支名与特性目录绑定

`create-new-feature.sh` 负责：
- 解析用户给的功能描述
- 生成短名称
- 找到下一个可用编号
- 创建分支名，如 `001-user-auth`
- 创建对应的 `specs/001-user-auth/` 目录

这个逻辑很关键，因为它把：
- Git 分支
- Feature 编号
- Spec 目录

三者绑在一起，从而保证每个功能的中间产物都有稳定归属。

### 6.3 为什么要用编号前缀而不是只用名称

脚本不只是取 `feature-name`，还要生成三位编号前缀，例如 `004-xxx`。原因有三个：

1. 保证顺序性，方便追踪功能演进
2. 即使短名称撞车，编号也能区分
3. 可以允许多个分支共享同一编号前缀，对应同一个规格目录

`common.sh` 里的 `find_feature_dir_by_prefix()` 就体现了这个思路：
- 它优先按数字前缀查找 spec 目录
- 而不是强制要求目录名和分支名完全一致

这使得“围绕同一 spec 开多个分支”成为可能。

## 7. 命令模板如何驱动流程

### 7.1 模板中的 frontmatter 是执行元数据

每个命令模板顶部都有 frontmatter，例如：
- `description`
- `scripts`
- `handoffs`
- `tools`

这些元数据不是装饰性的，它们定义了：
- 执行这个命令前要运行哪个脚本
- 执行完成后建议交给哪个后续命令
- 是否依赖外部工具，例如 GitHub MCP

换句话说，命令模板是“声明式工作流节点”。

### 7.2 `/speckit.specify` 的逻辑

`templates/commands/specify.md` 的职责是从自然语言生成 `spec.md`。

它的核心约束是：
- 聚焦 WHAT 和 WHY，不写 HOW
- 缺失信息时尽量做合理默认推断
- 最多保留 3 个 `NEEDS CLARIFICATION`
- 写完后还要生成一个 requirements checklist 做自检

这说明 `spec-kit` 并不鼓励无限追问用户，而是优先把规格写出来，只在真正影响范围、权限、安全、体验的关键点上保留澄清点。

### 7.3 `/speckit.clarify` 的逻辑

`clarify.md` 负责扫描 `spec.md` 中的不明确点，并以最多 5 个问题补全关键信息，再把答案回写到 spec。

这一步的本质是：
- 把一次性生成的规格文档做第二轮去歧义
- 防止不明确的内容流入 plan 和 tasks

也就是说，`specify` 允许带少量不确定性，而 `clarify` 负责把这些不确定性收敛掉。

### 7.4 `/speckit.plan` 的逻辑

`plan.md` 命令会先调用 `setup-plan.sh` 建立 `plan.md` 骨架，然后要求 AI：
- 从 spec 推导技术上下文
- 做 constitution 检查
- 补 research
- 产出 data model、contracts、quickstart
- 更新 agent 上下文文件

这里的关键思想是：

> plan 不是简单写技术方案，而是把“实现前的关键工程制品”一次性组织出来。

### 7.5 `/speckit.tasks` 的逻辑

`tasks.md` 的生成规则非常严格。它要求：
- 按用户故事组织任务，不是按技术层组织
- 每个任务都要有 ID
- 指出是否可并行 `[P]`
- 指出属于哪个用户故事 `[US1]`
- 带清晰文件路径

这说明 `spec-kit` 想解决的是“大模型生成任务列表太泛、不可执行”的问题。它希望 `tasks.md` 是可以被另一个 agent 直接执行的，而不是只给人类做参考。

### 7.6 `/speckit.analyze` 的逻辑

这是一个只读分析命令，专门在 `spec.md`、`plan.md`、`tasks.md` 三者之间做一致性检查。重点检查：
- 重复与冲突
- 模糊表述
- 覆盖缺失
- 宪章冲突
- 需求与任务映射缺口

这一设计很重要，因为它把“写完任务就开工”的路径多加了一道质量闸门。

### 7.7 `/speckit.implement` 的逻辑

虽然本次没有深入实现细节代码，但从命令体系可以清楚推断：
- `implement` 的输入不是一句需求，而是已经稳定的 `tasks.md`
- 它依赖前面阶段把模糊性尽量消化掉
- 它强调按 phase 和 story 递进式实现

这符合整个项目的一贯思想：

> AI 不直接从模糊需求跳到代码，而是沿着一条有中间制品的流水线前进。

## 8. 前置检查脚本的作用

### 8.1 `check-prerequisites.sh` 是所有命令的状态守门员

很多命令模板都会先运行 `check-prerequisites.sh`，它负责：
- 确认当前 feature 目录存在
- 确认 `plan.md` 是否存在
- 必要时确认 `tasks.md` 是否存在
- 返回当前 feature 已有哪些文档

这带来两个工程收益：
- 命令模板不用自己写一遍状态判断逻辑
- AI agent 可以通过 JSON 方式稳定拿到上下文路径

也就是说，它相当于“工作流状态探测器”。

### 8.2 `--json`、`--paths-only` 等参数的意义

这些参数不是细枝末节，而是为了适配不同命令阶段：
- `--paths-only`：只要路径，不做前置校验，适合较早阶段
- `--require-tasks`：要求任务文件已存在，适合 implement 或 analyze
- `--include-tasks`：把 `tasks.md` 加入可用文档列表

这体现出脚本设计是分阶段的，不同命令只拿自己需要的最小上下文。

## 9. Agent 上下文更新逻辑

### 9.1 为什么需要 `update-agent-context.sh`

计划阶段不仅生成 `plan.md`，还会更新当前项目里 agent 专用的上下文文件，例如：
- `CLAUDE.md`
- `GEMINI.md`
- `AGENTS.md`
- `.cursor/rules/specify-rules.mdc`
- `.windsurf/rules/specify-rules.md`

目的很明确：
- 让后续 agent 在继续实现时知道项目语言、框架、数据库、结构
- 避免每轮都重新从代码库推断技术栈

### 9.2 这个脚本更新哪些信息

从脚本实现看，它会从 `plan.md` 提取：
- `Language/Version`
- `Primary Dependencies`
- `Storage`
- `Project Type`

然后把这些信息写入 agent 上下文模板，生成适合当前技术栈的：
- 技术栈描述
- 推荐项目结构
- 典型命令（例如 `pytest`、`npm test`、`cargo test`）

这让 `plan.md` 变成了“agent 可消费的技术事实源”。

## 10. Extension 扩展系统逻辑

### 10.1 扩展系统的目标

`src/specify_cli/extensions.py` 表明，项目并不想把所有命令都固化在核心仓库里，而是允许通过扩展包追加：
- 新命令
- hook
- 扩展说明与版本约束

这是一种很标准的“核心稳定，能力外置”的架构思路。

### 10.2 manifest 校验机制

扩展通过 `extension.yml` 描述自己，核心字段包括：
- `schema_version`
- `extension`
- `requires`
- `provides`

并且会校验：
- 扩展 ID 格式
- 语义化版本
- 所需 `speckit_version`
- 提供的命令名是否符合 `speckit.{extension}.{command}` 规范

这说明扩展系统并不是松散插件目录，而是有严格契约的。

### 10.3 registry 的作用

`ExtensionRegistry` 在 `.specify/extensions/` 下维护安装记录，负责：
- 记录安装时间
- 记录版本和来源
- 判断扩展是否已安装
- 移除安装元数据

也就是说，扩展不是“复制即完事”，而是有可查询的已安装状态。

### 10.4 hook 与 tasks 流程耦合

从 `templates/commands/tasks.md` 可以看到，扩展 hook 支持：
- `before_tasks`
- `after_tasks`

其中：
- 可选 hook 会提示用户主动执行
- 必需 hook 会要求自动执行并等待结果

这说明扩展系统最先切入的是“任务生成前后”的节点，因为这里最适合插入额外分析、治理或质量检查逻辑。

## 11. AI Skills 安装逻辑

### 11.1 `--ai-skills` 在做什么

测试 `test_ai_skills.py` 显示，项目支持把命令模板进一步转换为 agent 的 `SKILL.md` 结构，安装到不同 agent 的技能目录。

例如：
- Claude：`.claude/skills/`
- Gemini：`.gemini/skills/`
- Codex：通过 override 映射到特定目录
- Tabnine：`.tabnine/agent/skills/`

### 11.2 为什么要把命令模板再转成 skill

原因是不同 agent 生态对“可复用提示能力”的抽象不同：
- 有的叫 commands
- 有的叫 prompts
- 有的叫 skills
- 有的放在 IDE rules 中

`spec-kit` 通过一层转换，把同一份命令模板包装成目标 agent 能理解的技能格式。这是它支持多 agent 的另一个关键机制。

## 12. 测试体系反映出的工程重点

从当前测试可以看出，项目最重视的不是业务算法，而是“平台一致性”。

重点测试对象包括：
- agent 配置是否和发布脚本一致
- 技能目录是否映射正确
- 扩展 manifest 是否有效
- 新 agent 接入是否同步影响帮助文本、上下文脚本、打包脚本

这说明它是一个偏“开发工具链”的工程，测试重点自然落在：
- 配置一致性
- 文件生成正确性
- 跨平台行为
- 契约稳定性

## 13. 这个工程最重要的设计取舍

### 13.1 用文件系统承载状态，而不是内部数据库

优点：
- 透明
- 可版本化
- 可人工编辑
- 便于 AI agent 直接读写

代价：
- 强依赖目录结构和命名规范
- 容易受到用户手工改动影响

### 13.2 用模板命令表达流程，而不是把流程写死在 CLI

优点：
- 易改
- 易读
- 易适配多 agent
- 工作流升级成本低

代价：
- 模板本身会变复杂
- 需要脚本和模板协同维护

### 13.3 用 `AGENT_CONFIG` 统一 agent 适配

优点：
- 多 agent 扩展更可控
- 帮助文本、目录生成、工具检测可复用同一份配置

代价：
- 一旦 agent 支持变多，一致性维护压力会上升
- 所以必须依赖测试兜底

### 13.4 用显式中间产物限制 AI 的自由发挥

中间产物包括：
- `spec.md`
- `plan.md`
- `tasks.md`
- `research.md`
- `data-model.md`
- `quickstart.md`
- `contracts/`

这背后的哲学是：

> 不信任一次性生成大而全的代码结果，而是通过逐步收敛的中间文档提升正确率和可追踪性。

## 14. 一条完整的运行链路示例

假设用户在一个新项目中使用 `spec-kit`，大致会发生下面这些事：

1. 执行 `specify-zh init my-project --ai claude`
2. CLI 把 `.specify/` 模板和 `.claude/commands/` 命令落到项目中
3. 用户在 agent 里运行 `/speckit.constitution`（Codex CLI 中对应 `/prompts:speckit-constitution`）
4. 用户运行 `/speckit.specify "我要做一个照片管理应用"`（Codex CLI 中对应 `/prompts:speckit-specify "我要做一个照片管理应用"`）
5. `create-new-feature.sh` 创建 `001-photo-management` 分支和 `specs/001-photo-management/spec.md`
6. agent 按 `specify.md` 模板写出规格文档和 requirements checklist
7. 用户运行 `/speckit.clarify`（Codex CLI 中对应 `/prompts:speckit-clarify`）
8. agent 对 spec 做去歧义补全
9. 用户运行 `/speckit.plan`（Codex CLI 中对应 `/prompts:speckit-plan`）
10. `setup-plan.sh` 建立 `plan.md`，agent 生成 research、data model、contracts、quickstart，并调用 `update-agent-context.sh`
11. 用户运行 `/speckit.tasks`（Codex CLI 中对应 `/prompts:speckit-tasks`）
12. agent 生成按用户故事组织的 `tasks.md`
13. 用户运行 `/speckit.analyze`（Codex CLI 中对应 `/prompts:speckit-analyze`）
14. agent 检查 spec、plan、tasks 是否一致
15. 用户运行 `/speckit.implement`（Codex CLI 中对应 `/prompts:speckit-implement`）
16. agent 按任务阶段逐步实现功能

这就是 `spec-kit` 的完整工程闭环。

## 15. 总结

如果只看表面，`spec-kit` 很像“提示词模板仓库”。

但从工程逻辑上看，它其实是一个分层明确的开发工作流平台：
- CLI 负责初始化与分发
- 模板定义流程协议
- 脚本维护 feature 状态与路径
- agent 适配层解决多工具兼容
- 扩展系统负责能力增量
- 测试保证配置与生成逻辑的一致性

它最核心的价值，不是帮某个 agent 更聪明，而是让不同 agent 都沿着同一条可审计、可追踪、可复用的规格驱动流程工作。

## 16. 阅读建议

如果你要继续深入源码，建议按这个顺序读：

1. `README.md`
2. `src/specify_cli/__init__.py`
3. `templates/commands/specify.md`
4. `templates/commands/plan.md`
5. `templates/commands/tasks.md`
6. `scripts/bash/common.sh`
7. `scripts/bash/create-new-feature.sh`
8. `scripts/bash/check-prerequisites.sh`
9. `scripts/bash/update-agent-context.sh`
10. `src/specify_cli/extensions.py`
11. `tests/test_extensions.py`
12. `tests/test_ai_skills.py`

按这个顺序，最容易把“初始化器 -> 流程模板 -> 文件状态 -> 扩展机制”这条主线串起来。
