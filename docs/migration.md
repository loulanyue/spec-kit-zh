<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 迁移指南

如果您之前使用了英文版的 `spec-kit` 或是早期版本的 `spec-kit-cn`，请参考此指南迁移到最新的 `specify-cli-zh` 工具包。

## 从 `spec-kit`（英文原版）迁移

1. **安装新版本 CLI 工具**
   使用 `uv tool install specify-cli-zh` 或 `pip install specify-cli-zh` 替代原有的 `specify`。运行命令变更为 `specify-zh`。
2. **兼容性**
   原有的项目结构、`.specify/` 目录以及各规范文件（`spec.md`, `plan.md`, `tasks.md`）是**完全兼容**的，不需要您进行手动修改。
3. **更新 Agent 指令**
   由于原版工具包的系统提示词是英文的，我们建议您使用 `specify-zh init . --here` 重新初始化并覆盖 Agent 命令文件。
   > 提示：在覆盖前，您可以使用 `specify-zh init --here --dry-run` 预览将要覆盖的文件，以免丢失您自建的自定义提示词。

## 从 `spec-kit-cn`（早期中文版）迁移

1. **更新 CLI 名称**
   旧版的 CLI 安装包可能名为 `spec-kit-cn`。由于品牌一致性升级，现已更名为 `specify-cli-zh`，执行命令为 `specify-zh`。
2. **更新项目模板**
   您的代码仓库无需做任何数据结构变更。我们建议您在项目根目录运行 `specify-zh init . --force` 来获取最新的中文提问与审查逻辑，让 Agent 的表现更上一层楼。
3. **术语统一**
   新版对规范驱动开发（SDD）的各术语进行了权威界定。请参考项目仓库中的 [TERMINOLOGY.md](../TERMINOLOGY.md)。

## 版本升级（v0.8.x → v0.9.x）

v0.9.x 引入了以下不兼容变更，请在升级后检查：

| 变更点 | v0.8.x 行为 | v0.9.x 行为 | 处理建议 |
|--------|-------------|-------------|----------|
| Codex 提示词命名空间 | `/speckit:command` | `/prompts:speckit-command` | 重新运行 `specify-zh codex-sync` 更新提示词文件 |
| Codex 同步命令 | 无独立命令 | `specify-zh codex-sync` | 初次升级后运行一次 `codex-sync` |
| 回退资源优先级 | 本地 → GitLab → GitHub | 打包资源 → GitLab → 本地 | 无需操作，行为自动生效 |

升级步骤：

```bash
# 卸载旧版本
uv tool uninstall specify-cli-zh

# 安装最新版
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git

# 在已有项目中重新同步 Codex 提示词
cd your-project
specify-zh codex-sync
```

## 文件覆盖指南

以下文件我们**不建议**在此次迁移中删除（请原样保留）：

- 根目录下的所有业务代码
- `.specify/` 目录结构（这是识别项目的核心标志）
- 现有的业务沉淀文件：`spec.md` (需求), `plan.md` (计划), `tasks.md` (任务)

以下文件我们**强烈建议**覆盖为新版：

- `.claude/commands/`, `.cursor/commands/`, 或您正在使用的其他对应的 Agent 系统 prompt 文件集。
- `.codex/prompts/speckit-*.md`（Codex 用户）——运行 `specify-zh codex-sync` 自动更新。

## 回滚方案

如果升级后遇到不可预期的问题，您可以回滚到历史版本：

```bash
# 安装指定版本（例如 v0.8.4）
uv tool install specify-cli-zh==0.8.4

# 或者锁定到指定 Git 提交
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git@<commit-hash>
```
