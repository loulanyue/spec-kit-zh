# 实施计划：[功能名称]

**分支**：`[###-feature-name]` | **日期**：[DATE] | **规格说明**：[link]
**输入**：来自 `/specs/[###-feature-name]/spec.md` 的功能规格说明

**说明**：该模板由计划命令填充；大多数 agent 使用 `/speckit.plan`，Codex CLI 使用 `/prompts:speckit-plan`。执行流程见 `.specify/templates/plan-template.md`。

## 摘要

[从功能规格中提取：主要需求 + 来自 research 的技术方案]

## 技术上下文

<!--
  需要操作：请将本节内容替换为该项目的真实技术上下文。
  这里的结构仅作为规划时的参考骨架，用于帮助你系统化补全信息。
-->

**语言/版本**：[例如 Python 3.11、Swift 5.9、Rust 1.75，或 NEEDS CLARIFICATION]  
**主要依赖**：[例如 FastAPI、UIKit、LLVM，或 NEEDS CLARIFICATION]  
**存储**：[若适用，例如 PostgreSQL、CoreData、文件，或 N/A]  
**测试方式**：[例如 pytest、XCTest、cargo test，或 NEEDS CLARIFICATION]  
**目标平台**：[例如 Linux 服务器、iOS 15+、WASM，或 NEEDS CLARIFICATION]
**项目类型**：[例如 library/cli/web-service/mobile-app/compiler/desktop-app，或 NEEDS CLARIFICATION]  
**性能目标**：[领域相关，例如 1000 req/s、每秒 1 万行、60 fps，或 NEEDS CLARIFICATION]  
**约束条件**：[领域相关，例如 p95 < 200ms、内存 < 100MB、可离线运行，或 NEEDS CLARIFICATION]  
**规模范围**：[领域相关，例如 1 万用户、100 万行代码、50 个界面，或 NEEDS CLARIFICATION]

## 宪章检查

*门禁：必须先通过本检查，才能进入第 0 阶段研究；并在第 1 阶段设计后重新复核。*

[根据宪章文件确定的门禁项]

## 项目结构

### 文档（当前功能）

```text
specs/[###-feature]/
├── plan.md              # 本文件（plan 命令输出）
├── research.md          # 第 0 阶段输出（plan 命令）
├── data-model.md        # 第 1 阶段输出（plan 命令）
├── quickstart.md        # 第 1 阶段输出（plan 命令）
├── contracts/           # 第 1 阶段输出（plan 命令）
└── tasks.md             # 第 2 阶段输出（tasks 命令，不由 plan 命令创建）
```

### 源代码（仓库根目录）
<!--
  需要操作：请将下方占位目录树替换为本功能实际采用的项目结构。
  删除未使用的方案，并将选中的结构扩展为真实路径（如 apps/admin、packages/something）。
  最终交付的计划中不应保留“方案 1/2/3”这类标签字样。
-->

```text
# [如未使用请删除] 方案 1：单体项目（默认）
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [如未使用请删除] 方案 2：Web 应用（检测到 “frontend” + “backend” 时）
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [如未使用请删除] 方案 3：移动端 + API（检测到 “iOS/Android” 时）
api/
└── [same as backend above]

ios/ or android/
└── [平台专用结构：功能模块、界面流程、平台测试]
```

**结构决策**：[说明选定的结构，并引用上面列出的真实目录]

## 复杂度跟踪

> **仅当宪章检查存在必须说明理由的违反项时填写**

| 违反项 | 必要原因 | 拒绝更简单方案的原因 |
|-----------|------------|-------------------------------------|
| [例如：第 4 个项目] | [当前需求] | [为什么 3 个项目不足以满足] |
| [例如：Repository 模式] | [具体问题] | [为什么直接访问数据库不够] |
