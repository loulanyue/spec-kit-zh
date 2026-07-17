# 项目治理

## 项目定位

Spec Kit ZH 是 [github/spec-kit](https://github.com/github/spec-kit) 的社区维护中文发行版。
本项目在保留上游核心工作流的基础上，维护中文本地化、国内网络适配、Codex 集成和
面向中文开发者的工程实践。

## 角色与职责

- **Maintainer**：负责路线图、版本发布、安全响应、最终合并和治理决策。
- **Reviewer**：在熟悉的模块内审查设计、实现、测试与文档，可由持续贡献者承担。
- **Contributor**：通过 Issue、PR、文档、测试或问题复现参与项目。

当前最终维护责任由 `@loulanyue` 承担。持续提供高质量审查和贡献的社区成员可以在
双方确认后成为 Reviewer 或 Maintainer。

## 决策方式

1. 小型修复、文档改进和测试增强通过 Pull Request 讨论并合并。
2. 新命令、模板契约变更、兼容性变化和较大重构必须先创建 Issue。
3. 优先寻求共识；无法形成共识时，由 Maintainer 根据兼容性、维护成本和项目定位决定。
4. 涉及上游行为时，优先保持兼容；有意偏离必须在 PR 和 CHANGELOG 中说明。

## 响应目标

这些是维护目标而非商业 SLA：

| 类型 | 首次响应目标 |
| --- | --- |
| 安全漏洞 | 3 个工作日 |
| 可复现 Bug | 5 个工作日 |
| Pull Request | 7 个工作日 |
| 功能建议 | 10 个工作日 |

长时间无活动的 Issue 或 PR 可能被标记为 stale；关闭不代表永久拒绝，可以在有新证据时重开。

## 发布与支持

- 使用语义化版本，并让 `pyproject.toml`、CHANGELOG、Git tag 和 GitHub Release 保持一致。
- PATCH 用于非破坏性修复与文档改进，MINOR 用于向后兼容的新能力，MAJOR 用于破坏性变化。
- 当前发布线和支持范围以 [CHANGELOG.md](CHANGELOG.md) 与 Releases 为准。
- 发布前执行 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)。

## 安全与行为准则

安全问题请遵循 [SECURITY.md](SECURITY.md) 私密报告，不要创建公开 Issue。
参与项目即表示同意遵守项目采用的行为准则和 [CONTRIBUTING.md](CONTRIBUTING.md)。
