<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 迁移指南

本文档说明如何将现有项目迁移至最新版本的 `specify-cli-zh`，包括从英文原版、早期中文版和旧版本升级的完整步骤。

---

## 目录

- [从 spec-kit（英文原版）迁移](#从-spec-kit英文原版迁移)
- [从 spec-kit-cn（早期中文版）迁移](#从-spec-kit-cn早期中文版迁移)
- [版本升级：v0.8.x → v0.9.x](#版本升级v08x--v09x)
- [版本升级：v0.9.x → v0.9.4（最新）](#版本升级v09x--v094最新)
- [文件覆盖指南](#文件覆盖指南)
- [迁移前检查清单](#迁移前检查清单)
- [迁移后验证步骤](#迁移后验证步骤)
- [回滚方案](#回滚方案)

---

## 从 `spec-kit`（英文原版）迁移

1. **安装新版本 CLI 工具**

   使用 `uv tool install specify-cli-zh` 替代原有的 `specify`。运行命令变更为 `specify-zh`。

   ```bash
   uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
   ```

2. **兼容性说明**

   原有的项目结构、`.specify/` 目录以及各规范文件（`spec.md`, `plan.md`, `tasks.md`）是**完全兼容**的，不需要手动修改。

3. **更新 Agent 指令**

   由于原版工具包的系统提示词是英文的，建议使用 `specify-zh init . --here` 重新初始化并覆盖 Agent 命令文件：

   ```bash
   # 先备份自定义 constitution.md
   cp .specify/memory/constitution.md /tmp/constitution-backup.md

   # 重新初始化覆盖 Agent 命令文件
   specify-zh init --here --force --ai <your-agent>

   # 还原自定义内容
   mv /tmp/constitution-backup.md .specify/memory/constitution.md
   ```

   > 提示：在覆盖前，可以使用 `specify-zh init --here --dry-run` 预览将要覆盖的文件。

---

## 从 `spec-kit-cn`（早期中文版）迁移

1. **更新 CLI 名称**

   旧版安装包名为 `spec-kit-cn`。由于品牌一致性升级，现已更名为 `specify-cli-zh`，执行命令为 `specify-zh`：

   ```bash
   # 卸载旧版
   uv tool uninstall spec-kit-cn 2>/dev/null || pip uninstall spec-kit-cn -y

   # 安装新版
   uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
   ```

2. **更新项目模板**

   代码仓库无需数据结构变更。建议在项目根目录运行以下命令获取最新的中文审查逻辑：

   ```bash
   specify-zh init --here --force --ai <your-agent>
   ```

3. **术语统一**

   新版对规范驱动开发（SDD）的各术语进行了权威界定，请参考 [TERMINOLOGY.md](../TERMINOLOGY.md)。

---

## 版本升级：v0.8.x → v0.9.x

v0.9.x 引入了以下不兼容变更，升级后请检查：

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

---

## 版本升级：v0.9.x → v0.9.4（最新）

v0.9.4 为**纯向后兼容**的增量改进版，无破坏性变更。建议所有 v0.9.x 用户升级。

### 主要改进

- `docs/troubleshooting.md`：排错条目从 10 个扩展至 16 个，新增 SSL 证书、stale 模板、Codex 命令格式等场景
- `TERMINOLOGY.md`：新增流程术语和工程术语两大章节（19 个新词条）
- `Makefile`：新增 `audit`（安全扫描）、`docs`（文档站构建）、`build` 目标
- `SECURITY.md`：新增响应 SLA、版本支持表、漏洞处理流程
- `spec-driven.md`：新增 FAQ 章节（6 个常见问题）
- `docs/quickstart.md`：新增常见踩坑表格
- `docs/local-development.md`：新增调试技巧章节
- `tests/test_docs_integrity.py`：新增 39 个文档结构验证测试

### 升级命令

```bash
# 升级 CLI
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git --force

# 验证版本
specify-zh --version  # 应显示 0.9.4

# 可选：同步最新模板到现有项目
specify-zh init --here --force --ai <your-agent>
```

> [!NOTE]
> v0.9.4 不修改 `spec.md`、`plan.md`、`tasks.md` 等业务规范文件的格式，升级后这些文件无需变动。

---

## 文件覆盖指南

以下文件**不建议**在迁移中删除（请原样保留）：

- 根目录下的所有业务代码
- `.specify/` 目录结构（这是识别项目的核心标志）
- 现有的业务沉淀文件：`spec.md`（需求）、`plan.md`（计划）、`tasks.md`（任务）
- `specs/` 目录下所有已生成的功能规范目录

以下文件**强烈建议**覆盖为新版：

- `.claude/commands/`、`.cursor/commands/` 或其他 Agent 系统 prompt 文件集
- `.codex/prompts/speckit-*.md`（Codex 用户）——运行 `specify-zh codex-sync` 自动更新
- `.specify/templates/`（命令模板）——运行 `specify-zh init --here --force` 更新

---

## 迁移前检查清单

执行迁移前，请逐项确认：

- [ ] 已提交或备份当前工作分支的所有改动（`git status` 确认干净）
- [ ] 已备份 `.specify/memory/constitution.md`（包含项目自定义章程）
- [ ] 已记录当前版本（`specify-zh --version`）以备回滚参考
- [ ] 已阅读目标版本的 `CHANGELOG.md` 对应条目，了解变更影响
- [ ] 如果使用 Codex：已确认 `~/.codex/prompts/` 目录有写权限

---

## 迁移后验证步骤

迁移完成后，运行以下命令确认一切正常：

```bash
# 1. 验证 CLI 版本
specify-zh --version

# 2. 验证命令帮助文本（确认无陈旧英文品牌名）
specify-zh --help

# 3. 验证工具链检测
specify-zh check

# 4. （Codex 用户）验证提示词已同步
ls ~/.codex/prompts/speckit-*.md

# 5. 运行全量测试（贡献者）
uv run pytest --tb=short -q
```

如遇问题，请参考 [docs/troubleshooting.md](./troubleshooting.md)。

---

## 回滚方案

如果升级后遇到不可预期的问题，可以回滚到历史版本：

```bash
# 安装指定版本（例如 v0.9.3）
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git@v0.9.3

# 或者锁定到指定 Git 提交
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git@<commit-hash>

# 验证回滚成功
specify-zh --version
```

> [!CAUTION]
> 回滚后，如果已在现有项目中运行了 `init --here --force`，部分 Agent 命令文件也会被覆盖为旧版本。如需恢复，可以从 git 历史中恢复对应文件。
