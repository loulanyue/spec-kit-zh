<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# Spec Kit 扩展系统

[Spec Kit](https://github.com/loulanyue/spec-kit-zh) 的扩展系统，用于在不膨胀核心框架的前提下增加新能力。

## 扩展目录

Spec Kit 提供两个用途不同的目录文件：

### 你的目录（`catalog.json`）

- **用途**：Spec Kit CLI 默认使用的上游扩展目录
- **默认状态**：上游项目默认保持为空，通常由你或你的组织在 fork/copy 中填入受信任的扩展
- **上游位置**：托管在 GitHub 的 spec-kit 仓库中的 `extensions/catalog.json`
- **CLI 默认行为**：除非显式覆盖，否则 `specify extension` 命令默认使用上游目录 URL
- **组织目录**：你可以将 `SPECKIT_CATALOG_URL` 指向组织自己的 fork 或托管目录 JSON，以替代默认上游目录
- **自定义方式**：可将社区目录中的条目复制到你的组织目录中，也可以直接加入自定义扩展

**覆盖示例：**
```bash
# 使用你们组织自己的目录覆盖默认上游目录
export SPECKIT_CATALOG_URL="https://your-org.com/spec-kit/catalog.json"
specify extension search  # 此时会使用组织目录，而不是默认上游目录
```

### 社区参考目录（`catalog.community.json`）

- **用途**：浏览社区贡献的可用扩展
- **状态**：活跃使用中，包含社区提交的扩展
- **位置**：`extensions/catalog.community.json`
- **使用方式**：作为发现可用扩展的参考目录
- **贡献方式**：接受社区通过 Pull Request 提交

## 工作方式

## 让扩展可用

你可以自行决定团队能发现和安装哪些扩展：

### 方式一：维护精选目录（推荐用于组织团队）

将已批准扩展写入 `catalog.json`：

1. **发现** 扩展来源：
   - 浏览 `catalog.community.json` 中的社区扩展
   - 查找组织内部仓库中的私有扩展
   - 从可信第三方发现扩展
2. **评审** 扩展，并决定哪些要开放给团队使用
3. **加入** 这些扩展条目到你的 `catalog.json`
4. **团队成员** 就可以发现并安装它们：
   - `specify extension search` 会展示你的精选目录
   - `specify extension add <name>` 会从你的目录安装扩展

**优点**：可完全控制可用扩展范围，保持团队一致性，并适配组织审批流程

**示例**：把 `catalog.community.json` 中的某个条目复制到 `catalog.json`，之后团队成员就可以通过名称发现并安装它。

### 方式二：直接使用 URL（适合临时场景）

跳过目录维护，团队成员直接通过 URL 安装：

```bash
specify extension add --from https://github.com/org/spec-kit-ext/archive/refs/tags/v1.0.0.zip
```

**优点**：适合一次性测试或私有扩展，速度快

**代价**：除非你同时把它加入 `catalog.json`，否则其他团队成员无法在 `specify extension search` 中看到这类扩展。

## 可用的社区扩展

以下社区贡献扩展当前收录于 [`catalog.community.json`](catalog.community.json)：

| 扩展 | 用途 | URL |
|------|------|-----|
| Azure DevOps Integration | Sync user stories and tasks to Azure DevOps work items using OAuth authentication | [spec-kit-azure-devops](https://github.com/pragya247/spec-kit-azure-devops) |
| Cleanup Extension | Post-implementation quality gate that reviews changes, fixes small issues (scout rule), creates tasks for medium issues, and generates analysis for large issues | [spec-kit-cleanup](https://github.com/dsrednicki/spec-kit-cleanup) |
| Fleet Orchestrator | Orchestrate a full feature lifecycle with human-in-the-loop gates across all SpecKit phases | [spec-kit-fleet](https://github.com/sharathsatish/spec-kit-fleet) |
| Jira Integration | Create Jira Epics, Stories, and Issues from spec-kit specifications and task breakdowns with configurable hierarchy and custom field support | [spec-kit-jira](https://github.com/mbachorik/spec-kit-jira) |
| Ralph Loop | Autonomous implementation loop using AI agent CLI | [spec-kit-ralph](https://github.com/Rubiss/spec-kit-ralph) |
| Retrospective Extension | Post-implementation retrospective with spec adherence scoring, drift analysis, and human-gated spec updates | [spec-kit-retrospective](https://github.com/emi-dm/spec-kit-retrospective) |
| Review Extension | Post-implementation comprehensive code review with specialized agents for code quality, comments, tests, error handling, type design, and simplification | [spec-kit-review](https://github.com/ismaelJimenez/spec-kit-review) |
| Spec Sync | Detect and resolve drift between specs and implementation. AI-assisted resolution with human approval | [spec-kit-sync](https://github.com/bgervin/spec-kit-sync) |
| Understanding | Automated requirements quality analysis — 31 deterministic metrics against IEEE/ISO standards with experimental energy-based ambiguity detection | [understanding](https://github.com/Testimonial/understanding) |
| V-Model Extension Pack | Enforces V-Model paired generation of development specs and test specs with full traceability | [spec-kit-v-model](https://github.com/leocamello/spec-kit-v-model) |
| Verify Extension | Post-implementation quality gate that validates implemented code against specification artifacts | [spec-kit-verify](https://github.com/ismaelJimenez/spec-kit-verify) |


## 添加你的扩展

### 提交流程

如果你想把自己的扩展加入社区目录：

1. 按照 [扩展开发指南](EXTENSION-DEVELOPMENT-GUIDE.md) **准备扩展**
2. 为扩展 **创建 GitHub Release**
3. 提交 **Pull Request**，内容包括：
   - 将扩展加入 `extensions/catalog.community.json`
   - 在本 README 的“可用社区扩展”表格中补上你的扩展
4. **等待审核**，维护者会在符合标准后合并

详细步骤请参考 [扩展发布指南](EXTENSION-PUBLISHING-GUIDE.md)。

### 提交检查清单

在提交前，请确认：

- ✅ Valid `extension.yml` manifest
- ✅ Complete README with installation and usage instructions
- ✅ LICENSE file included
- ✅ GitHub release created with semantic version (e.g., v1.0.0)
- ✅ Extension tested on a real project
- ✅ All commands working as documented

## 安装扩展

当扩展已经可用（无论是通过你的目录还是直接 URL）后，可以这样安装：

```bash
# 从你的精选目录安装（按名称）
specify extension search                  # 查看目录里有哪些扩展
specify extension add <extension-name>    # 按名称安装

# 直接通过 URL 安装（绕过目录）
specify extension add --from https://github.com/<org>/<repo>/archive/refs/tags/<version>.zip

# 查看已安装扩展
specify extension list
```

更多说明请参考 [扩展用户指南](EXTENSION-USER-GUIDE.md)。
