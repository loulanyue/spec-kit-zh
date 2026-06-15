<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 国内网络环境加速与排障指引

`specify-cli-zh` 工具包的正常运行强依赖于 GitHub 与各类包管理器的官方源。由于国内网络环境极其不稳定，在初始化工程模板及拉取大模型客户端时，常会遇到 `ConnectTimeout` 或 HTTP 响应报错。请仔细阅读本快速行动指南。

---

## 场景一：终端命令卡住 / 拉取超时

在执行 `specify-zh init`、`specify-zh extension install` 等网络操作指令报错时，推荐通过配置命令行全局代理突破网络限制。

> [!TIP]
> 确信你的个人电脑上已安装并启用了能够科学上网的代理客户端（如 Clash、V2Ray 等），并核对局域网默认代理通讯端口。以下举例默认为常见的 `7890` 端口。

**macOS / Linux（bash/zsh）：**

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890
```

**Windows PowerShell：**

```powershell
$env:HTTPS_PROXY="http://127.0.0.1:7890"
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:ALL_PROXY="socks5://127.0.0.1:7890"
```

以上配置可解决 90% 由于与 `.githubusercontent.com` 以及 `api.github.com` 断联所产生的问题。

> [!NOTE]
> 代理配置仅在当前终端会话生效。如需永久生效，请将上述 `export` 语句加入 `~/.zshrc`（macOS Zsh）或 `~/.bashrc`（Linux Bash）。

---

## 场景二：Python 生态拉取龟速

当你首次执行 `uv tool install` 或更新内部 `pip` 生态时遇到极长等待或 SSL 报错，请切换至国内镜像。

### PyPI 镜像

```bash
# 清华大学镜像（推荐）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云镜像（备选）
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 中国科技大学镜像（备选）
pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/
```

### uv 镜像

`uv` 支持通过环境变量配置镜像，临时使用：

```bash
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
```

或在 `pyproject.toml` 中永久配置（适用于项目级开发）：

```toml
[[tool.uv.index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

---

## 场景三：离线手动分发策略

若因企业内网隔离策略完全无法通过公网连接 GitHub，可预先下载模板压缩包在本地使用。

1. 在有公网访问的机器上，前往 [spec-kit-zh 发行版页面](https://github.com/loulanyue/spec-kit-zh/releases) 下载对应的模板包，例如：
   - `spec-kit-template-claude-sh-<version>.zip`
   - `spec-kit-template-codex-sh-<version>.zip`
   - `spec-kit-template-kiro-cli-sh-<version>.zip`
   - `spec-kit-template-tabnine-sh-<version>.zip`
   - `spec-kit-template-copilot-sh-<version>.zip`

2. 将 `.zip` 包复制到隔离机器后本地解压，然后使用本地模板初始化：

```bash
specify-zh init my-project --template-dir /path/to/unzipped-template
```

---

## 场景四：Git 克隆 GitHub 仓库速度慢

如果直接 `git clone https://github.com/...` 速度极慢，可尝试以下加速方案：

### 方案 A：使用 SSH 协议（需配置 SSH 密钥）

```bash
git clone git@github.com:loulanyue/spec-kit-zh.git
```

### 方案 B：使用 GitHub 镜像加速站

```bash
# ghfast.top（第三方，请自行评估风险）
git clone https://ghfast.top/https://github.com/loulanyue/spec-kit-zh.git
```

### 方案 C：设置 Git 全局代理

```bash
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 完成后若要取消
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 场景五：GitHub Token 避免限流

若你的终端访问频率过高被 GitHub 触发 Rate Limit（HTTP 403），可主动签发一个 Personal Access Token：

1. 前往 [GitHub Developer Settings → Tokens](https://github.com/settings/tokens)
2. 点击 **Generate new token (classic)**，无需勾选任何权限
3. 获取形如 `ghp_xxxx` 的 Token

在终端中赋予凭证：

```bash
export GITHUB_TOKEN=ghp_XXXXXXXyourtokenXXXXXX
specify-zh init ...
```

或通过 GitHub CLI 登录（推荐，可持久保存凭证）：

```bash
gh auth login
```

---

## 快速诊断命令

遇到网络问题时，可运行以下命令快速诊断：

```bash
# 检测是否能访问 GitHub API
curl -s https://api.github.com/zen

# 检测 PyPI 是否可访问
curl -s https://pypi.org/pypi/pip/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"

# 查看当前代理配置
echo "HTTP_PROXY=$HTTP_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"
```
