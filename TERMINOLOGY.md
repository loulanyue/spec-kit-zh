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
