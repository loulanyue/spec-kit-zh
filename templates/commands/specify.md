---
description: 从自然语言功能描述创建或更新功能规范。
handoffs: 
  - label: 构建技术计划
    agent: speckit.plan
    prompt: 为该规范创建计划。我正在构建...
  - label: 澄清规范需求
    agent: speckit.clarify
    prompt: 澄清规范需求
    send: true
scripts:
  sh: scripts/bash/create-new-feature.sh "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 "{ARGS}"
---

<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->


## 用户输入

```text
$ARGUMENTS
```

在继续之前，你**必须**考虑用户输入（如果不为空）。

## 语言要求

- 所有面向用户的生成内容，包括 `spec.md`、检查清单、澄清问题、摘要和状态报告，都必须使用简体中文。
- 分支名、文件路径、ID 和其他机器导向标识在兼容性需要时保持 ASCII。
- 如果用户提供英文术语，应在必要时保留原词，并以中文补充说明。

## 概述

用户在触发消息中 `/speckit.specify` 后输入的文本**就是**功能描述。即使下面字面显示 `{ARGS}`，也应假设你始终可以在本次对话中访问该描述。除非用户输入为空，否则不要要求用户重复描述。

基于该功能描述，请执行以下操作：

1. **为功能生成简洁的短名称**（2-4 个单词），作为分支名：
   - 当用户使用中文描述需求时，根据功能含义生成对应的 ASCII 短名称；分支名不得包含中文字符
   - 分析功能描述，提取最有意义的关键词
   - 创建一个 2-4 个单词的短名称，概括功能要点
   - 尽量采用"动词-名词"格式（如 `add-user-auth`、`fix-payment-bug`）
   - 保留技术术语和缩写（OAuth2、API、JWT 等）
   - 名称应简洁，同时足以让人一眼理解功能含义
   - 示例：
     - "我想添加用户身份验证" → `user-auth`
     - "Implement OAuth2 integration for the API" → `oauth2-api-integration`
     - "创建分析仪表板" → `analytics-dashboard`
     - "修复支付处理超时 Bug" → `fix-payment-timeout`

2. **创建功能分支**：运行脚本时传入 `--short-name`（以及 `--json`），**不要**传入 `--number`（脚本会自动检测全局下一个可用编号）：

   - Bash 示例：`{SCRIPT} --json --short-name "user-auth" "Add user authentication"`
   - PowerShell 示例：`{SCRIPT} -Json -ShortName "user-auth" "Add user authentication"`

   **重要说明**：
   - **不要**传入 `--number` — 脚本会自动确定正确的下一个编号
   - 始终包含 JSON 标志（Bash 用 `--json`，PowerShell 用 `-Json`），以便可靠地解析输出
   - 每个功能只运行一次此脚本
   - JSON 输出包含 BRANCH_NAME 和 SPEC_FILE 路径，始终参考这些路径获取实际内容
   - 对于包含单引号的参数（如 "I'm Groot"），使用转义语法：`'I'\''m Groot'`（或尽可能使用双引号）

3. 加载 `templates/spec-template.md` 以了解所需章节结构。

4. **遵循以下执行流程**：

    1. 从用户输入中解析功能描述
       若为空：报错"未提供功能描述"
    2. 从描述中提取关键概念
       识别：参与者、操作、数据、约束条件
    3. 对于不明确的内容：
       - 基于上下文和行业惯例做出合理推断
       - 仅在以下情况下标记 `[NEEDS CLARIFICATION: 具体问题]`：
         - 该选择对功能范围或用户体验有重大影响
         - 存在多种合理解读，且各自有不同含义
         - 没有合理的默认值
       - **限制：最多 3 个 [NEEDS CLARIFICATION] 标记**
       - 按影响程度排列澄清优先级：范围 > 安全/隐私 > 用户体验 > 技术细节
    4. 填写用户场景与测试章节
       若无法确定用户流程：报错"无法确定用户场景"
    5. 生成功能需求
       每条需求必须可测试
       对未明确的细节使用合理默认值（在"假设"章节中记录）
    6. 定义成功标准
       创建可量化、与技术无关的结果指标
       同时包含定量指标（时间、性能、数量）和定性指标（用户满意度、任务完成率）
       每条标准无需了解实现细节即可验证
    7. 识别关键实体（如涉及数据）
    8. 返回：成功（规范已可进入规划阶段）

5. 使用模板结构将规范写入 SPEC_FILE，用功能描述中的具体内容替换占位符，同时保持章节顺序和标题不变。

