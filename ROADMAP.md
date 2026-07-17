# Spec Kit ZH Roadmap

本路线图说明项目当前优先级，不构成固定交付日期承诺。具体工作通过 GitHub Issues
和 Milestones 跟踪；优先级会根据上游变化、用户反馈与维护成本调整。

## Now: 稳定 0.9.x 发布线

- 补齐版本发布、变更日志和可复现安装验证，确保代码版本与 Releases 一致。
- 持续跟踪 [github/spec-kit](https://github.com/github/spec-kit)，优先同步功能修复、
  安全修复和代理兼容性变化。
- 完善中文 CLI、模板和文档的一致性检查，避免术语与命令示例漂移。
- 降低国内网络环境、GitHub API 限流和离线初始化对首次使用的影响。

## Next: 扩展兼容与贡献体验

- 建立主要 AI coding agents 的兼容矩阵和最小 smoke test。
- 改善 extensions、presets 与自定义 agent 目录的中文使用体验。
- 为新贡献者整理 `good first issue`，提供更小、更容易验证的贡献入口。
- 将上游同步差异、保留的本地增强和迁移影响记录为可审查的同步报告。

## Later: 可持续生态

- 为稳定扩展建立质量分级、兼容性声明与弃用策略。
- 增加真实项目演练和版本升级案例，覆盖新项目与存量项目。
- 在维护容量允许时培养 reviewer 和 release maintainer，降低单人维护风险。

## 如何参与

- Bug 和兼容性问题：使用 Bug Report 表单并提供最小复现。
- 新能力建议：使用 Feature Request 表单，先说明问题和使用场景。
- 计划贡献代码：阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和
  [GOVERNANCE.md](GOVERNANCE.md)，重大改动先在 Issue 中达成共识。
