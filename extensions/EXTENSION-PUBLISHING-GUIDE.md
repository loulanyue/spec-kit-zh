<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 扩展发布指南

本指南说明如何将你的扩展发布到 Spec Kit 扩展目录中，使其能够被 `specify extension search` 发现。

## 目录

1. [前置条件](#前置条件)
2. [准备扩展](#准备扩展)
3. [提交到目录](#提交到目录)
4. [验证流程](#验证流程)
5. [发布流程](#发布流程)
6. [最佳实践](#最佳实践)

---

## 前置条件

在发布扩展之前，请确保你已经具备以下条件：

1. **有效扩展**：拥有可运行、且 `extension.yml` 有效的扩展
2. **Git 仓库**：扩展托管在 GitHub（或其他公开 Git 托管平台）
3. **文档**：README.md 中包含安装与使用说明
4. **许可证**：带有开源许可证文件（如 MIT、Apache 2.0）
5. **版本管理**：采用语义化版本（例如 1.0.0）
6. **测试**：扩展已在真实项目中测试过

---

## 准备扩展

### 1. 扩展目录结构

请确保扩展符合标准目录结构：

```text
your-extension/
├── extension.yml              # 必需：扩展清单
├── README.md                  # 必需：文档
├── LICENSE                    # 必需：许可证文件
├── CHANGELOG.md               # 推荐：版本历史
├── .gitignore                 # 推荐：Git ignore 规则
│
├── commands/                  # 扩展命令
│   ├── command1.md
│   └── command2.md
│
├── config-template.yml        # 配置模板（如有需要）
│
└── docs/                      # 额外文档
    ├── usage.md
    └── examples/
```

### 2. 校验 extension.yml

Verify your manifest is valid:

```yaml
schema_version: "1.0"

extension:
  id: "your-extension"           # 唯一的小写连字符 ID
  name: "Your Extension Name"    # 人类可读名称
  version: "1.0.0"               # 语义化版本
  description: "Brief description (one sentence)"
  author: "Your Name or Organization"
  repository: "https://github.com/your-org/spec-kit-your-extension"
  license: "MIT"
  homepage: "https://github.com/your-org/spec-kit-your-extension"

requires:
  speckit_version: ">=0.1.0"    # 所需 spec-kit 版本

provides:
  commands:                      # 列出所有命令
    - name: "speckit.your-extension.command"
      file: "commands/command.md"
      description: "Command description"

tags:                            # 2-5 个相关标签
  - "category"
  - "tool-name"
```

**校验清单：**

- ✅ `id` 只使用小写字母和连字符（不能有下划线、空格或特殊字符）
- ✅ `version` 符合语义化版本规则（X.Y.Z）
- ✅ `description` 简洁明确（建议不超过 100 字符）
- ✅ `repository` URL 有效且可公开访问
- ✅ 所有命令文件都存在于扩展目录中
- ✅ 标签使用小写，且具备描述性

### 3. 创建 GitHub Release

为当前扩展版本创建 GitHub Release：

```bash
# 打 tag
git tag v1.0.0
git push origin v1.0.0

// 在 GitHub 上创建 Release
# Go to: https://github.com/your-org/spec-kit-your-extension/releases/new
# - Tag: v1.0.0
# - Title: v1.0.0 - Release Name
# - Description: Changelog/release notes
```

生成的 Release 压缩包 URL 形如：

```text
https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.0.0.zip
```

### 4. 测试安装

验证用户是否可以从你的 Release 安装扩展：

```bash
# 测试本地开发安装
specify extension add --dev /path/to/your-extension

# 测试从 GitHub 压缩包安装
specify extension add --from https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.0.0.zip
```

---

## 提交到目录

### 理解目录机制

Spec Kit 使用双目录系统。关于目录如何工作的详细说明，请参考主文档 [Extensions README](README.md#扩展目录)。

**对于扩展发布来说**：所有社区扩展都应加入 `catalog.community.json`。用户会先浏览这个目录，再把自己信任的扩展复制到自己的 `catalog.json` 中。

### 1. Fork spec-kit 仓库

```bash
# 先在 GitHub 上 fork
# https://github.com/loulanyue/spec-kit-zh/fork

# 再克隆你的 fork
git clone https://github.com/YOUR-USERNAME/spec-kit.git
cd spec-kit
```

### 2. 将扩展加入社区目录

编辑 `extensions/catalog.community.json`，加入你的扩展：

```json
{
  "schema_version": "1.0",
  "updated_at": "2026-01-28T15:54:00Z",
  "catalog_url": "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json",
  "extensions": {
    "your-extension": {
      "name": "Your Extension Name",
      "id": "your-extension",
      "description": "Brief description of your extension",
      "author": "Your Name",
      "version": "1.0.0",
      "download_url": "https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.0.0.zip",
      "repository": "https://github.com/your-org/spec-kit-your-extension",
      "homepage": "https://github.com/your-org/spec-kit-your-extension",
      "documentation": "https://github.com/your-org/spec-kit-your-extension/blob/main/docs/",
      "changelog": "https://github.com/your-org/spec-kit-your-extension/blob/main/CHANGELOG.md",
      "license": "MIT",
      "requires": {
        "speckit_version": ">=0.1.0",
        "tools": [
          {
            "name": "required-mcp-tool",
            "version": ">=1.0.0",
            "required": true
          }
        ]
      },
      "provides": {
        "commands": 3,
        "hooks": 1
      },
      "tags": [
        "category",
        "tool-name",
        "feature"
      ],
      "verified": false,
      "downloads": 0,
      "stars": 0,
      "created_at": "2026-01-28T00:00:00Z",
      "updated_at": "2026-01-28T00:00:00Z"
    }
  }
}
```

**注意：**

- 将 `verified` 设为 `false`（由维护者审核后再更新）
- 将 `downloads` 和 `stars` 设为 `0`（后续可自动更新）
- `created_at` 和 `updated_at` 使用当前时间戳
- 顶层的 `updated_at` 也要同步更新为当前时间

### 3. 更新 Extensions README

将你的扩展加入 `extensions/README.md` 的“可用社区扩展”表格中：

```markdown
| Your Extension Name | Brief description of what it does | [repo-name](https://github.com/your-org/spec-kit-your-extension) |
```

请按字母顺序插入你的扩展。

### 4. 提交 Pull Request

```bash
# Create a branch
git checkout -b add-your-extension

# Commit your changes
git add extensions/catalog.community.json extensions/README.md
git commit -m "Add your-extension to community catalog

- Extension ID: your-extension
- Version: 1.0.0
- Author: Your Name
- Description: Brief description
"

# Push to your fork
git push origin add-your-extension

# Create Pull Request on GitHub
# https://github.com/loulanyue/spec-kit-zh/compare
```

**Pull Request Template**:

```markdown
## Extension Submission

**Extension Name**: Your Extension Name
**Extension ID**: your-extension
**Version**: 1.0.0
**Author**: Your Name
**Repository**: https://github.com/your-org/spec-kit-your-extension

### Description
Brief description of what your extension does.

### Checklist
- [x] Valid extension.yml manifest
- [x] README.md with installation and usage docs
- [x] LICENSE file included
- [x] GitHub release created (v1.0.0)
- [x] Extension tested on real project
- [x] All commands working
- [x] No security vulnerabilities
- [x] Added to extensions/catalog.community.json
- [x] Added to extensions/README.md Available Extensions table

### Testing
Tested on:
- macOS 13.0+ with spec-kit 0.1.0
- Project: [Your test project]

### Additional Notes
Any additional context or notes for reviewers.
```

---

## Verification Process

### What Happens After Submission

1. **Automated Checks** (if available):
   - Manifest validation
   - Download URL accessibility
   - Repository existence
   - License file presence

2. **Manual Review**:
   - Code quality review
   - Security audit
   - Functionality testing
   - Documentation review

3. **Verification**:
   - If approved, `verified: true` is set
   - Extension appears in `specify extension search --verified`

### Verification Criteria

To be verified, your extension must:

✅ **Functionality**:

- Works as described in documentation
- All commands execute without errors
- No breaking changes to user workflows

✅ **Security**:

- No known vulnerabilities
- No malicious code
- Safe handling of user data
- Proper validation of inputs

✅ **Code Quality**:

- Clean, readable code
- Follows extension best practices
- Proper error handling
- Helpful error messages

✅ **Documentation**:

- Clear installation instructions
- Usage examples
- Troubleshooting section
- Accurate description

✅ **Maintenance**:

- Active repository
- Responsive to issues
- Regular updates
- Semantic versioning followed

### Typical Review Timeline

- **Automated checks**: Immediate (if implemented)
- **Manual review**: 3-7 business days
- **Verification**: After successful review

---

## Release Workflow

### Publishing New Versions

When releasing a new version:

1. **Update version** in `extension.yml`:

   ```yaml
   extension:
     version: "1.1.0"  # Updated version
   ```

2. **Update CHANGELOG.md**:

   ```markdown
   ## [1.1.0] - 2026-02-15

   ### Added
   - New feature X

   ### Fixed
   - Bug fix Y
   ```

3. **Create GitHub release**:

   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   # Create release on GitHub
   ```

4. **Update catalog**:

   ```bash
   # Fork spec-kit repo (or update existing fork)
   cd spec-kit

   # Update extensions/catalog.json
   jq '.extensions["your-extension"].version = "1.1.0"' extensions/catalog.json > tmp.json && mv tmp.json extensions/catalog.json
   jq '.extensions["your-extension"].download_url = "https://github.com/your-org/spec-kit-your-extension/archive/refs/tags/v1.1.0.zip"' extensions/catalog.json > tmp.json && mv tmp.json extensions/catalog.json
   jq '.extensions["your-extension"].updated_at = "2026-02-15T00:00:00Z"' extensions/catalog.json > tmp.json && mv tmp.json extensions/catalog.json
   jq '.updated_at = "2026-02-15T00:00:00Z"' extensions/catalog.json > tmp.json && mv tmp.json extensions/catalog.json

   # Submit PR
   git checkout -b update-your-extension-v1.1.0
   git add extensions/catalog.json
   git commit -m "Update your-extension to v1.1.0"
   git push origin update-your-extension-v1.1.0
   ```

5. **Submit update PR** with changelog in description

---

## Best Practices

### Extension Design

1. **Single Responsibility**: Each extension should focus on one tool/integration
2. **Clear Naming**: Use descriptive, unambiguous names
3. **Minimal Dependencies**: Avoid unnecessary dependencies
4. **Backward Compatibility**: Follow semantic versioning strictly

### Documentation

1. **README.md Structure**:
   - Overview and features
   - Installation instructions
   - Configuration guide
   - Usage examples
   - Troubleshooting
   - Contributing guidelines

2. **Command Documentation**:
   - Clear description
   - Prerequisites listed
   - Step-by-step instructions
   - Error handling guidance
   - Examples

3. **Configuration**:
   - Provide template file
   - Document all options
   - Include examples
   - Explain defaults

### Security

1. **Input Validation**: Validate all user inputs
2. **No Hardcoded Secrets**: Never include credentials
3. **Safe Dependencies**: Only use trusted dependencies
4. **Audit Regularly**: Check for vulnerabilities

### Maintenance

1. **Respond to Issues**: Address issues within 1-2 weeks
2. **Regular Updates**: Keep dependencies updated
3. **Changelog**: Maintain detailed changelog
4. **Deprecation**: Give advance notice for breaking changes

### Community

1. **License**: Use permissive open-source license (MIT, Apache 2.0)
2. **Contributing**: Welcome contributions
3. **Code of Conduct**: Be respectful and inclusive
4. **Support**: Provide ways to get help (issues, discussions, email)

---

## FAQ

### Q: Can I publish private/proprietary extensions?

A: The main catalog is for public extensions only. For private extensions:

- Host your own catalog.json file
- Users add your catalog: `specify extension add-catalog https://your-domain.com/catalog.json`
- Not yet implemented - coming in Phase 4

### Q: How long does verification take?

A: Typically 3-7 business days for initial review. Updates to verified extensions are usually faster.

### Q: What if my extension is rejected?

A: You'll receive feedback on what needs to be fixed. Make the changes and resubmit.

### Q: Can I update my extension anytime?

A: Yes, submit a PR to update the catalog with your new version. Verified status may be re-evaluated for major changes.

### Q: Do I need to be verified to be in the catalog?

A: No, unverified extensions are still searchable. Verification just adds trust and visibility.

### Q: Can extensions have paid features?

A: Extensions should be free and open-source. Commercial support/services are allowed, but core functionality must be free.

---

## Support

- **Catalog Issues**: <https://github.com/statsperform/spec-kit/issues>
- **Extension Template**: <https://github.com/statsperform/spec-kit-extension-template> (coming soon)
- **Development Guide**: See EXTENSION-DEVELOPMENT-GUIDE.md
- **Community**: Discussions and Q&A

---

## Appendix: Catalog Schema

### Complete Catalog Entry Schema

```json
{
  "name": "string (required)",
  "id": "string (required, unique)",
  "description": "string (required, <200 chars)",
  "author": "string (required)",
  "version": "string (required, semver)",
  "download_url": "string (required, valid URL)",
  "repository": "string (required, valid URL)",
  "homepage": "string (optional, valid URL)",
  "documentation": "string (optional, valid URL)",
  "changelog": "string (optional, valid URL)",
  "license": "string (required)",
  "requires": {
    "speckit_version": "string (required, version specifier)",
    "tools": [
      {
        "name": "string (required)",
        "version": "string (optional, version specifier)",
        "required": "boolean (default: false)"
      }
    ]
  },
  "provides": {
    "commands": "integer (optional)",
    "hooks": "integer (optional)"
  },
  "tags": ["array of strings (2-10 tags)"],
  "verified": "boolean (default: false)",
  "downloads": "integer (auto-updated)",
  "stars": "integer (auto-updated)",
  "created_at": "string (ISO 8601 datetime)",
  "updated_at": "string (ISO 8601 datetime)"
}
```

### Valid Tags

Recommended tag categories:

- **Integration**: jira, linear, github, gitlab, azure-devops
- **Category**: issue-tracking, vcs, ci-cd, documentation, testing
- **Platform**: atlassian, microsoft, google
- **Feature**: automation, reporting, deployment, monitoring

Use 2-5 tags that best describe your extension.

---

*Last Updated: 2026-01-28*
*Catalog Format Version: 1.0*
