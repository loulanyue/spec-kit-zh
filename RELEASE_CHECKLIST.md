<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

## 发布前检查清单

每次向公众发布新版本的 `specify-cli-zh` 之前，请严格对照以下清单逐项验证：

---

### 版本与文档

- [ ] `pyproject.toml` 中的版本号已更新为发布目标的版本号。
- [ ] `CHANGELOG.md` 中已添加新版本的变更说明记录，且条目标题格式为 `## [x.y.z] - YYYY-MM-DD`。
- [ ] 本地运行 `specify-zh --version`，确认输出的版本号与 `pyproject.toml` 完全一致。
- [ ] 运行 `specify-zh --help`，确认全局帮助文本中**均无**陈旧的英文品牌名（如 `Specify CLI`）。
- [ ] `TERMINOLOGY.md` 对本次版本新引入的术语已有定义。
- [ ] `docs/migration.md` 已更新（如本次版本包含破坏性变更）。

---

### 测试与代码质量

- [ ] 全量测试及 Smoke test 已 100% 通过（运行 `make smoke` 及 `pytest`）。
- [ ] 运行 `make lint` 确认无任何 ruff 代码风格违规。
- [ ] 运行 `make typecheck` 确认无 mypy 类型错误（允许已知的 `ignore-missing-imports`）。
- [ ] 运行 `make coverage` 确认测试覆盖率不低于 **80%**。
- [ ] 运行 `make audit` 确认无已知高危依赖漏洞。
- [ ] GitHub Actions CI（Lint, Test, Smoke, Brand-guard）全部绿灯通过。

---

### 资产与安装

- [ ] 运行 `.github/workflows/scripts/create-release-packages.sh`（或对应的 `.ps1`），确认当前 Agent 清单的模板包都能生成。
- [ ] 核对发布资产前缀，确认包含 `kiro-cli`、`shai`、`agy`、`tabnine`，且不再出现旧的 `q` 包名。
- [ ] `README.md` 项目顶部的 `Version` 或 `Release` 徽章状态正确。
- [ ] `docs/installation.md` 等相关安装指南内描述的命令仍能工作，必要时更新对应的版本说明。
- [ ] 在全新的机器或隔离环境中验证安装：
  ```bash
  uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
  specify-zh --version
  specify-zh init --help
  ```

---

### 链接与文档质量

- [ ] 清理和测试所有的文档链接，确认没有任何死链（404）。可运行 `make link-check` 进行本地检查。
- [ ] `docs/troubleshooting.md` 涵盖了本次版本新引入的常见错误场景。
- [ ] `docs/quickstart.md` 和 `docs/local-development.md` 与当前版本的行为保持一致。
- [ ] 如果新增了 Codex 提示词或斜杠命令，`docs/upstream-sync.md` 已更新对应说明。

---

### 最终验证与发布

- [ ] 本地 `git log --oneline -5` 确认提交历史整洁，无调试用临时提交。
- [ ] 创建并推送 Git tag，格式为 `vx.y.z`：
  ```bash
  git tag v0.9.4
  git push origin v0.9.4
  ```
- [ ] 在 GitHub 上从该 tag 创建 Release，填写发布说明（可直接复制 `CHANGELOG.md` 对应条目）。
- [ ] 通知团队成员和活跃社区用户（如有）本次发布的主要变更内容。
