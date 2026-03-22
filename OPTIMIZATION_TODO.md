# spec-kit-zh 优化操作清单

> 基于代码审计自动生成，每项均标注 **当前状态、涉及文件、具体步骤、验收标准**。
> 最后审计时间：2026-03-23 | 项目版本：0.4.0

---

## P0：必须立即处理（阻塞发布）

### 1. 统一所有 CLI 展示品牌

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未完成 — `__init__.py` 15 处 + `extensions.py` 11 处，共 **26 处**需修复 |
| **涉及文件** | `src/specify_cli/__init__.py`、`src/specify_cli/extensions.py` |

**操作步骤：**

1. **`__init__.py` — 品牌文本修正（15 处）：**
   - [ ] L13 文档字符串：`Specify CLI` → `specify-cli-zh`
   - [ ] L315-322 BANNER ASCII art：在 `SPECIFY` 下方或 TAGLINE 中明确 ZH 标识
   - [ ] L324 TAGLINE：`"GitHub Spec Kit ZH - 规范驱动开发工具包"` → `"specify-cli-zh - 规范驱动开发工具包"`
   - [ ] L518 help 文本：`"Spec Kit 规范驱动开发项目设置工具"` → `"specify-cli-zh 规范驱动开发项目设置工具"`
   - [ ] L2016 Panel 标题：`"Specify CLI 信息"` → `"specify-cli-zh 信息"`
   - [ ] L579 错误提示：`"Error running command:"` → `"执行命令出错："`
   - [ ] L582 错误提示：`"Error output:"` → `"错误输出："`
   - [ ] L789 错误提示：`"Error initializing git repository:"` → `"初始化 Git 仓库出错："`
   - [ ] L1003 错误提示：`"Error downloading template:"` → `"下载模板出错："`
   - [ ] L1101 调试输出：`"Error extracting template:"` → `"解压模板出错："`
   - [ ] L1103 Panel 标题：`"Extraction Error"` → `"解压错误"`
   - [ ] L1113 tracker label：`"Remove temporary archive"` → `"清理临时压缩包"`
   - [ ] L1120 verbose 输出：`"Cleaned up: {zip_path.name}"` → `"已清理：{zip_path.name}"`
   - [ ] L1200 提示：`"Initialized constitution from template"` → `"已从模板初始化章程"`
   - [ ] L1206 警告：`"Warning: Could not initialize constitution:"` → `"警告：无法初始化章程："`

2. **`extensions.py` — 英文异常/日志消息（11 处）：**
   - [ ] L1208：`"Invalid catalog format from {entry.url}"` → `"目录格式无效，来源：{entry.url}"`
   - [ ] L1221：`"Failed to fetch catalog from ..."` → `"获取扩展目录失败，来源：..."`
   - [ ] L1223：`"Invalid JSON in catalog from ..."` → `"扩展目录 JSON 格式无效，来源：..."`
   - [ ] L1272：`"Failed to fetch any extension catalog"` → `"未能获取任何扩展目录"`
   - [ ] L1326：`"Invalid catalog format"` → `"目录格式无效"`
   - [ ] L1342：`"Failed to fetch catalog from ..."` → `"获取目录失败：..."`
   - [ ] L1344：`"Invalid JSON in catalog: ..."` → `"目录 JSON 格式无效：..."`
   - [ ] L1438：`"Extension '...' not found in catalog"` → `"在目录中未找到扩展 '...'"`
   - [ ] L1442：`"Extension '...' has no download URL"` → `"扩展 '...' 没有下载地址"`
   - [ ] L1471：`"Failed to download extension from ..."` → `"从 ... 下载扩展失败：..."`
   - [ ] L1473：`"Failed to save extension ZIP: ..."` → `"保存扩展压缩包失败：..."`

**验收标准：**
- `grep -rn "Specify CLI" src/` 返回 0 结果
- `grep -rn '"Error ' src/` 返回 0 条英文 UI 文案（日志级别的 debug 信息除外）
- `specify-zh --help`、`specify-zh version`、`specify-zh doctor` 输出中无旧品牌名

---

### 2. 完成 extension 子系统中文化收口

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未完成 — TODO 列出的 12 类字符串全部存在（~25 处），额外发现 ~35 处英文 UI，总计约 **60 处** |
| **涉及文件** | `src/specify_cli/__init__.py` L2500-L2870 区间（extension 子命令集中区） |

**操作步骤：**