6. **规范质量验证**：初稿完成后，对照质量标准进行验证：

   a. **创建规范质量检查清单**：在 `FEATURE_DIR/checklists/requirements.md` 生成一个检查清单文件，结构如下：

      ```markdown
      # 规范质量检查清单：[功能名称]
      
      **目的**：在进入规划阶段前验证规范的完整性与质量
      **创建时间**：[DATE]
      **功能**：[spec.md 链接]
      
      ## 内容质量
      
      - [ ] 无实现细节（无编程语言、框架、API 引用）
      - [ ] 聚焦用户价值与业务需求
      - [ ] 面向非技术干系人撰写
      - [ ] 所有必填章节均已完成
      
      ## 需求完整性
      
      - [ ] 无 [NEEDS CLARIFICATION] 标记残留
      - [ ] 需求可测试且无歧义
      - [ ] 成功标准可量化
      - [ ] 成功标准与技术无关（无实现细节）
      - [ ] 所有验收场景已定义
      - [ ] 边界情况已识别
      - [ ] 范围边界清晰
      - [ ] 依赖项与假设已识别
      
      ## 功能就绪度
      
      - [ ] 所有功能需求有明确的验收标准
      - [ ] 用户场景覆盖主要流程
      - [ ] 功能满足成功标准中定义的可量化结果
      - [ ] 规范中无实现细节泄漏
      
      ## 备注
      
      - 标记为未完成的条目需要在执行 `/speckit.clarify` 或 `/speckit.plan` 之前更新规范
      ```

   b. **执行验证检查**：对照每条检查项审查规范：
      - 对每条项目判断通过或失败
      - 记录发现的具体问题（引用相关规范章节）

   c. **处理验证结果**：

      - **若所有条目通过**：将检查清单标记为完成，继续执行步骤 7

      - **若有条目失败（不含 [NEEDS CLARIFICATION]）**：
        1. 列出失败条目及具体问题
        2. 更新规范以解决每个问题
        3. 重新验证直到所有条目通过（最多 3 次迭代）
        4. 若 3 次迭代后仍有失败，在检查清单备注中记录剩余问题并提示用户

      - **若存在 [NEEDS CLARIFICATION] 标记**：
        1. 提取规范中所有 `[NEEDS CLARIFICATION: ...]` 标记
        2. **数量检查**：若超过 3 个标记，仅保留最关键的 3 个（按范围/安全/用户体验影响排序），其余采用合理推断
        3. 对每个需澄清的问题（最多 3 个），以如下格式向用户展示选项：

           ```markdown
           ## 问题 [N]：[主题]
           
           **上下文**：[引用相关规范章节]
           
           **需要了解的内容**：[来自 NEEDS CLARIFICATION 标记的具体问题]
           
           **建议答案**：
           
           | 选项 | 答案 | 影响说明 |
           |------|------|---------|
           | A    | [第一个建议答案] | [对功能意味着什么] |
           | B    | [第二个建议答案] | [对功能意味着什么] |
           | C    | [第三个建议答案] | [对功能意味着什么] |
           | 自定义 | 提供您自己的答案 | [说明如何提供自定义输入] |
           
           **您的选择**：_[等待用户回复]_
           ```

        4. **重要 — 表格格式**：确保 Markdown 表格格式正确：
           - 使用一致的间距，竖线对齐
           - 每个单元格内容周围留有空格：`| Content |` 而非 `|Content|`
           - 表头分隔符至少使用 3 个破折号：`|--------|`
           - 在 Markdown 预览中确认表格渲染正确
        5. 按顺序为问题编号（Q1、Q2、Q3，最多 3 个）
        6. 等待用户回复之前，一次性展示所有问题
        7. 等待用户对所有问题作出回应（例如："Q1: A，Q2: 自定义 - [详情]，Q3: B"）
        8. 用用户选择或提供的答案替换规范中每个 [NEEDS CLARIFICATION] 标记
        9. 所有澄清解决后，重新执行验证

   d. **更新检查清单**：每次验证迭代后，用当前通过/失败状态更新检查清单文件

7. 汇报完成情况，包括分支名、规范文件路径、检查清单结果，以及进入下一阶段（`/speckit.clarify` 或 `/speckit.plan`）的就绪状态。

**注意：** 脚本会在写入前创建并切换到新分支，并初始化规范文件。

## 总体指引

## 简明指引

- 聚焦用户**需要什么**以及**为什么需要**。
- 避免描述**如何实现**（不涉及技术栈、API、代码结构）。
- 面向业务干系人撰写，而非开发者。
- **不要**在规范中内嵌检查清单，检查清单由独立命令生成。

### 章节要求

- **必填章节**：每个功能必须完成
- **可选章节**：仅在与功能相关时包含
- 若某章节不适用，请完全删除（不要留"N/A"）

### AI 生成规范时的注意事项

从用户提示创建规范时：

1. **做出合理推断**：利用上下文、行业标准和常见模式填补空白
2. **记录假设**：在"假设"章节中记录合理的默认选择
3. **限制澄清数量**：最多 3 个 [NEEDS CLARIFICATION] 标记，仅用于以下关键决策：
   - 对功能范围或用户体验有重大影响
   - 存在多种合理解读且各有不同含义
   - 没有任何合理的默认值
4. **按优先级排列澄清**：范围 > 安全/隐私 > 用户体验 > 技术细节
5. **像测试人员一样思考**：每个模糊的需求都应该在"可测试且无歧义"检查项中失败
6. **常见需要澄清的领域**（仅在没有合理默认值时）：
   - 功能范围与边界（包含/排除特定用例）
   - 用户类型与权限（若存在多种合理解读）
   - 安全/合规要求（当涉及法律或财务影响时）

**合理默认值示例**（无需询问这些内容）：

- 数据保留：该领域的行业标准实践
- 性能目标：标准 Web/移动应用期望值（除非另有说明）
- 错误处理：带适当回退的用户友好提示
- 认证方式：Web 应用的标准 Session 或 OAuth2
- 集成模式：使用项目适合的模式（Web 服务用 REST/GraphQL，库用函数调用，工具用 CLI 参数等）

### 成功标准指引

成功标准必须：

1. **Measurable**: Include specific metrics (time, percentage, count, rate)
2. **Technology-agnostic**: No mention of frameworks, languages, databases, or tools
3. **User-focused**: Describe outcomes from user/business perspective, not system internals
4. **Verifiable**: Can be tested/validated without knowing implementation details

**Good examples**:

- "Users can complete checkout in under 3 minutes"
- "System supports 10,000 concurrent users"
- "95% of searches return results in under 1 second"
- "Task completion rate improves by 40%"

**Bad examples** (implementation-focused):

- "API response time is under 200ms" (too technical, use "Users see results instantly")
- "Database can handle 1000 TPS" (implementation detail, use user-facing metric)
- "React components render efficiently" (framework-specific)
- "Redis cache hit rate above 80%" (technology-specific)
