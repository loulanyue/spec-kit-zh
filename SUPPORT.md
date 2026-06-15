<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 支持（Support）

## 如何获取帮助

本项目使用 GitHub Issues 追踪 Bug 和功能请求。在提交新 Issue 之前，请先搜索现有 Issues 避免重复。

### 快速自助参考

| 你的问题 | 推荐文档 |
| --- | --- |
| 首次安装和入门 | [docs/quickstart.md](./docs/quickstart.md) |
| 安装报错、命令找不到 | [docs/troubleshooting.md](./docs/troubleshooting.md) |
| 网络超时、国内访问 | [docs/china-network.md](./docs/china-network.md) |
| 从旧版本升级 | [docs/upgrade.md](./docs/upgrade.md) |
| 本地开发和调试 | [docs/local-development.md](./docs/local-development.md) |
| 规范驱动开发方法论 | [spec-driven.md](./spec-driven.md) |
| 术语解释 | [TERMINOLOGY.md](./TERMINOLOGY.md) |
| 贡献代码 | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| 安全漏洞报告 | [SECURITY.md](./SECURITY.md) |

---

## 提交 Bug 报告

提交 Bug 时，请通过 [GitHub Issue](https://github.com/loulanyue/spec-kit-zh/issues/new) 提交，并尽量包含：

1. **环境信息**：
   ```bash
   specify-zh --version   # CLI 版本
   python --version        # Python 版本
   uv --version            # uv 版本
   uname -a                # 操作系统（macOS/Linux）
   # 或 Windows:
   systeminfo | findstr "OS"
   ```

2. **复现步骤**：能触发问题的最小命令序列

3. **期望行为**：你认为应该发生什么

4. **实际行为**：实际发生了什么，包含完整的错误信息和堆栈跟踪

5. **临时解决方案**：如果你找到了 workaround，请一并描述

---

## 提交功能请求

欢迎功能建议！请通过 [GitHub Issue](https://github.com/loulanyue/spec-kit-zh/issues/new) 提交，并描述：

- 该功能要解决的问题或使用场景
- 你设想的解决方案或接口设计
- 你考虑过的替代方案
- 对现有用户的潜在影响（向后兼容性）

> [!NOTE]
> 重大功能（如新增命令、修改模板结构）建议先通过 Issue 讨论达成共识，再提交 Pull Request，以避免大量返工。

---

## 项目维护状态

**Spec Kit ZH** 处于积极维护状态，由社区协作维护。我们将尽力及时回应支持请求、功能建议和社区问题。

**响应时效参考**：

| 类型 | 目标响应时间 |
| --- | --- |
| 安全漏洞 | 3 个工作日内确认 |
| Bug 报告 | 5 个工作日内初步回复 |
| 功能请求 | 尽力而为，无固定 SLA |
| Pull Request | 7 个工作日内初步审查 |

---

## 贡献代码

如果你想直接贡献修复或功能，欢迎提交 Pull Request！请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解代码规范、测试要求和 PR 流程。