1. **TODO 原始列出的 12 类字符串翻译：**
   - [ ] `[red]Error:[/red]` → `[red]错误：[/red]`（L2544, L2561, L2572, L2668, L2685, L2697, L2775, L2791, L2799, L2835, L2843 共 11 处）
   - [ ] `[cyan]Install:[/cyan]` → `[cyan]安装：[/cyan]`（L2657）
   - [ ] `"To remove"` → `"如需卸载"`（L2654）
   - [ ] `"Updates available"` → `"有可用更新"`（L2743）
   - [ ] `"Up to date"` → `"已是最新"`（L2736, L2739 共 2 处）
   - [ ] `"Cancelled"` → `"已取消"`（L2752）
   - [ ] `"Not installed"` → `"未安装"`（L2656, L2660 共 2 处）
   - [ ] `"✓ Verified"` → `"✓ 已验证"`（L2500, L2577 共 2 处）
   - [ ] `"Requirements"` → `"依赖要求"`（L2599）
   - [ ] `"Provides"` → `"提供内容"`（L2613）
   - [ ] `"Tags"` → `"标签"`（L2624）
   - [ ] `"Statistics"` → `"统计信息"`（L2634）

2. **审计额外发现的 ~35 处英文 UI（必须一并处理）：**
   - [ ] 子命令 help 文本翻译（4 处）：
     - L2553 `"Show detailed information about an extension."` → `"显示扩展的详细信息。"`
     - L2676 `"Update extension(s) to latest version."` → `"将扩展更新到最新版本。"`
     - L2783 `"Enable a disabled extension."` → `"启用已禁用的扩展。"`
     - L2827 `"Disable an extension without removing it."` → `"禁用扩展（不卸载）。"`
   - [ ] 参数描述翻译（4 处）：
     - L2551 `"Extension ID or name"` → `"扩展 ID 或名称"`
     - L2674 `"Extension ID to update (or all)"` → `"要更新的扩展 ID（或 all）"`
     - L2781 `"Extension ID to enable"` → `"要启用的扩展 ID"`
     - L2825 `"Extension ID to disable"` → `"要禁用的扩展 ID"`
   - [ ] 错误消息翻译（4 处重复模式）：
     - `"Not a spec-kit project (no .specify/ directory)"` → `"非 spec-kit 项目（未找到 .specify/ 目录）"`
     - `"Run this command from a spec-kit project root"` → `"请在 spec-kit 项目根目录下执行此命令"`
   - [ ] 信息标签翻译（全部）：
     - `"Author:"` → `"作者："`、`"License:"` → `"许可证："`、`"Source catalog:"` → `"来源目录："`
     - `"Commands:"` → `"命令："` 、`"Hooks:"` → `"钩子："`、`"Downloads:"` → `"下载量："`、`"Stars:"` → `"星标："`
     - `"Links:"` → `"链接："`、`"Repository:"` → `"仓库："`、`"Homepage:"` → `"主页："`、`"Documentation:"` → `"文档："`、`"Changelog:"` → `"更新日志："`
     - `"(required)"` → `"（必需）"`、`"(optional)"` → `"（可选）"`、`"(discovery only)"` → `"（仅发现）"`
   - [ ] 流程消息翻译：
     - `"✓ Installed"` → `"✓ 已安装"`（L2653）
     - `"Checking for updates..."` → `"正在检查更新..."`（L2709）
     - `"No extensions installed"` → `"未安装任何扩展"`（L2706）
     - `"Not found in catalog (skipping)"` → `"在目录中未找到（已跳过）"`（L2721）
     - `"All extensions are up to date!"` → `"所有扩展均已是最新版本！"`（L2739）
     - `"Update these extensions?"` → `"是否更新这些扩展？"`（L2750）
     - `"Updating {ext_id}..."` → `"正在更新 {ext_id}..."`（L2759）
     - `"Note: Automatic update not yet implemented..."` → `"提示：自动更新功能尚未实现..."`（L2764-2765）
     - `"Tip: Automatic updates will be available..."` → `"提示：自动更新将在后续版本推出..."`（L2771）
   - [ ] enable/disable 结果消息：
     - `"Extension '...' enabled"` → `"扩展 '...' 已启用"`（L2805）
     - `"Extension '...' is already enabled"` → `"扩展 '...' 已处于启用状态"`（L2820）
     - `"Extension '...' disabled"` → `"扩展 '...' 已禁用"`（L2849）
     - `"Extension '...' is already disabled"` → `"扩展 '...' 已处于禁用状态"`（L2864）
     - `"Commands will no longer be available. Hooks will not execute."` → `"命令将不可用，钩子将不再执行。"`（L2865）
   - [ ] 品牌修正（P0-1 交叉项）：
     - L2654 `"specify extension remove"` → `"specify-zh extension remove"`
     - L2767 `"specify extension remove"` → `"specify-zh extension remove"`
     - L2866 `"To re-enable: specify extension enable"` → `"重新启用：specify-zh extension enable"`

