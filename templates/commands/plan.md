---
description: 执行实施规划工作流，并使用计划模板生成设计制品。
handoffs: 
  - label: 创建任务
    agent: speckit.tasks
    prompt: 将计划拆解为任务
    send: true
  - label: 创建检查清单
    agent: speckit.checklist
    prompt: 为以下领域创建检查清单...
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->


## 用户输入

```text
$ARGUMENTS
```

在继续之前，你**必须**考虑用户输入（如果不为空）。

## 语言要求

- 所有面向用户的生成制品与摘要，包括 `plan.md`、`research.md`、`data-model.md`、`quickstart.md`、合同描述和完成报告，都必须使用简体中文。
- 文件路径、命令、ID 和代码/配置键在需要时保持机器可读原样。

## 概述

1. **设置**：从仓库根目录运行 `{SCRIPT}` 并解析 JSON 输出，获取 FEATURE_SPEC、IMPL_PLAN、SPECS_DIR 和 BRANCH 的路径。对于参数中的单引号（例如 "I'm Groot"），使用转义语法：例如 `'I'\''m Groot'`（或尽量使用双引号）。

2. **加载上下文**：读取 FEATURE_SPEC 和 `/memory/constitution.md` 的内容。加载已复制的 IMPL_PLAN 模板。

3. **执行规划工作流**：按照 IMPL_PLAN 模板的结构执行：
   - 填写“技术上下文”（将未知项标记为 "NEEDS CLARIFICATION"）
   - 根据章程内容填写“宪章检查”部分
   - 评估门禁（如果存在无合理解释的违反项则报错退出）
   - 第 0 阶段：生成 `research.md`（解决所有 "NEEDS CLARIFICATION" 项）
   - 第 1 阶段：生成 `data-model.md`、`contracts/` 目录和 `quickstart.md`
   - 第 1 阶段：运行 agent 脚本以更新 agent 上下文
   - 重新评估设计完成后的“宪章检查”

4. **停止并报告**：在完成第 2 阶段规划后结束命令。报告当前分支、IMPL_PLAN 路径以及已生成的制品。

## 阶段步骤

### 第 0 阶段：提纲与研究

1. **从上方“技术上下文”中提取未知项**：
   - 每一个 NEEDS CLARIFICATION → 研究任务
   - 每一个依赖项 → 最佳实践任务
   - 每一个集成项 → 模式任务

2. **生成并分派研究任务**：

   ```text
   针对技术上下文中的每一个未知项：
     任务："研究 {unknown} 在 {feature context} 中的应用"
   针对每一个技术选型：
     任务："寻找 {tech} 在 {domain} 领域的最佳实践"
   ```

3. **在 `research.md` 中汇总研究结果**，采用以下格式：
   - 决策：[选择了什么方案]
   - 理由：[为什么选择该方案]
   - 评估过的替代方案：[还评估了什么其他方案]

**产出**：完成 `research.md` 并解决所有 NEEDS CLARIFICATION 标记。

### 第 1 阶段：设计与契约

**前置条件：** `research.md` 已完成。

1. **从功能规范中提取实体** → `data-model.md`：
   - 实体名称、字段、关系
   - 来自需求的验证规则
   - 状态转移逻辑（如果适用）

2. **定义接口契约**（如果项目具有外部接口）→ `/contracts/` 目录：
   - 识别项目向用户或其他系统暴露的接口
   - 记录适合项目类型的契约格式
   - 示例：库的公共 API、CLI 工具的命令行 Schema、Web 服务的端点、解析器的语法规则、应用程序的 UI 契约
   - 如果项目纯粹是内部的（构建脚本、一次性工具等），则跳过此步

3. **更新 Agent 上下文**：
   - 运行 `{AGENT_SCRIPT}`
   - 这些脚本会自动检测当前使用的 AI Agent
   - 更新相应的 Agent 专用上下文文件
   - 仅添加当前计划中的新技术
   - 保留在标记之间的手动修改内容

**产出**：`data-model.md`、`/contracts/*`、`quickstart.md`、Agent 专用上下文文件。

## 关键规则

- 始终使用绝对路径。
- 如果门禁检查失败或存在未解决的澄清项，则报错退出。
