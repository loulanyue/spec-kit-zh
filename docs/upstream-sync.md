<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 上游版本同步指南

本文档描述 `spec-kit-zh` 与上游 `spec-kit` 之间的版本跟踪与同步策略。

---

## 同步触发机制

上游版本同步检测通过 `.github/workflows/upstream-sync.yml` 自动运行：

- **定时检测**：每周一 UTC 03:00（北京时间 11:00）
- **手动触发**：在 GitHub Actions 页面手动触发 `upstream-sync` workflow

当检测到上游新版本时，系统会自动创建 GitHub Issue，标记为 `上游同步` 标签，提醒维护者处理。

---

## 版本号跟踪规则

```
spec-kit-zh 版本格式：MAJOR.MINOR.PATCH

MAJOR  跟随上游大版本（如上游发布 v2.0 → 本仓库升至 v2.0.x）
MINOR  本仓库独立递增（每个中文化改进版本 / 批量 Bug 修复）
PATCH  本仓库独立递增（紧急 Bug 修复 / 文档修订）
```

**示例**：
- 上游发布 `v1.5.0` → 本仓库下一版本为 `v1.5.0` 或 `v1.5.1`（若有额外修复）
- 本仓库中文化改进 → 版本从 `v1.5.1` 升至 `v1.6.0`，不等待上游更新

---

## 同步处理流程

收到自动创建的同步 Issue 后，维护者按以下步骤操作：

### 第 1 步：了解上游变更

```bash
# 添加上游作为远端（首次）
git remote add upstream https://github.com/microsoft/spec-kit.git

# 获取上游最新变更
git fetch upstream

# 查看差异
git log HEAD..upstream/main --oneline
git diff HEAD upstream/main -- templates/ src/
```

### 第 2 步：分类变更

对比上游变更，按以下优先级分类：

| 变更类型 | 处理方式 |
|----------|---------|
| 功能性增强（新命令、新模板、逻辑修复） | **cherry-pick**，并追加中文翻译 |
| Bug 修复 | **cherry-pick**，保留原有修复 |
| 纯英文文案变更（提示语、注释） | **忽略**，保留中文本地化版本 |
| 架构重构 | **评估**，若影响较大，专开 PR 讨论 |

### 第 3 步：应用功能性变更

```bash
# 从上游 cherry-pick 特定提交
git cherry-pick <commit-hash>

# 或合并特定文件
git checkout upstream/main -- templates/commands/new-command.md
```

### 第 4 步：中文化处理

对 cherry-pick 的内容进行中文化：

1. 翻译新增的英文 UI 文案和注释
2. 对照 [TERMINOLOGY.md](../TERMINOLOGY.md) 统一术语
3. 确保模板文件符合 P4-22 标准（正文为中文，代码/命令保留英文）

### 第 5 步：更新版本与日志

```bash
# 更新 pyproject.toml 版本号
vim pyproject.toml

# 添加 CHANGELOG 条目
vim CHANGELOG.md

# 更新上游同步版本记录
echo "v1.5.0" > .upstream-sync-version
```

### 第 6 步：验证与发布

```bash
# 运行 smoke test
make smoke

# 运行全量测试
make test

# 推送并提 PR
git push origin sync/upstream-v1.5.0
```

---

## 冲突处理优先级

当上游变更与本仓库中文化内容冲突时：

```
中文化内容 > 上游原文

即：优先保留中文版本，在中文版基础上应用上游的功能性变更。
```

**原则**：
- 不回退已完成的中文化工作
- 上游增加新章节 → 翻译后追加
- 上游删除章节 → 评估本仓库是否也应删除（若已有中文用户依赖，可保留并标注）

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `.upstream-sync-version` | 记录最后一次同步的上游版本号 |
| `.github/workflows/upstream-sync.yml` | 自动检测 workflow |
| `CHANGELOG.md` | 记录每次同步引入的变更 |
| `TERMINOLOGY.md` | 中文术语对照表，同步时参考 |
