<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 扩展 API 参考

这是 Spec Kit 扩展系统 API 与 manifest schema 的技术参考文档。

## 目录

1. [扩展 Manifest](#扩展-manifest)
2. [Python API](#python-api)
3. [命令文件格式](#命令文件格式)
4. [配置 Schema](#配置-schema)
5. [Hook 系统](#hook-系统)
6. [CLI 命令](#cli-命令)

---

## 扩展 Manifest

### Schema 版本 1.0

文件：`extension.yml`

```yaml
schema_version: "1.0"  # 必填

extension:
  id: string           # 必填，模式：^[a-z0-9-]+$
  name: string         # 必填，人类可读名称
  version: string      # 必填，语义化版本（X.Y.Z）
  description: string  # 必填，简短描述（<200 chars）
  author: string       # 必填
  repository: string   # 必填，有效 URL
  license: string      # 必填（例如 "MIT", "Apache-2.0"）
  homepage: string     # 可选，有效 URL

requires:
  speckit_version: string  # 必填，版本约束（>=X.Y.Z）
  tools:                   # 可选，工具要求数组
    - name: string         # 工具名称
      version: string      # 可选，版本约束
      required: boolean    # 可选，默认 false

provides:
  commands:               # 必填，至少一个命令
    - name: string        # 必填，模式：^speckit\.[a-z0-9-]+\.[a-z0-9-]+$
      file: string        # 必填，命令文件相对路径
      description: string # 必填
      aliases: [string]   # 可选，别名数组

  config:                # 可选，配置文件数组
    - name: string       # 配置文件名称
      template: string   # 模板文件路径
      description: string
      required: boolean  # 默认 false

hooks:                   # 可选，事件 hooks
  event_name:            # 例如 "after_tasks", "after_implement"
    command: string      # 要执行的命令
    optional: boolean    # 默认 true
    prompt: string       # 可选 hook 的提示语
    description: string  # Hook 描述
    condition: string    # 可选，条件表达式

tags:                    # 可选，标签数组（建议 2-10 个）
  - string

defaults:                # 可选，默认配置值
  key: value             # 任意 YAML 结构
```

### 字段规范

#### `extension.id`

- **类型**：string
- **模式**：`^[a-z0-9-]+$`
- **说明**：唯一扩展标识
- **示例**：`jira`、`linear`、`azure-devops`
- **无效示例**：`Jira`、`my_extension`、`extension.id`

#### `extension.version`

- **类型**：string
- **格式**：语义化版本（X.Y.Z）
- **说明**：扩展版本
- **示例**：`1.0.0`、`0.9.5`、`2.1.3`
- **无效示例**：`v1.0`、`1.0`、`1.0.0-beta`

#### `requires.speckit_version`

- **类型**：string
- **格式**：版本约束表达式
- **说明**：要求的 spec-kit 版本范围
- **示例**：
  - `>=0.1.0` - 任何 0.1.0 及以上版本
  - `>=0.1.0,<2.0.0` - 0.1.x 或 1.x
  - `==0.1.0` - 精确匹配 0.1.0
- **无效示例**：`0.1.0`、`>= 0.1.0`（带空格）、`latest`

#### `provides.commands[].name`

- **类型**：string
- **模式**：`^speckit\.[a-z0-9-]+\.[a-z0-9-]+$`
- **说明**：带命名空间的命令名
- **格式**：`speckit.{extension-id}.{command-name}`
- **示例**：`speckit.jira.specstoissues`、`speckit.linear.sync`
- **无效示例**：`jira.specstoissues`、`speckit.command`、`speckit.jira.CreateIssues`

#### `hooks`

- **类型**：object
- **键名**：事件名称（例如 `after_tasks`、`after_implement`、`before_commit`）
- **说明**：在生命周期事件上触发的 hooks
- **事件来源**：由 core spec-kit commands 定义

---

## Python API

### ExtensionManifest

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionManifest

manifest = ExtensionManifest(Path("extension.yml"))
```

**Properties**:

```python
manifest.id                        # str: Extension ID
manifest.name                      # str: Extension name
manifest.version                   # str: Version
manifest.description               # str: Description
manifest.requires_speckit_version  # str: Required spec-kit version
manifest.commands                  # List[Dict]: Command definitions
manifest.hooks                     # Dict: Hook definitions
```

**Methods**:

```python
manifest.get_hash()  # str: SHA256 hash of manifest file
```

**Exceptions**:

```python
ValidationError       # Invalid manifest structure
CompatibilityError    # Incompatible with current spec-kit version
```

### ExtensionRegistry

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionRegistry

registry = ExtensionRegistry(extensions_dir)
```

**Methods**:

```python
# Add extension to registry
registry.add(extension_id: str, metadata: dict)

# Remove extension from registry
registry.remove(extension_id: str)

# Get extension metadata
metadata = registry.get(extension_id: str)  # Optional[dict]

# List all extensions
extensions = registry.list()  # Dict[str, dict]

# Check if installed
is_installed = registry.is_installed(extension_id: str)  # bool
```

**Registry Format**:

```json
{
  "schema_version": "1.0",
  "extensions": {
    "jira": {
      "version": "1.0.0",
      "source": "catalog",
      "manifest_hash": "sha256...",
      "enabled": true,
      "registered_commands": ["speckit.jira.specstoissues", ...],
      "installed_at": "2026-01-28T..."
    }
  }
}
```

### ExtensionManager

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionManager

manager = ExtensionManager(project_root)
```

**Methods**:

```python
# Install from directory
manifest = manager.install_from_directory(
    source_dir: Path,
    speckit_version: str,
    register_commands: bool = True
)  # Returns: ExtensionManifest

# Install from ZIP
manifest = manager.install_from_zip(
    zip_path: Path,
    speckit_version: str
)  # Returns: ExtensionManifest

# Remove extension
success = manager.remove(
    extension_id: str,
    keep_config: bool = False
)  # Returns: bool

# List installed extensions
extensions = manager.list_installed()  # List[Dict]

# Get extension manifest
manifest = manager.get_extension(extension_id: str)  # Optional[ExtensionManifest]

# Check compatibility
manager.check_compatibility(
    manifest: ExtensionManifest,
    speckit_version: str
)  # Raises: CompatibilityError if incompatible
```

### CatalogEntry

**Module**: `specify_cli.extensions`

Represents a single catalog in the active catalog stack.

```python
from specify_cli.extensions import CatalogEntry

entry = CatalogEntry(
    url="https://example.com/catalog.json",
    name="default",
    priority=1,
    install_allowed=True,
    description="Built-in catalog of installable extensions",
)
```

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `url` | `str` | Catalog URL (must use HTTPS, or HTTP for localhost) |
| `name` | `str` | Human-readable catalog name |
| `priority` | `int` | Sort order (lower = higher priority, wins on conflicts) |
| `install_allowed` | `bool` | Whether extensions from this catalog can be installed |
| `description` | `str` | Optional human-readable description of the catalog (default: empty) |

### ExtensionCatalog

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import ExtensionCatalog

catalog = ExtensionCatalog(project_root)
```

**Class attributes**:

```python
ExtensionCatalog.DEFAULT_CATALOG_URL    # default catalog URL
ExtensionCatalog.COMMUNITY_CATALOG_URL  # community catalog URL
```

**Methods**:

```python
# Get the ordered list of active catalogs
entries = catalog.get_active_catalogs()  # List[CatalogEntry]

# Fetch catalog (primary catalog, backward compat)
catalog_data = catalog.fetch_catalog(force_refresh: bool = False)  # Dict

# Search extensions across all active catalogs
# Each result includes _catalog_name and _install_allowed
results = catalog.search(
    query: Optional[str] = None,
    tag: Optional[str] = None,
    author: Optional[str] = None,
    verified_only: bool = False
)  # Returns: List[Dict]  — each dict includes _catalog_name, _install_allowed

# Get extension info (searches all active catalogs)
# Returns None if not found; includes _catalog_name and _install_allowed
ext_info = catalog.get_extension_info(extension_id: str)  # Optional[Dict]

# Check cache validity (primary catalog)
is_valid = catalog.is_cache_valid()  # bool

# Clear all catalog caches
catalog.clear_cache()
```

**Result annotation fields**:

Each extension dict returned by `search()` and `get_extension_info()` includes:

| Field | Type | Description |
|-------|------|-------------|
| `_catalog_name` | `str` | Name of the source catalog |
| `_install_allowed` | `bool` | Whether installation is allowed from this catalog |

**Catalog config file** (`.specify/extension-catalogs.yml`):

```yaml
catalogs:
  - name: "default"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.json"
    priority: 1
    install_allowed: true
    description: "Built-in catalog of installable extensions"
  - name: "community"
    url: "https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json"
    priority: 2
    install_allowed: false
    description: "Community-contributed extensions (discovery only)"
```

### HookExecutor

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import HookExecutor

hook_executor = HookExecutor(project_root)
```

**Methods**:

```python
# Get project config
config = hook_executor.get_project_config()  # Dict

# Save project config
hook_executor.save_project_config(config: Dict)

# Register hooks
hook_executor.register_hooks(manifest: ExtensionManifest)

# Unregister hooks
hook_executor.unregister_hooks(extension_id: str)

# Get hooks for event
hooks = hook_executor.get_hooks_for_event(event_name: str)  # List[Dict]

# Check if hook should execute
should_run = hook_executor.should_execute_hook(hook: Dict)  # bool

# Format hook message
message = hook_executor.format_hook_message(
    event_name: str,
    hooks: List[Dict]
)  # str
```

### CommandRegistrar

**Module**: `specify_cli.extensions`

```python
from specify_cli.extensions import CommandRegistrar

registrar = CommandRegistrar()
```

**Methods**:

```python
# Register commands for Claude Code
registered = registrar.register_commands_for_claude(
    manifest: ExtensionManifest,
    extension_dir: Path,
    project_root: Path
)  # Returns: List[str] (command names)

# Parse frontmatter
frontmatter, body = registrar.parse_frontmatter(content: str)

# Render frontmatter
yaml_text = registrar.render_frontmatter(frontmatter: Dict)  # str
```

---

## Command File Format

### Universal Command Format

**File**: `commands/{command-name}.md`

```markdown
---
description: "Command description"
tools:
  - 'mcp-server/tool_name'
  - 'other-mcp-server/other_tool'
---

# Command Title

Command documentation in Markdown.

## Prerequisites

1. Requirement 1
2. Requirement 2

## User Input

$ARGUMENTS

## Steps

### Step 1: Description

Instruction text...

\`\`\`bash
# Shell commands
\`\`\`

### Step 2: Another Step

More instructions...

## Configuration Reference

Information about configuration options.

## Notes

Additional notes and tips.
```

### Frontmatter Fields

```yaml
description: string   # Required, brief command description
tools: [string]       # Optional, MCP tools required
```

### Special Variables

- `$ARGUMENTS` - Placeholder for user-provided arguments
- Extension context automatically injected:

  ```markdown
  <!-- Extension: {extension-id} -->
  <!-- Config: .specify/extensions/{extension-id}/ -->
  ```

---

## Configuration Schema

### Extension Config File

**File**: `.specify/extensions/{extension-id}/{extension-id}-config.yml`

Extensions define their own config schema. Common patterns:

```yaml
# Connection settings
connection:
  url: string
  api_key: string

# Project settings
project:
  key: string
  workspace: string

# Feature flags
features:
  enabled: boolean
  auto_sync: boolean

# Defaults
defaults:
  labels: [string]
  assignee: string

# Custom fields
field_mappings:
  internal_name: "external_field_id"
```

### Config Layers

1. **Extension Defaults** (from `extension.yml` `defaults` section)
2. **Project Config** (`{extension-id}-config.yml`)
3. **Local Override** (`{extension-id}-config.local.yml`, gitignored)
4. **Environment Variables** (`SPECKIT_{EXTENSION}_*`)

### Environment Variable Pattern

Format: `SPECKIT_{EXTENSION}_{KEY}`

Examples:

- `SPECKIT_JIRA_PROJECT_KEY`
- `SPECKIT_LINEAR_API_KEY`
- `SPECKIT_GITHUB_TOKEN`

---

## Hook System

### Hook Definition

**In extension.yml**:

```yaml
hooks:
  after_tasks:
    command: "speckit.jira.specstoissues"
    optional: true
    prompt: "Create Jira issues from tasks?"
    description: "Automatically create Jira hierarchy"
    condition: null
```

### Hook Events

Standard events (defined by core):

- `after_tasks` - After task generation
- `after_implement` - After implementation
- `before_commit` - Before git commit
- `after_commit` - After git commit

### Hook Configuration

**In `.specify/extensions.yml`**:

```yaml
hooks:
  after_tasks:
    - extension: jira
      command: speckit.jira.specstoissues
      enabled: true
      optional: true
      prompt: "Create Jira issues from tasks?"
      description: "..."
      condition: null
```

### Hook Message Format

```markdown
## Extension Hooks

**Optional Hook**: {extension}
Command: `/{command}`
Description: {description}

Prompt: {prompt}
To execute: `/{command}`
```

Or for mandatory hooks:

```markdown
**Automatic Hook**: {extension}
Executing: `/{command}`
EXECUTE_COMMAND: {command}
```

---

## CLI Commands

### extension list

**Usage**: `specify extension list [OPTIONS]`

**Options**:

- `--available` - Show available extensions from catalog
- `--all` - Show both installed and available

**Output**: List of installed extensions with metadata

### extension catalog list

**Usage**: `specify extension catalog list`

Lists all active catalogs in the current catalog stack, showing name, description, URL, priority, and `install_allowed` status.

### extension catalog add

**Usage**: `specify extension catalog add URL [OPTIONS]`

**Options**:

- `--name NAME` - Catalog name (required)
- `--priority INT` - Priority (lower = higher priority, default: 10)
- `--install-allowed / --no-install-allowed` - Allow installs from this catalog (default: false)
- `--description TEXT` - Optional description of the catalog

**Arguments**:

- `URL` - Catalog URL (must use HTTPS)

Adds a catalog entry to `.specify/extension-catalogs.yml`.

### extension catalog remove

**Usage**: `specify extension catalog remove NAME`

**Arguments**:

- `NAME` - Catalog name to remove

Removes a catalog entry from `.specify/extension-catalogs.yml`.

### extension add

**Usage**: `specify extension add EXTENSION [OPTIONS]`

**Options**:

- `--from URL` - Install from custom URL
- `--dev PATH` - Install from local directory

**Arguments**:

- `EXTENSION` - Extension name or URL

**Note**: Extensions from catalogs with `install_allowed: false` cannot be installed via this command.

### extension remove

**Usage**: `specify extension remove EXTENSION [OPTIONS]`

**Options**:

- `--keep-config` - Preserve config files
- `--force` - Skip confirmation

**Arguments**:

- `EXTENSION` - Extension ID

### extension search

**Usage**: `specify extension search [QUERY] [OPTIONS]`

Searches all active catalogs simultaneously. Results include source catalog name and install_allowed status.

**Options**:

- `--tag TAG` - Filter by tag
- `--author AUTHOR` - Filter by author
- `--verified` - Show only verified extensions

**Arguments**:

- `QUERY` - Optional search query

### extension info

**Usage**: `specify extension info EXTENSION`

Shows source catalog and install_allowed status.

**Arguments**:

- `EXTENSION` - Extension ID

### extension update

**Usage**: `specify extension update [EXTENSION]`

**Arguments**:

- `EXTENSION` - Optional, extension ID (default: all)

### extension enable

**Usage**: `specify extension enable EXTENSION`

**Arguments**:

- `EXTENSION` - Extension ID

### extension disable

**Usage**: `specify extension disable EXTENSION`

**Arguments**:

- `EXTENSION` - Extension ID

---

## Exceptions

### ValidationError

Raised when extension manifest validation fails.

```python
from specify_cli.extensions import ValidationError

try:
    manifest = ExtensionManifest(path)
except ValidationError as e:
    print(f"Invalid manifest: {e}")
```

### CompatibilityError

Raised when extension is incompatible with current spec-kit version.

```python
from specify_cli.extensions import CompatibilityError

try:
    manager.check_compatibility(manifest, "0.1.0")
except CompatibilityError as e:
    print(f"Incompatible: {e}")
```

### ExtensionError

Base exception for all extension-related errors.

```python
from specify_cli.extensions import ExtensionError

try:
    manager.install_from_directory(path, "0.1.0")
except ExtensionError as e:
    print(f"Extension error: {e}")
```

---

## Version Functions

### version_satisfies

Check if a version satisfies a specifier.

```python
from specify_cli.extensions import version_satisfies

# True if 1.2.3 satisfies >=1.0.0,<2.0.0
satisfied = version_satisfies("1.2.3", ">=1.0.0,<2.0.0")  # bool
```

---

## File System Layout

```text
.specify/
├── extensions/
│   ├── .registry               # Extension registry (JSON)
│   ├── .cache/                 # Catalog cache
│   │   ├── catalog.json
│   │   └── catalog-metadata.json
│   ├── .backup/                # Config backups
│   │   └── {ext}-{config}.yml
│   ├── {extension-id}/         # Extension directory
│   │   ├── extension.yml       # Manifest
│   │   ├── {ext}-config.yml    # User config
│   │   ├── {ext}-config.local.yml  # Local overrides (gitignored)
│   │   ├── {ext}-config.template.yml  # Template
│   │   ├── commands/           # Command files
│   │   │   └── *.md
│   │   ├── scripts/            # Helper scripts
│   │   │   └── *.sh
│   │   ├── docs/               # Documentation
│   │   └── README.md
│   └── extensions.yml          # Project extension config
└── scripts/                    # (existing spec-kit)

.claude/
└── commands/
    └── speckit.{ext}.{cmd}.md  # Registered commands
```

---

*Last Updated: 2026-01-28*
*API Version: 1.0*
*Spec Kit Version: 0.1.0*