**验收标准：**
- `specify-zh extension info <any>` 全中文输出
- `specify-zh extension update` 全中文输出
- `specify-zh extension enable/disable <any>` 全中文输出
- 运行 `grep -n '"[A-Z][a-z]' src/specify_cli/__init__.py | grep -v '#\|import\|def \|class '` 在 L2500-L2870 区间无英文 UI 残留

---

### 3. 增加安装验证说明

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 部分完成 — `docs/installation.md` L67-74 有简略"验证"段，但缺关键验证命令；README 无验证段落 |
| **涉及文件** | `docs/installation.md`、`README.md` |

**操作步骤：**

1. **完善 `docs/installation.md` L67-74 的验证段落：**
   - [ ] 添加三条验证命令及期望输出：
     ```
     specify-zh --help      # 期望：显示命令帮助列表
     specify-zh version     # 期望：显示版本号和环境信息
     specify-zh check       # 期望：显示工具链检测结果
     ```
   - [ ] 添加"安装包名 vs 执行命令名"说明框：
     ```
     安装包名（pip/uv install 时用）：specify-cli-zh
     执行命令（终端运行时用）：    specify-zh
     ```

2. **在 `README.md` 快速开始段落（L44 `## ⚡ 快速开始`）末尾追加验证小节：**
   - [ ] 添加 `### 验证安装` 小节，包含上述三条命令

**验收标准：**
- `docs/installation.md` 包含 `specify-zh --help`、`specify-zh version`、`specify-zh check` 三条命令
- `README.md` 快速开始段末尾包含验证步骤
- 明确标注"安装包名"与"执行命令名"的区别

---

### 4. 增加发布前 smoke test

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 — 无 smoke test，无 CI 配置，无 `.github/` 目录 |
| **涉及文件** | 新建 `tests/test_smoke.py`、新建 `.github/workflows/smoke.yml`（可选） |

**操作步骤：**

1. **新建 `tests/test_smoke.py`：**
   - [ ] 测试 `specify-zh --help` 退出码为 0
   - [ ] 测试 `specify-zh version` 输出包含版本号格式 `\d+\.\d+\.\d+`
   - [ ] 测试 `specify-zh init --help` 退出码为 0 且输出包含 `--ai`
   - [ ] 测试 `specify-zh check` 退出码为 0
   - [ ] 测试 `specify-zh --help` 输出不包含旧品牌名 `Specify CLI`（不带 -zh）
   - [ ] 测试 `pyproject.toml` 中 `[project.scripts]` 包含 `specify-zh` 入口
   - 实现方式：`subprocess.run(["specify-zh", ...], capture_output=True)` 或 `typer.testing.CliRunner`

2. **在 `Makefile` 中添加 smoke 目标：**
   - [ ] 添加 `smoke: pytest tests/test_smoke.py -v`

3. **（可选）新建 `.github/workflows/smoke.yml`：**
   - [ ] 在 `push` 和 `pull_request` 时触发
   - [ ] 步骤：checkout → setup-python 3.11 → `uv tool install . ` → `pytest tests/test_smoke.py -v`

**验收标准：**
- `make smoke` 或 `pytest tests/test_smoke.py` 全部通过
- smoke test 覆盖：`--help`、`version`、`init --help`、`check` 四个核心入口

---

## P1：强烈建议处理（显著提升体验）

### 5. 给 `specify-zh doctor` 增加诊断信息

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 ~60% 完成 — 已有 Python/Git/uv/Token/连接性检测，缺分发包名、命令入口、结构化输出 |
| **涉及文件** | `src/specify_cli/__init__.py` — `doctor()` L1849、`_collect_doctor_diagnostics()` L687、`_build_doctor_recommendations()` L717 |

**操作步骤：**

1. [ ] 在 `_collect_doctor_diagnostics()` 中新增两项诊断：
   - 分发包名检测：`importlib.metadata.distribution("specify-cli-zh")` 成功/失败
   - 命令入口检测：`shutil.which("specify-zh")` 路径
2. [ ] 在 summary table（L1905-1923）中增加两行：`分发包名: specify-cli-zh`、`命令入口: specify-zh`
3. [ ] 在 `_build_doctor_recommendations()` L728-730 GitHub Token 建议中，补充具体设置命令：
   ```
   export GITHUB_TOKEN=ghp_xxxxx  # 或配置 gh auth login
   ```
4. [ ] 在模板下载失败建议（L734）中，补充离线方案的具体路径：
   ```
   离线方案：手动下载模板仓库到本地，使用 specify-zh init --template-dir <本地路径>
   ```
