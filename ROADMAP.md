# Spec Kit ZH Roadmap

本路线图说明项目当前优先级，不构成固定交付日期承诺。具体工作通过 GitHub Issues
和 Milestones 跟踪；优先级会根据上游变化、用户反馈与维护成本调整。

## Now: 稳定 0.9.x 发布线

- 补齐版本发布、变更日志和可复现安装验证，确保代码版本与 Releases 一致。
- 持续跟踪 [github/spec-kit](https://github.com/github/spec-kit)，优先同步功能修复、
  安全修复和代理兼容性变化。
- 完善中文 CLI、模板和文档的一致性检查，避免术语与命令示例漂移。
- 降低国内网络环境、GitHub API 限流和离线初始化对首次使用的影响。

## Next: 扩展前沿智能体协议与兼容体验

- **模型上下文协议 (MCP) 契约生成**：支持直接从规范导出符合 MCP 标准的 Tool JSON Schema 与 Resource 契约，让 Agent 工具声明具备强类型约束。
- **System 2 思考与测试驱动合成 (TDD)**：在规范中嵌入确定性断言门禁，驱动智能体执行“红灯测试 -> 最小代码 -> 绿灯重构”自反思闭环。
- **主流 AI Coding Agents 深度适配**：建立针对 Claude Code、Codex、Cursor、OpenCode 与 Windsurf 的兼容矩阵和端到端 Smoke Test。
- **Prompt 缓存与上下文开销优化**：优化分发规范模板，对齐主流模型的 Prompt Caching 边界，大幅降低长上下文推理延迟与 Token 成本。
- 为新贡献者整理 `good first issue`，提供更小、更容易验证的贡献入口。

## Later: 可持续生态

- 为稳定扩展建立质量分级、兼容性声明与弃用策略。
- 增加真实项目演练和版本升级案例，覆盖新项目与存量项目。
- 在维护容量允许时培养 reviewer 和 release maintainer，降低单人维护风险。

## 如何参与

- Bug 和兼容性问题：使用 Bug Report 表单并提供最小复现。
- 新能力建议：使用 Feature Request 表单，先说明问题和使用场景。
- 计划贡献代码：阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和
  [GOVERNANCE.md](GOVERNANCE.md)，重大改动先在 Issue 中达成共识。
