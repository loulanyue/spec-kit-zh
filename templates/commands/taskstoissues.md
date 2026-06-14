---
description: 基于现有设计制品，将任务转换为可执行、带依赖顺序的 GitHub Issues。
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->


## 用户输入

```text
$ARGUMENTS
```

在继续之前，你**必须**考虑用户输入（如果不为空）。用户可能指定：

- 特定功能目录（例如 `001-user-auth`）——如指定则仅处理该目录。
- 过滤标签或阶段（例如 `--phase=1`）——仅创建匹配的 Issues。
- 额外的 GitHub Labels（以逗号分隔）——附加到每个新建 Issue。

## 语言要求

- Issue 标题和正文使用简体中文，除非项目 `constitution.md` 另有规定。
- 代码示例、路径、命令保持原样，不翻译。

---

## 概述

本命令将 `.specify/<FEATURE_DIR>/tasks.md` 中的结构化任务列表转换为 GitHub Issues，
并按正确的依赖顺序提交，使团队可以立即在 GitHub Project Board 上开始追踪进度。

---

## 执行流程

### 步骤 1 — 前置条件检查

在仓库根目录运行 `{SCRIPT}`，解析 `FEATURE_DIR` 和 `AVAILABLE_DOCS` 列表。

- 所有路径必须使用绝对路径。
- 对于包含单引号的参数（如 `"I'm Groot"`），使用转义语法：`'I'\''m Groot'`（或尽可能使用双引号）。

### 步骤 2 — 解析任务文件

从脚本输出中提取 **tasks** 文件路径，读取其内容。

每个任务条目应包含：

| 字段 | 格式 | 说明 |
|---|---|---|
| 任务 ID | `T-NNN` | 全局唯一编号 |
| 标题 | 字符串 | 简洁描述 |
| 阶段 | `Phase N` | 执行阶段 |
| 依赖 | `T-NNN, T-NNN` | 前置任务 ID |
| 验收条件 | Markdown 列表 | 完成标准 |
| 负责角色 | 字符串 | 开发者 / QA / DevOps 等 |

若 `tasks.md` 中缺少某字段，使用空字符串并在 Issue 正文中标注 `TODO`。

### 步骤 3 — 确认远端仓库

通过以下命令获取 Git 远端地址：

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> 仅当远端地址为 **GitHub URL**（`github.com`）时，才继续执行后续步骤。
> 若为其他平台或本地路径，终止并提示用户。

从 URL 中解析 `{OWNER}` 和 `{REPO}`。验证你对该仓库有 `issues:write` 权限。

### 步骤 4 — 排序（拓扑排序）

根据依赖字段对任务做拓扑排序，确保：

1. 无依赖任务优先创建。
2. 被依赖的任务 Issue 编号在创建依赖任务时已知，可填入正文。
3. 若存在循环依赖，报告错误并终止，列出循环路径。

### 步骤 5 — 创建 Issues

对排序后的每个任务，使用 GitHub MCP Server 创建 Issue，格式如下：

**Issue 标题**：`[T-NNN] <任务标题>`

**Issue 正文模板**：

```markdown
## 任务描述

<任务说明，来自 tasks.md>

## 验收条件

<来自 tasks.md 的验收条件列表>

## 依赖关系

- 前置 Issues：<若有，列出 #<issue_number>，否则填"无">

## 元数据

| 字段 | 值 |
|---|---|
| 阶段 | Phase N |
| 负责角色 | <角色> |
| 任务 ID | T-NNN |
| 功能目录 | `.specify/<FEATURE_DIR>/` |

---
*此 Issue 由 `speckit.taskstoissues` 命令自动生成，来源：`tasks.md`。*
```

**Labels**（如仓库已存在对应标签则自动应用）：

- `spec-kit` — 标记所有自动生成的 Issues
- `phase-N` — 对应执行阶段
- 用户通过 `$ARGUMENTS` 额外传入的标签

> [!CAUTION]
> 在任何情况下，都绝对不允许在与远端 URL 不匹配的仓库中创建 Issue。

### 步骤 6 — 汇总报告

所有 Issue 创建完成后，输出汇总报告：

```
✅ 已创建 Issues 汇总
========================
T-001  #42  初始化数据库 Schema
T-002  #43  实现用户注册 API        依赖 → #42
T-003  #44  前端登录页面            依赖 → #43
...
总计：N 个 Issues 已创建于 github.com/{OWNER}/{REPO}
```

如有任何 Issue 创建失败，列出失败原因并提示手动重试。

---

## 幂等性说明

若相同 `[T-NNN]` 标题的 Issue 已存在于仓库中，**跳过创建**并在报告中注明"已存在：#<issue_number>"。
这确保命令可安全重复运行而不产生重复 Issues。