5. [ ] （可选）将诊断结果重构为"现状→风险→修复命令"三栏格式

**验收标准：**
- `specify-zh doctor` 输出包含"分发包名"和"命令入口"两行
- Token 未配置时显示具体 `export` 命令
- 网络失败时显示离线替代方案

---

### 6. 增强 `init` 的交互体验

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 ~30% 完成 — 有 agent 选择和目录非空确认，缺引导式流程、摘要确认、`.specify/` 冲突检测 |
| **涉及文件** | `src/specify_cli/__init__.py` — `init()` L1423 |

**操作步骤：**

1. [ ] **引导式初始化**：当 `project_name` 未提供且 `--here` 未设置时（L1493-1495），用 `typer.prompt()` 引导输入，而非直接报错
2. [ ] **目录选择**：提示用户选择"在当前目录初始化"还是"创建新目录"
3. [ ] **Agent 选择说明**：在 `select_with_arrows()`（L1557-1563）的选项中为每个 agent 添加一行描述（如 `claude - GitHub 官方 AI 编码助手`）
4. [ ] **初始化摘要确认**：在 setup info panel（L1533-1543）显示后，增加 `typer.confirm("确认以上配置并开始初始化？")` 门控
5. [ ] **`.specify/` 冲突检测**：在初始化开始前检查目标路径是否已有 `.specify/` 目录，提供选项：覆盖 / 跳过 / 取消

**验收标准：**
- 直接执行 `specify-zh init`（无参数）进入引导流程而非报错
- 初始化前显示配置摘要并要求确认
- 已有 `.specify/` 目录时弹出处理选项

---

### 7. 增加 `init --dry-run`

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 — 代码中无 `dry_run` 相关逻辑 |
| **涉及文件** | `src/specify_cli/__init__.py` — `init()` L1423 |

**操作步骤：**

1. [ ] 在 `init()` 函数签名中添加 `--dry-run: bool = typer.Option(False, help="预览将创建的文件和目录，不实际执行")`
2. [ ] 当 `dry_run=True` 时，收集所有将创建的目录、文件、agent 配置目录到列表
3. [ ] 用 Rich Tree 或 Table 展示预览结果，标注哪些文件已存在（会覆盖）、哪些是新建
4. [ ] 跳过所有实际文件写入和 git 操作

**验收标准：**
- `specify-zh init my-project --ai claude --dry-run` 输出文件预览列表，实际不创建任何文件
- 已存在文件标注"[覆盖]"，新文件标注"[新建]"

---

### 8. 增加 `init --json`

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 |
| **涉及文件** | `src/specify_cli/__init__.py` — `init()` L1423 |

**操作步骤：**

1. [ ] 在 `init()` 函数签名中添加 `--json: bool = typer.Option(False, "--json", help="以 JSON 格式输出初始化结果")`
2. [ ] 当 `json=True` 时，抑制 Rich 终端输出，收集结果到 dict 后 `json.dumps()` 输出
3. [ ] JSON schema：
   ```json
   {
     "project_path": "/abs/path",
     "ai_agent": "claude",
     "generated_files": ["list", "of", "files"],
     "generated_directories": ["list", "of", "dirs"],
     "warnings": [],
     "skills_installed": [],
     "template_version": "0.4.0"
   }
   ```

**验收标准：**
- `specify-zh init my-project --ai claude --json | python -m json.tool` 输出合法 JSON
- JSON 包含 `project_path`、`ai_agent`、`generated_files` 字段

---

### 9. 优化 `check` 展示层

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 ~10% — 有 StepTracker 逐项输出，无汇总统计 |
| **涉及文件** | `src/specify_cli/__init__.py` — `check()` L1804 |

**操作步骤：**

1. [ ] 在 tracker 渲染后（L1837）添加汇总 Panel：
   ```
   ╭── 检测汇总 ──╮
   │ 已安装 CLI：5/8          │
   │ 缺失 CLI：  3/8          │
   │ IDE 型（无需 CLI）：13    │
   ╰───────────────╯
   ```
2. [ ] 统计 `AGENT_CONFIG` 中 `check_command` 非空的 agent 通过/失败数
3. [ ] 缺失 CLI > 0 时，输出"推荐优先安装"列表（按使用频率排序前 3）
4. [ ] 将 `"IDE 型 agent，无需 CLI 检测"` 类长提示缩短为 `"[dim]IDE 型，跳过[/dim]"`

**验收标准：**
- `specify-zh check` 底部显示"检测汇总"含已安装/缺失数量
- IDE 型提示不超过 10 个汉字

