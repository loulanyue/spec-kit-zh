<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 术语表

本文件用于统一 `spec-kit-zh` 中的中文术语，避免同一概念出现多种译法。

## 核心术语

| 英文原文 | 中文术语 | 说明 |
| --- | --- | --- |
| `Spec` | 规范 | 泛指规范文档或规格说明 |
| `Specification` | 规范文档 | 完整的规格说明文件 |
| `Plan` | 计划 | 实施计划文件（`plan.md`） |
| `Implementation Plan` | 实施计划 | 详细说明功能实现路径的计划 |
| `Tasks` | 任务 | 细分的执行条目（`tasks.md`） |
| `Constitution` | 章程 | 项目级约定与风格规范 |
| `Extension` | 扩展 | 对 Spec Kit 的功能扩充模块 |
| `Catalog` | 目录 | 扩展或模板的索引清单 |
| `Community Catalog` | 社区目录 | 由社区维护的扩展目录 |
| `Agent` | Agent | AI 编码助手（保留英文） |
| `AI Assistant` | AI 助手 | 泛指 AI 辅助工具 |
| `Skill` | Skill | Agent 的自定义能力模块（保留英文） |
| `Template` | 模板 | 供 init 命令使用的文件模板 |
| `Workflow` | 工作流 | 描述开发流程的抽象步骤序列 |
| `Requirements` | 需求 | 功能或非功能需求描述 |
| `User Story` | 用户故事 | 以用户视角描述的需求单元 |
| `Acceptance Criteria` | 验收标准 | 确认需求满足的判断条件 |
| `Success Criteria` | 成功标准 | 衡量功能成功与否的指标 |
| `Frontmatter` | 前置元数据 | Markdown 文件顶部的 YAML 块 |
| `Prompt` | 提示词 | 发送给 AI 的指令文本 |
| `Slash Command` | 斜杠命令 | Agent 中以 `/` 开头的快捷指令 |
| `Spec-Driven Development` | 规范驱动开发 | 本工具的核心开发方法论（缩写 SDD） |
| `Init` | 初始化 | `specify-zh init` 所执行的项目初始化操作 |

## 流程术语

| 英文原文 | 中文术语 | 说明 |
| --- | --- | --- |
| `Clarify` | 澄清 | 在规范编写前向用户提问并确认需求的步骤 |
| `Analyze` | 分析 | 对现有制品和代码库进行调研评估的步骤 |
| `Research` | 研究 | 针对技术选型和未知点的深度调研（生成 `research.md`） |
| `Phase` | 阶段 | 实施计划中按顺序划分的执行单元 |
| `Gate` | 门禁 | 进入下一阶段前必须通过的验收检查点 |
| `Handoff` | 移交 | 从一个命令流转到下一个命令的动作 |
| `Sync Impact Report` | 同步影响报告 | 章程更新后列出受影响制品的汇总报告 |
| `Rollback` | 回滚 | 将项目恢复到上一个已知良好状态的操作 |
| `Idempotent` | 幂等 | 重复执行相同操作结果不变的特性 |
| `Upstream` | 上游 | 指 spec-kit 英文原版仓库 |
| `Downstream` | 下游 | 指基于 spec-kit-zh 的派生项目或使用者 |

## 代码与工程术语

| 英文原文 | 中文术语 | 说明 |
| --- | --- | --- |
| `Frontmatter` | 前置元数据 | Markdown 文件 `---` 包裹的 YAML 头部块 |
| `Data Model` | 数据模型 | 描述实体、字段和关系的结构（生成 `data-model.md`） |
| `Contract` | 接口契约 | API、CLI 或 UI 的对外接口协议（生成 `contracts/` 目录） |
| `NFR` | 非功能需求 | Non-Functional Requirement，如性能、安全、可用性等约束 |
| `Brand Guard` | 品牌守护 | CI 中检测包名和命令名是否符合中文版命名规范的自动检测 |
| `Codex Sync` | Codex 同步 | 将模板提示词同步到 Codex 提示词目录的操作 |
| `Topology Sort` | 拓扑排序 | 按任务依赖关系确定执行顺序的算法 |
| `Coverage` | 测试覆盖率 | 被测试代码覆盖的行数百分比 |

## 保留英文的场景

- 命令名、参数名、环境变量、目录名、文件名保持英文。
- frontmatter 键名、JSON/YAML/TOML 字段名保持英文。
- `spec.md`、`plan.md`、`tasks.md`、`SKILL.md` 等文件名不翻译。
- `slash commands`、`Prompt.MD`、`agent skills` 这类约定名词优先保留英文。
- 代码示例、命令行片段中出现的所有标识符不翻译。

## 书写建议

- 用户可见说明以简体中文为主。
- 技术术语在首次出现时可中文为主、英文补充，例如：规范（Spec）。
- 与实现细节强绑定的关键词尽量保留英文原文，减少歧义。
- 文档标题中中英混排时，英文单词前后各留一个半角空格。
- 新引入术语应先在本文件登记，再在其他文档中使用。
