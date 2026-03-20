# 扩展开发指南

本指南介绍如何创建 Spec Kit 扩展。

---

## 快速开始

### 1. 创建扩展目录

```bash
mkdir my-extension
cd my-extension
```

### 2. 创建 `extension.yml` 清单文件

```yaml
schema_version: "1.0"

extension:
  id: "my-ext"                          # 仅允许小写字母、数字和连字符
  name: "My Extension"
  version: "1.0.0"                      # 语义化版本
  description: "My custom extension"
  author: "Your Name"
  repository: "https://github.com/you/spec-kit-my-ext"
  license: "MIT"

requires:
  speckit_version: ">=0.1.0"            # 最低 spec-kit 版本
  tools:                                # 可选：所需外部工具
    - name: "my-tool"
      required: true
      version: ">=1.0.0"
  commands:                             # 可选：依赖的核心命令
    - "speckit.tasks"

provides:
  commands:
    - name: "speckit.my-ext.hello"      # 必须符合模式：speckit.{ext-id}.{cmd}
      file: "commands/hello.md"
      description: "Say hello"
      aliases: ["speckit.hello"]        # 可选：命令别名

  config:                               # 可选：配置文件
    - name: "my-ext-config.yml"
      template: "my-ext-config.template.yml"
      description: "Extension configuration"
      required: false

hooks:                                  # 可选：集成 hooks
  after_tasks:
    command: "speckit.my-ext.hello"
    optional: true
    prompt: "Run hello command?"

tags:                                   # 可选：用于目录搜索
  - "example"
  - "utility"
```

### 3. 创建 commands 目录

```bash
mkdir commands
```

### 4. 创建命令文件

**文件**：`commands/hello.md`

```markdown
---
description: "Say hello command"
tools:                              # 可选：命令会调用的 AI 工具
  - 'some-tool/function'
scripts:                            # 可选：辅助脚本
  sh: ../../scripts/bash/helper.sh
  ps: ../../scripts/powershell/helper.ps1
---

# Hello Command

This command says hello!

## User Input

$ARGUMENTS

## Steps

1. Greet the user
2. Show extension is working

```bash
echo "Hello from my extension!"
echo "Arguments: $ARGUMENTS"
```

## Extension Configuration

Load extension config from `.specify/extensions/my-ext/my-ext-config.yml`.

### 5. 本地测试

```bash
cd /path/to/spec-kit-project
specify extension add --dev /path/to/my-extension
```

### 6. 验证安装结果

```bash
specify extension list

# 预期输出：
#  ✓ My Extension (v1.0.0)
#     My custom extension
#     Commands: 1 | Hooks: 1 | Status: Enabled
```

### 7. 测试命令

如果你使用 Claude：

```bash
claude
> /speckit.my-ext.hello world
```

命令文件会出现在 `.claude/commands/speckit.my-ext.hello.md`。

---

## Manifest Schema 参考

### 必填字段

#### `schema_version`

扩展 manifest 的 schema 版本。当前值为：`"1.0"`

#### `extension`

扩展元数据块。

**必填子字段：**

- `id`：扩展标识（小写、数字、连字符）
- `name`：可读名称
- `version`：语义化版本（例如 `"1.0.0"`）
- `description`：简短描述

**可选子字段：**

- `author`：扩展作者
- `repository`：源码仓库 URL
- `license`：SPDX license 标识
- `homepage`：扩展主页 URL

#### `requires`

兼容性要求。

**必填子字段：**

- `speckit_version`：语义化版本约束（例如 `" >=0.1.0,<2.0.0"`）

**可选子字段：**

- `tools`：所需外部工具（工具对象数组）
- `commands`：依赖的 core spec-kit commands（命令名数组）
- `scripts`：依赖的 core scripts（脚本名数组）

#### `provides`

扩展提供的能力。

**必填子字段：**

- `commands`：命令对象数组（至少提供一个）

**命令对象字段：**

- `name`：命令名（必须匹配 `speckit.{ext-id}.{command}`）
- `file`：命令文件路径（相对扩展根目录）
- `description`：命令描述（可选）
- `aliases`：命令别名（可选，数组）

### 可选字段

#### `hooks`

用于自动执行的集成 hooks。

可用的 hook 点：

- `after_tasks`：在 `/speckit.tasks` 完成后触发
- `after_implement`：在 `/speckit.implement` 完成后触发（未来能力）

Hook 对象字段：

- `command`：要执行的命令（必须出现在 `provides.commands` 中）
- `optional`：为 `true` 时，执行前提示用户确认
- `prompt`：可选 hook 的提示语
- `description`：hook 描述
- `condition`：执行条件（未来能力）

#### `tags`

用于目录发现的标签数组。

#### `defaults`

扩展默认配置值。

#### `config_schema`

用于校验扩展配置的 JSON Schema。

---

## Command File Format

### Frontmatter (YAML)

```yaml
---
description: "Command description"          # Required
tools:                                      # Optional
  - 'tool-name/function'