---

### 10. `version` 命令增强

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 ~40% — 有版本号和平台信息，缺包名/入口/来源/运行模式 |
| **涉及文件** | `src/specify_cli/__init__.py` — `version()` L1960、`_get_cli_distribution_version()` L539 |

**操作步骤：**

1. [ ] 在 version 信息面板（L2001-2012）中增加四行：
   - `分发包名：specify-cli-zh`
   - `命令入口：specify-zh`
   - `模板仓库：github/spec-kit`（从常量或配置读取）
   - `运行模式：已安装` 或 `运行模式：本地开发`
2. [ ] 修改 `_get_cli_distribution_version()` 返回值增加 `source` 字段（`"installed"` / `"local"`），根据是 `importlib.metadata` 成功还是回退 `pyproject.toml` 来判断
3. [ ] 修复 Panel 标题（P0-1 交叉项）：`"Specify CLI 信息"` → `"specify-cli-zh 信息"`

**验收标准：**
- `specify-zh version` 输出包含"分发包名""命令入口""模板仓库""运行模式"四行
- 通过 `uv tool install` 安装后显示"已安装"，`python -m` 本地运行时显示"本地开发"

---

## P2：体验增强（提升第一印象）

### 11. README 首页结构优化

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 缺失 — 无"3 分钟上手"、无"包名 vs 命令名"卡片 |
| **涉及文件** | `README.md` — 在 L44 `## ⚡ 快速开始` 前后调整 |

**操作步骤：**

1. [ ] 在 `## ⚡ 快速开始` 段首添加"3 分钟上手"精简版（仅 3 步：安装→初始化→验证）
2. [ ] 在安装命令后添加醒目提示框：
   ```
   > 📦 安装包名：`specify-cli-zh`（用于 pip/uv install）
   > 🚀 执行命令：`specify-zh`（用于终端运行）
   ```
3. [ ] 添加 `### 我应该用哪个命令？` FAQ 小节，解释 `specify-cli-zh` vs `specify-zh` vs 上游 `specify`

**验收标准：**
- README 前 100 行内包含完整的 3 步快速上手
- 有"安装包名 vs 执行命令"醒目区分

---

### 12. 顶部徽章优化

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 3 个徽章（Stars、License、Docs），缺 version/release，风格不统一 |
| **涉及文件** | `README.md` L12-14 |

**操作步骤：**

1. [ ] 添加 version badge：`![Version](https://img.shields.io/badge/version-0.4.0-blue)`
2. [ ] 添加 latest release badge：`![Release](https://img.shields.io/github/v/release/loulanyue/spec-kit-zh)`
3. [ ] 将 Stars badge 统一为 flat 风格（去掉 `?style=social`），或全部改用 social 风格
4. [ ] 替换 Docs 静态 badge 为动态 badge（如有 docs 站点构建状态）

**验收标准：**
- 徽章数量 >= 5（Stars、License、Version、Release、Docs）
- 所有徽章使用统一的 style 参数

---

### 13. 文档语言一致性收尾

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 README L1-290 已中文化，L292-707 大段英文未翻译 |
| **涉及文件** | `README.md` L292 起的全部英文段落 |

**操作步骤：**

1. [ ] 翻译以下英文段落为中文（保留命令、参数、术语为英文）：
   - L292-317：`Available Slash Commands` 表格 → `可用斜杠命令`
   - L318-323：`Environment Variables` → `环境变量`
   - L325-333：`Core Philosophy` → `核心理念`
   - L335-342：`Development Phases` → `开发阶段`
   - L344-369：`Experimental Goals` → `实验目标`
   - L371-380：`Prerequisites` → `前置要求`
   - L382-388：`Learn More` → `了解更多`
   - L390-669：`Detailed Process` 展开段 → `详细流程`
   - L674-691：`Troubleshooting` → `故障排除`
   - L694-707：`Support` → `支持渠道`
2. [ ] 参照 `TERMINOLOGY.md` 统一术语用法

**验收标准：**
- README 全文中文正文（命令/参数/术语保留英文）
- 无成段英文叙述

---

### 14. 增加迁移指南

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 |
| **涉及文件** | 新建 `docs/migration.md` |

**操作步骤：**

1. [ ] 新建 `docs/migration.md`，包含以下章节：
   - 从 `spec-kit`（英文版）迁移
   - 从 `spec-kit-cn`（早期中文版）迁移
   - 可复用的目录/文件说明：`.specify/`、`spec.md`、`plan.md`、`tasks.md` 可直接保留
   - 建议重新生成的文件：agent commands（因命令格式可能变化）
   - 如何避免覆盖：使用 `init --dry-run` 预览（P1-7 完成后）
