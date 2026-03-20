# 扩展模板

这是一个用于创建 Spec Kit 扩展的起始模板。

## 快速开始

1. **复制此模板**：

   ```bash
   cp -r extensions/template my-extension
   cd my-extension
   ```

2. **自定义 `extension.yml`**：
   - 修改扩展 ID、名称和描述
   - 更新作者和仓库地址
   - 定义自己的命令

3. **Create commands**:
   - Add command files in `commands/` directory
   - Use Markdown format with YAML frontmatter

4. **Create config template**:
   - Define configuration options
   - Document all settings

5. **Write documentation**:
   - Update README.md with usage instructions
   - Add examples

6. **Test locally**:

   ```bash
   cd /path/to/spec-kit-project
   specify extension add --dev /path/to/my-extension
   ```

7. **Publish** (optional):
   - Create GitHub repository
   - Create release
   - Submit to catalog (see EXTENSION-PUBLISHING-GUIDE.md)

## 模板内包含的文件

- `extension.yml` - Extension manifest (CUSTOMIZE THIS)
- `config-template.yml` - Configuration template (CUSTOMIZE THIS)
- `commands/example.md` - Example command (REPLACE THIS)
- `README.md` - Extension documentation (REPLACE THIS)
- `LICENSE` - MIT License (REVIEW THIS)
- `CHANGELOG.md` - Version history (UPDATE THIS)
- `.gitignore` - Git ignore rules

## 自定义检查清单

- [ ] Update `extension.yml` with your extension details
- [ ] Change extension ID to your extension name
- [ ] Update author information
- [ ] Define your commands
- [ ] Create command files in `commands/`
- [ ] Update config template
- [ ] Write README with usage instructions
- [ ] Add examples
- [ ] Update LICENSE if needed
- [ ] Test extension locally
- [ ] Create git repository
- [ ] Create first release

## 需要帮助？

- **Development Guide**: See EXTENSION-DEVELOPMENT-GUIDE.md
- **API Reference**: See EXTENSION-API-REFERENCE.md
- **Publishing Guide**: See EXTENSION-PUBLISHING-GUIDE.md
- **User Guide**: See EXTENSION-USER-GUIDE.md

## 模板版本

- Version: 1.0.0
- Last Updated: 2026-01-28
- Compatible with Spec Kit: >=0.1.0