scripts:                                    # Optional
  sh: ../../scripts/bash/helper.sh
  ps: ../../scripts/powershell/helper.ps1
---
```

### Body (Markdown)

Use standard Markdown with special placeholders:

- `$ARGUMENTS`: User-provided arguments
- `{SCRIPT}`: Replaced with script path during registration

**Example**:

````markdown
## Steps

1. Parse arguments
2. Execute logic

```bash
args="$ARGUMENTS"
echo "Running with args: $args"
```
````

### Script Path Rewriting

Extension commands use relative paths that get rewritten during registration:

**In extension**:

```yaml
scripts:
  sh: ../../scripts/bash/helper.sh
```

**After registration**:

```yaml
scripts:
  sh: .specify/scripts/bash/helper.sh
```

This allows scripts to reference core spec-kit scripts.

---

## Configuration Files

### Config Template

**File**: `my-ext-config.template.yml`

```yaml
# My Extension Configuration
# Copy this to my-ext-config.yml and customize

# Example configuration
api:
  endpoint: "https://api.example.com"
  timeout: 30

features:
  feature_a: true
  feature_b: false

credentials:
  # DO NOT commit credentials!
  # Use environment variables instead
  api_key: "${MY_EXT_API_KEY}"
```

### Config Loading

In your command, load config with layered precedence:

1. Extension defaults (`extension.yml` → `defaults`)
2. Project config (`.specify/extensions/my-ext/my-ext-config.yml`)
3. Local overrides (`.specify/extensions/my-ext/my-ext-config.local.yml` - gitignored)
4. Environment variables (`SPECKIT_MY_EXT_*`)

**Example loading script**:

```bash
#!/usr/bin/env bash
EXT_DIR=".specify/extensions/my-ext"

# Load and merge config
config=$(yq eval '.' "$EXT_DIR/my-ext-config.yml" -o=json)

# Apply env overrides
if [ -n "${SPECKIT_MY_EXT_API_KEY:-}" ]; then
  config=$(echo "$config" | jq ".api.api_key = \"$SPECKIT_MY_EXT_API_KEY\"")
fi

echo "$config"
```

---

## Validation Rules

### Extension ID

- **Pattern**: `^[a-z0-9-]+$`
- **Valid**: `my-ext`, `tool-123`, `awesome-plugin`
- **Invalid**: `MyExt` (uppercase), `my_ext` (underscore), `my ext` (space)

### Extension Version

- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Valid**: `1.0.0`, `0.1.0`, `2.5.3`
- **Invalid**: `1.0`, `v1.0.0`, `1.0.0-beta`

### Command Name

- **Pattern**: `^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`
- **Valid**: `speckit.my-ext.hello`, `speckit.tool.cmd`
- **Invalid**: `my-ext.hello` (missing prefix), `speckit.hello` (no extension namespace)

### Command File Path

- **Must be** relative to extension root
- **Valid**: `commands/hello.md`, `commands/subdir/cmd.md`
- **Invalid**: `/absolute/path.md`, `../outside.md`

---

## Testing Extensions

### Manual Testing

1. **Create test extension**
2. **Install locally**:

   ```bash
   specify extension add --dev /path/to/extension
   ```

3. **Verify installation**:

   ```bash
   specify extension list
   ```

4. **Test commands** with your AI agent
5. **Check command registration**:

   ```bash
   ls .claude/commands/speckit.my-ext.*
   ```

6. **Remove extension**:

   ```bash
   specify extension remove my-ext
   ```

### Automated Testing

Create tests for your extension:

```python
# tests/test_my_extension.py
import pytest
from pathlib import Path
from specify_cli.extensions import ExtensionManifest

def test_manifest_valid():
    """Test extension manifest is valid."""
    manifest = ExtensionManifest(Path("extension.yml"))
    assert manifest.id == "my-ext"
    assert len(manifest.commands) >= 1

def test_command_files_exist():
    """Test all command files exist."""
    manifest = ExtensionManifest(Path("extension.yml"))
    for cmd in manifest.commands:
        cmd_file = Path(cmd["file"])
        assert cmd_file.exists(), f"Command file not found: {cmd_file}"