2. [ ] 在 `README.md` 和 `docs/index.md` 中添加链接指向迁移指南

**验收标准：**
- `docs/migration.md` 文件存在且包含两个迁移路径
- README 中有链接指向迁移指南

---

### 15. 增加常见安装问题文档

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 几乎缺失 — README L673 仅有 1 个故障排除项（GCM Linux） |
| **涉及文件** | 新建 `docs/troubleshooting.md`、更新 `README.md` L673 |

**操作步骤：**

1. [ ] 新建 `docs/troubleshooting.md`，覆盖以下问题（每个问题给出可复制的解决命令）：
   - `error: Executable already exists` → `uv tool install specify-cli-zh --force`
   - GitHub API rate limit → `export GITHUB_TOKEN=ghp_xxx` 或 `gh auth login`
   - `ModuleNotFoundError: No module named 'typer'` → `uv tool install specify-cli-zh`（而非 pip install）
   - 当前目录非空 → `specify-zh init --here` 或创建新目录
   - Agent CLI 未安装提示 → 列出各 agent CLI 的安装命令
   - 网络超时 → 代理设置 `export HTTPS_PROXY=...`
2. [ ] 在 README `## 🔍 Troubleshooting` 段落中添加链接指向完整文档

**验收标准：**
- `docs/troubleshooting.md` 包含 >= 5 个常见问题及解决方案
- 每个问题提供可直接复制的终端命令

---

## P3：工程质量与维护性

### 16. CLI 输出快照测试

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未开始 — 现有 5 个测试文件仅覆盖内部逻辑，无 CLI 输出捕获 |
| **涉及文件** | 新建 `tests/test_cli_output.py` |

**操作步骤：**

1. [ ] 新建 `tests/test_cli_output.py`，使用 `typer.testing.CliRunner` 捕获 CLI 输出
2. [ ] 添加以下断言测试：
   - `check` 输出不包含 `"Specify CLI"` 且包含 `"specify-zh"`
   - `doctor` 输出不包含 `"Specify CLI"` 且包含 `"specify-zh"`
   - `version` 输出包含 `"specify-cli-zh"` 品牌名
   - `extension` 子命令 help 文本为中文
3. [ ] 添加品牌守护断言：任何子命令输出不得包含 `"Specify CLI"` 字符串（不带 `-zh` 后缀）

**验收标准：**
- `pytest tests/test_cli_output.py` 全绿
- 后续若有人引入英文旧品牌名，测试自动失败

---

### 17. 抽取统一文案常量

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未开始 — ~43 处硬编码品牌字符串分布在两个源文件中 |
| **涉及文件** | `src/specify_cli/__init__.py`、`src/specify_cli/extensions.py` |

**操作步骤：**

1. [ ] 在 `__init__.py` 顶部（或新建 `src/specify_cli/constants.py`）定义品牌常量：
   ```python
   DIST_NAME = "specify-cli-zh"
   CMD_NAME = "specify-zh"
   BRAND_DISPLAY = "specify-cli-zh"
   UPSTREAM_REPO = "github/spec-kit"
   TAGLINE = "specify-cli-zh - 规范驱动开发工具包"
   ```
2. [ ] 全局替换 `__init__.py` 中 30+ 处 `"specify-zh"` 硬编码为 `CMD_NAME`
3. [ ] 全局替换 `__init__.py` 中 2 处 `"specify-cli-zh"` 硬编码为 `DIST_NAME`
4. [ ] 全局替换 `extensions.py` 中相关品牌字符串
5. [ ] 在 `extensions.py` 中 `import` 这些常量

**验收标准：**
- `grep -rn '"specify-zh"' src/` 返回 0 结果（全部使用常量）
- `grep -rn '"specify-cli-zh"' src/` 返回 0 结果（全部使用常量）
- 所有测试通过

---

### 18. 统一 README/docs 术语规则

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 `TERMINOLOGY.md` 已定义 16 个术语，但 README 下半部分未遵循 |
| **涉及文件** | `TERMINOLOGY.md`、`README.md`、`docs/*.md` |

**操作步骤：**

1. [ ] 根据 `TERMINOLOGY.md` 规则校对所有文档，确保以下术语一致：
   - Spec（规范）、Plan（计划）、Tasks（任务）、Extension（扩展）、Catalog（目录）
   - Agent、Skill — 固定保留英文不翻译
2. [ ] 在 `TERMINOLOGY.md` 末尾补充文档中发现的新术语映射（如有）
3. [ ] （可选）编写一个简单的 lint 脚本 `scripts/check-terminology.sh`，grep 检查常见错误翻译

