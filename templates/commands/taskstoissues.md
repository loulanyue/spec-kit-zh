---
description: 基于现有设计制品，将任务转换为可执行、带依赖顺序的 GitHub Issues。
tools: ['github/github-mcp-server/issue_write']
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前，你**必须**考虑用户输入（如果不为空）。

## 概述

1. 在仓库根目录运行 `{SCRIPT}`，解析 FEATURE_DIR 和 AVAILABLE_DOCS 列表。所有路径必须使用绝对路径。对于包含单引号的参数（如 "I'm Groot"），使用转义语法：`'I'\''m Groot'`（或尽可能使用双引号）。
1. 从执行脚本的输出中提取 **tasks** 文件路径。
1. 通过以下命令获取 Git 远端地址：

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> 仅当远端地址为 GitHub URL 时，才继续执行后续步骤。

1. 对 tasks 列表中的每个任务，使用 GitHub MCP Server 在与 Git 远端对应的仓库中创建一个新 Issue，Issue 内容应准确反映该任务。

> [!CAUTION]
> 在任何情况下，都绝对不允许在与远端 URL 不匹配的仓库中创建 Issue。
