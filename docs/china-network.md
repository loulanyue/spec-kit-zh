<!-- spec-kit-zh repo note: package `specify-cli-zh`, command `specify-zh`. -->

# 国内网络环境加速与排障指引

`specify-cli-zh` 工具包的正常运行强依赖于 GitHub 与各类包管理器的官方源。由于国内网络环境极其不稳定，在初始化工程模板及拉取大模型客户端时，常会遇到 `ConnectTimeout` 或 HTTP 响应报错。请仔细阅读本快速行动指南。

## 场景一：终端命令卡住 / 拉取目标超时

在执行诸如 `specify-zh init`、`specify-zh extension install` 等网络操作指令报错时，推荐通过配置命令行全局代理来突破网络限制。

> [!TIP]
> 确信你的个人电脑上安装并启用了能够科学上网的代理客户端（如 Clash、V2Ray 等），并核对局域网默认代理通讯端口。以下举例默认为常见的 `7890` 端口。

如果问题严重，请在所有 `specify-zh` 操作的前置步骤通过命令行追加环境变量：

**在 macOS/Linux 等 `bash`/`zsh` 终端：**
```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export ALL_PROXY=socks5://127.0.0.1:7890
```

**在 Windows PowerShell 终端：**
```powershell
$env:HTTPS_PROXY="http://127.0.0.1:7890"
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:ALL_PROXY="socks5://127.0.0.1:7890"
```

这能够解决 90% 的因为与 `.githubusercontent.com` 以及 `api.github.com` 断联所产生的问题。

## 场景二：Python 生态拉取安装龟速

当你首次执行 `uv tool install` 或更新内部 `pip` 生态遇到极长等待时间或 SSL 抛错时，请尝试切换至清华镜像或阿里云镜像。

**PyPI (pip) 清华镜像设置**
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**uv 安装器镜像设置**
`uv` 也支持配置 `index-url`，可以在终端执行如下环境变量申明后再进行下载：
```bash
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
uv tool install specify-cli-zh --from git+https://github.com/loulanyue/spec-kit-zh.git
```

## 场景三：离线手动分发策略

若因为某些企业内网隔离策略，完全无法通过公网连接到 GitHub 进行远端仓库拉取，你可以预先下载好对应的模板资源压缩包并在本地使用。

你可以在任何正常的公网环境中，打开浏览器获取模板的二进制包。请前往 [spec-kit-zh 发行版页面](https://github.com/loulanyue/spec-kit-zh/releases)，并根据自己期望组合的 AI 大模型名称寻找下载对口的 Zip 文件，例如你想用 Claude，就下载类似 `spec-kit-template-claude-sh-<version>.zip` 的文件。

常见的离线模板包命名模式包括：

- `spec-kit-template-claude-sh-<version>.zip`
- `spec-kit-template-codex-sh-<version>.zip`
- `spec-kit-template-kiro-cli-sh-<version>.zip`
- `spec-kit-template-tabnine-sh-<version>.zip`

将该 `.zip` 压缩包复制进入你的隔离办公机内并进行本地解压拿到 `.specify` 即等价操作。或者通过设置本地指定目录进行构建：

```bash
specify-zh init my-project --template-dir /path/to/my/local/template-unzipped
```

## 延伸：GitHub Token 无视频次访问墙

若你的终端访问频率过高被 GitHub 触发 Rate Limit（限流）而产生封锁（表现为 HTTP 403 连带请求时间惩罚），我们建议你主动签发一个用于规避限流的开发级强认证身份：

1. 前往 [GitHub Developer Settings](https://github.com/settings/tokens)
2. 点击 Generate new token (classic)。无需给任何权限（甚至不要勾选 repo，除非你需要使用 `gh` 直接提 PR）
3. 获取这串代号为 `ghp_xxxx` 的 Token。

为本地赋予凭证，执行：
```bash
export GITHUB_TOKEN=ghp_XXXXXXXyourtokenXXXXXX
# 再执行业务
specify-zh init ...
```