**验收标准：**
- 全部 `.md` 文件中同一概念使用统一译法
- `TERMINOLOGY.md` 作为术语权威来源

---

### 19. 发布检查清单

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 |
| **涉及文件** | 新建 `RELEASE_CHECKLIST.md` |

**操作步骤：**

1. [ ] 新建 `RELEASE_CHECKLIST.md`，包含：
   ```markdown
   ## 发布前检查清单
   - [ ] `pyproject.toml` 版本号已更新
   - [ ] `CHANGELOG.md` 已添加新版本条目
   - [ ] `specify-zh --version` 输出与 pyproject.toml 一致
   - [ ] `specify-zh --help` 无英文旧品牌名
   - [ ] smoke test 全部通过：`make smoke`
   - [ ] README 顶部版本徽章已更新
   - [ ] `docs/installation.md` 安装命令版本号正确
   - [ ] 所有文档链接有效（无 404）
   - [ ] `uv tool install specify-cli-zh --from git+...` 安装测试通过
   ```

**验收标准：**
- `RELEASE_CHECKLIST.md` 存在且包含 >= 8 项检查项
- 每项可直接作为 issue/PR checklist 使用

---

### 20. CI 校验流水线

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 完全缺失 — 无 `.github/` 目录 |
| **涉及文件** | 新建 `.github/workflows/ci.yml` |

**操作步骤：**

1. [ ] 新建 `.github/workflows/ci.yml`，包含以下 job：
   ```yaml
   jobs:
     lint:
       - ruff check src/
       - ruff format --check src/
     test:
       - pytest tests/ -v --tb=short
     smoke:
       - pytest tests/test_smoke.py -v
     brand-guard:
       - 断言 README 不包含 `pip install specify-cli`（无 -zh）
       - 断言 README 不包含 `uv tool install specify-cli`（无 -zh）
       - 断言 pyproject.toml `[project.scripts]` 包含 `specify-zh`
       - 断言 CHANGELOG.md 非空
   ```
2. [ ] 触发条件：`push` 到 `main` 和所有 `pull_request`

**验收标准：**
- `.github/workflows/ci.yml` 存在
- PR 合并前自动运行 lint + test + smoke + brand-guard
- 旧品牌名混入时 CI 自动失败

---

## P4：功能扩展与深度本地化（中长期路线图）

### 21. 国内网络加速与镜像指引

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 几乎无 — 仅 `__init__.py` L734 有一句泛泛的"配置代理"提示 |
| **涉及文件** | `src/specify_cli/__init__.py`、新建 `docs/china-network.md` |

**操作步骤：**

1. [ ] 在 `init` / `extension install` 网络超时 catch 块中增加具体指引：
   - 检测 `HTTPS_PROXY` / `HTTP_PROXY` 环境变量是否已设置
   - 未设置时输出：`"提示：如在国内网络环境下，请设置代理：export HTTPS_PROXY=http://127.0.0.1:7890"`
2. [ ] 新建 `docs/china-network.md`，内容覆盖：
   - PyPI 国内镜像配置（清华源/阿里源）
   - GitHub 加速方案（ghproxy、fastgit 等）
   - `HTTPS_PROXY` 配置方法
   - 离线安装方案

**验收标准：**
- 网络超时错误中包含国内代理设置提示
- `docs/china-network.md` 文件存在

---

### 22. AI 指令模板深度本地化

| 维度 | 信息 |
|------|------|
| **当前状态** | 🟡 大部分完成 — 9 个命令模板的 frontmatter 和标题已中文化，但指令正文仍有英文 |
| **涉及文件** | `templates/commands/*.md`（9 个文件） |

**操作步骤：**

1. [ ] 逐文件翻译指令正文（保留代码块和变量引用为英文）：
   - `specify.md` L36-88 英文步骤说明 → 中文
   - `plan.md` 英文步骤 → 中文
   - `implement.md` 英文步骤 → 中文
   - 其他 6 个文件同理
2. [ ] 优化提示词结构：按国内 AI 工具使用习惯调整指令措辞（更直接、步骤化）
3. [ ] 在每个模板 `## 语言要求` 段落中统一标注"请用简体中文回复"

**验收标准：**
- `templates/commands/` 下所有 `.md` 文件正文为中文（代码/变量除外）
- 每个模板包含"简体中文回复"要求

---

### 23. 国内大模型/工具生态接入

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未开始 — 代码中无国内大模型相关引用 |
| **涉及文件** | `src/specify_cli/__init__.py` AGENT_CONFIG、新建 `docs/domestic-llm.md` |

**操作步骤：**