```

---

## Distribution

### Option 1: GitHub Repository

1. **Create repository**: `spec-kit-my-ext`
2. **Add files**:

   ```text
   spec-kit-my-ext/
   ├── extension.yml
   ├── commands/
   ├── scripts/
   ├── docs/
   ├── README.md
   ├── LICENSE
   └── CHANGELOG.md
   ```

3. **Create release**: Tag with version (e.g., `v1.0.0`)
4. **Install from repo**:

   ```bash
   git clone https://github.com/you/spec-kit-my-ext
   specify extension add --dev spec-kit-my-ext/
   ```

### Option 2: ZIP Archive (Future)

Create ZIP archive and host on GitHub Releases:

```bash
zip -r spec-kit-my-ext-1.0.0.zip extension.yml commands/ scripts/ docs/
```

Users install with:

```bash
specify extension add --from https://github.com/.../spec-kit-my-ext-1.0.0.zip
```

### Option 3: Community Reference Catalog

Submit to the community catalog for public discovery:

1. **Fork** spec-kit repository
2. **Add entry** to `extensions/catalog.community.json`
3. **Update** `extensions/README.md` with your extension
4. **Create PR** following the [Extension Publishing Guide](EXTENSION-PUBLISHING-GUIDE.md)
5. **After merge**, your extension becomes available:
   - Users can browse `catalog.community.json` to discover your extension
   - Users copy the entry to their own `catalog.json`
   - Users install with: `specify extension add my-ext` (from their catalog)

See the [Extension Publishing Guide](EXTENSION-PUBLISHING-GUIDE.md) for detailed submission instructions.

---

## Best Practices

### Naming Conventions

- **Extension ID**: Use descriptive, hyphenated names (`jira-integration`, not `ji`)
- **Commands**: Use verb-noun pattern (`create-issue`, `sync-status`)
- **Config files**: Match extension ID (`jira-config.yml`)

### Documentation

- **README.md**: Overview, installation, usage
- **CHANGELOG.md**: Version history
- **docs/**: Detailed guides
- **Command descriptions**: Clear, concise

### Versioning

- **Follow SemVer**: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features
- **PATCH**: Bug fixes

### Security

- **Never commit secrets**: Use environment variables
- **Validate input**: Sanitize user arguments
- **Document permissions**: What files/APIs are accessed

### Compatibility

- **Specify version range**: Don't require exact version
- **Test with multiple versions**: Ensure compatibility
- **Graceful degradation**: Handle missing features

---

## Example Extensions

### Minimal Extension

Smallest possible extension:

```yaml
# extension.yml
schema_version: "1.0"
extension:
  id: "minimal"
  name: "Minimal Extension"
  version: "1.0.0"
  description: "Minimal example"
requires:
  speckit_version: ">=0.1.0"
provides:
  commands:
    - name: "speckit.minimal.hello"
      file: "commands/hello.md"
```

````markdown
<!-- commands/hello.md -->
---
description: "Hello command"
---

# Hello World

```bash
echo "Hello, $ARGUMENTS!"
```
````

### Extension with Config

Extension using configuration:

```yaml
# extension.yml
# ... metadata ...
provides:
  config:
    - name: "tool-config.yml"
      template: "tool-config.template.yml"
      required: true
```

```yaml
# tool-config.template.yml
api_endpoint: "https://api.example.com"
timeout: 30
```

````markdown
<!-- commands/use-config.md -->
# Use Config

Load config:
```bash
config_file=".specify/extensions/tool/tool-config.yml"
endpoint=$(yq eval '.api_endpoint' "$config_file")
echo "Using endpoint: $endpoint"
```
````

### Extension with Hooks

Extension that runs automatically:

```yaml
# extension.yml
hooks:
  after_tasks:
    command: "speckit.auto.analyze"
    optional: false  # Always run
    description: "Analyze tasks after generation"
```

---

## Troubleshooting

### Extension won't install

**Error**: `Invalid extension ID`

- **Fix**: Use lowercase, alphanumeric + hyphens only

**Error**: `Extension requires spec-kit >=0.2.0`

- **Fix**: Update spec-kit with `uv tool install specify-cli --force`

**Error**: `Command file not found`

- **Fix**: Ensure command files exist at paths specified in manifest

### Commands not registered

**Symptom**: Commands don't appear in AI agent

**Check**:

1. `.claude/commands/` directory exists
2. Extension installed successfully
3. Commands registered in registry:

   ```bash
   cat .specify/extensions/.registry
   ```

**Fix**: Reinstall extension to trigger registration

### Config not loading

**Check**:

1. Config file exists: `.specify/extensions/{ext-id}/{ext-id}-config.yml`
2. YAML syntax is valid: `yq eval '.' config.yml`
3. Environment variables set correctly

---

## Getting Help

- **Issues**: Report bugs at GitHub repository
- **Discussions**: Ask questions in GitHub Discussions
- **Examples**: See `spec-kit-jira` for full-featured example (Phase B)

---

## Next Steps

1. **Create your extension** following this guide
2. **Test locally** with `--dev` flag
3. **Share with community** (GitHub, catalog)
4. **Iterate** based on feedback

Happy extending! 🚀
