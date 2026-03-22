## 发布前检查清单

每次向公众发布新版本的 `specify-cli-zh` 之前，请严格对照以下清单逐项验证：

- [ ] `pyproject.toml` 中的版本号已更新为发布目标的版本号。
- [ ] `CHANGELOG.md` 中已添加新版本的变更说明记录。
- [ ] 本地运行 `specify-zh --version`，确认输出的版本号与 `pyproject.toml` 完全一致。
- [ ] 运行 `specify-zh --help`，确认全局帮助文本中**均无**陈旧的英文品牌名（如 `Specify CLI`）。
- [ ] 全量测试及 Smoke test 已 100% 通过（运行 `make smoke` 及 `pytest`）。
- [ ] `README.md` 项目顶部的 `Version` 或 `Release` 徽章状态正确。
- [ ] `docs/installation.md` 等相关安装指南内描述的命令仍能工作，必要时更新对应的版本说明。
- [ ] 清理和测试所有的文档链接，确认没有任何死链（404）。
- [ ] 在全新的机器或隔离环境中运行 `uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git` 等安装测试并确认工作。
- [ ] GitHub Actions CI（Lint, Test, Smoke, Brand-guard）全部绿灯通过。