1. [ ] 在 `docs/domestic-llm.md` 中撰写以下内容：
   - 通义灵码 + SDD 工作流最佳实践
   - DeepSeek Coder + SDD 工作流指南
   - 其他国内 AI 编码工具适配说明
2. [ ] 调研国内 AI 编码 CLI 工具（如有），评估是否添加到 `AGENT_CONFIG`
3. [ ] 在 README `## 🤖 支持的 AI 编码工具` 段落中增加国内工具说明

**验收标准：**
- `docs/domestic-llm.md` 文件存在，包含至少两个国内大模型的使用指南
- README 中提及国内大模型生态支持

---

### 24. 上游版本同步机制

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未开始 — 目录 URL 硬编码上游地址（`extensions.py` L991-992），但无自动同步 |
| **涉及文件** | 新建 `.github/workflows/upstream-sync.yml`、新建 `docs/upstream-sync.md` |

**操作步骤：**

1. [ ] 新建 `.github/workflows/upstream-sync.yml`：
   - 每周定时触发（`cron: "0 3 * * 1"`）
   - Checkout 上游 `github/spec-kit` 最新 release
   - 与本地 `main` 分支 diff，输出变更文件列表
   - 自动创建 issue 标注需要中文化的变更
2. [ ] 新建 `docs/upstream-sync.md`，明确：
   - 版本号跟随规则：大版本跟随上游，中/小版本独立递增
   - 合并策略：cherry-pick 功能性变更，忽略纯英文文案变更
   - 冲突处理优先级：中文化内容 > 上游原文

**验收标准：**
- `.github/workflows/upstream-sync.yml` 文件存在
- 上游更新后一周内自动生成同步 issue

---

### 25. 中文文档死链扫描

| 维度 | 信息 |
|------|------|
| **当前状态** | 🔴 未开始 — 无链接检查工具 |
| **涉及文件** | 新建 `.github/workflows/link-check.yml`、更新 `Makefile` |

**操作步骤：**

1. [ ] 在 CI 中添加 `lychee` 或 `markdown-link-check` 工具：
   ```yaml
   # .github/workflows/link-check.yml
   - uses: lycheeverse/lychee-action@v2
     with:
       args: --verbose --no-progress '**/*.md'
       fail: true
   ```
2. [ ] 在 `Makefile` 中添加本地检查目标：
   ```makefile
   link-check:
       npx markdown-link-check README.md docs/*.md
   ```
3. [ ] 首次运行，修复发现的所有死链

**验收标准：**
- `make link-check` 本地可执行且通过
- CI PR 检查中包含链接检查步骤
- 全部 `.md` 文件无 404 链接

---

## 附录：执行优先级与依赖关系

```
执行顺序建议（→ 表示依赖）：

第一批（阻塞发布）：
  P0-1 品牌统一
  P0-2 Extension 中文化   → 依赖 P0-1 的品牌修正
  P0-3 安装验证说明
  P0-4 Smoke Test

第二批（核心体验）：
  P3-17 抽取常量          → 先于 P0-1/P0-2 执行可降低工作量，也可事后重构
  P1-10 version 增强
  P1-5 doctor 增强
  P1-9 check 展示优化

第三批（交互增强）：
  P1-6 init 交互          → 为 P1-7 和 P1-8 打基础
  P1-7 init --dry-run     → 依赖 P1-6
  P1-8 init --json        → 依赖 P1-6

第四批（文档完善）：
  P2-13 文档语言一致性    → 工作量最大的文档项
  P2-11 README 优化
  P2-12 徽章优化
  P2-14 迁移指南
  P2-15 常见问题文档

第五批（工程保障）：
  P3-16 输出快照测试      → 依赖 P0-1/P0-2 完成后才有意义
  P3-18 术语统一          → 依赖 P2-13
  P3-19 发布检查清单
  P3-20 CI 校验           → 依赖 P0-4 smoke test

第六批（中长期）：
  P4-21 网络加速
  P4-22 模板本地化
  P4-23 国内大模型接入
  P4-24 上游同步
  P4-25 死链扫描
```

---

## 统计总览

| 优先级 | 项数 | 完成度 | 预估总工时 |
|--------|------|--------|-----------|
| **P0** | 4 项 | 🔴 ~10% | 3-4 天 |
| **P1** | 6 项 | 🟡 ~25% | 4-5 天 |
| **P2** | 5 项 | 🟡 ~15% | 3-4 天 |
| **P3** | 5 项 | 🔴 ~5% | 2-3 天 |
| **P4** | 5 项 | 🔴 ~5% | 5-7 天 |
| **合计** | **25 项** | **~12%** | **17-23 天** |
