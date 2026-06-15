<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 安全政策（Security Policy）

感谢您帮助维护 spec-kit-zh 的安全。

---

## 支持的版本

我们仅对最新主分支（`main`）的最新发布版本提供安全修复支持。

| 版本 | 支持状态 |
| --- | --- |
| 最新 `main` 分支 | ✅ 持续支持 |
| 旧版本 | ❌ 不再支持 |

如果您使用的是旧版本并发现漏洞，请先升级到最新版后确认问题是否仍然存在。

---

## 报告安全漏洞

**请勿通过公开的 GitHub Issues、Discussions 或 Pull Requests 报告安全漏洞。**

如果您发现任何安全漏洞，请通过以下方式进行负责任披露（Coordinated Disclosure）：

- 发送邮件至：`opensource-security[@]github.com`
- 或通过 [GitHub Security Advisories](https://github.com/loulanyue/spec-kit-zh/security/advisories/new) 私密报告

### 报告时请尽量包含以下信息

- 漏洞类型（如：路径遍历、不当权限提升、依赖注入等）
- 漏洞所在的源文件路径（含行号或函数名）
- 受影响的版本（tag、branch 或 commit SHA）
- 触发漏洞所需的特殊配置（如有）
- 最小化复现步骤（step-by-step）
- 概念验证代码或利用示例（如可提供）
- 漏洞影响评估（CVSS 评分或文字描述）

以上信息将帮助我们更快速地对报告进行分类处理。

---

## 处理流程与时效

1. **确认收到**：我们将在收到报告后 **3 个工作日**内发送确认回复。
2. **初步评估**：在 **7 个工作日**内完成初步影响评估并告知您结论。
3. **修复与发布**：根据漏洞严重程度，修复时间从数小时到数周不等。修复完成后将通知报告者。
4. **公开披露**：修复版本发布后，我们会在 GitHub Security Advisories 中公开披露细节，并在 `CHANGELOG.md` 中注明安全修复条目。

---

## 依赖安全

`specify-cli-zh` 的直接运行时依赖包括 `typer`、`rich`、`httpx`、`pyyaml`、`truststore` 等。我们会通过以下方式持续监控依赖安全：

- CI 流水线中集成 `pip-audit` 扫描（`make audit`）
- GitHub Dependabot 自动依赖更新提醒

如果您在依赖项中发现漏洞，也请通过上述渠道告知我们。

---

## 免责声明

本项目是开源社区工具，不在 GitHub Bug Bounty 计划范围内，因此不提供漏洞奖励。但我们会认真对待每一份安全报告，并确保将您的发现转交给相应的维护者处理。

参见 [GitHub Safe Harbor Policy](https://docs.github.com/en/site-policy/security-policies/github-bug-bounty-program-legal-safe-harbor#1-safe-harbor-terms)。
