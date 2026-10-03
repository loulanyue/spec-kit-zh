"""Template downloading, extraction, bundling, constitution, and agent skills installation."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional, Tuple

import httpx
import typer
import yaml
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from specify_cli.agents import (
    AGENT_CONFIG,
    AI_ASSISTANT_ALIASES,
    SKILL_DESCRIPTIONS,
    TOML_AGENTS,
    _get_skills_dir,
)
from specify_cli.codex_prompts import (
    DEFAULT_CODEX_PROMPTS_DIR as CODEX_GLOBAL_PROMPTS_DIR,
    normalize_speckit_name as _normalize_speckit_name,
    render_codex_prompt as _render_codex_prompt,
    sync_codex_prompts_from_templates,
)
from specify_cli.git import handle_vscode_settings
from specify_cli.network import (
    FALLBACK_GITLAB_INSTALL_URL,
    FALLBACK_GITLAB_REPO_URL,
    _format_rate_limit_error,
    _github_auth_headers,
    resolve_mirror_url,
    ssl_context,
)
from specify_cli.ui import StepTracker, console

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None

BUNDLED_DOCS_DIR = Path(__file__).resolve().parent / "_bundled_docs"
BUNDLED_CORE_DIR = Path(__file__).resolve().parent / "_bundled_core"
BUNDLED_TEMPLATES_DIR = Path(__file__).resolve().parent / "_bundled_templates"
CONVENTIONS_DIRNAME = "conventions"


def _resolve(name: str, fallback: Any) -> Any:
    """Resolve symbol from sys.modules['specify_cli'] if available (supports unittest.mock.patch)."""
    pkg = sys.modules.get("specify_cli")
    if pkg is not None and hasattr(pkg, name):
        return getattr(pkg, name)
    return fallback


def _repo_root_from_source() -> Path | None:
    """Return the local repository root when running from source checkout."""
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "templates").exists() and (repo_root / "scripts").exists():
        return repo_root
    return None


def _bundled_asset_root_from_package() -> Path | None:
    """Return packaged template/script assets for installed wheels, if present."""
    if (BUNDLED_CORE_DIR / "templates").is_dir() and (
        BUNDLED_CORE_DIR / "scripts"
    ).is_dir():
        return BUNDLED_CORE_DIR
    return None


def _parse_markdown_command_template(template_path: Path) -> tuple[dict, str]:
    """Parse markdown command template into frontmatter and body."""
    content = template_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            if not isinstance(frontmatter, dict):
                frontmatter = {}
            return frontmatter, parts[2].strip() + "\n"
    return {}, content


def _render_agent_command(template_path: Path, ai_assistant: str) -> tuple[str, str]:
    """Render a generic command template into the selected agent's command format."""
    command_name = template_path.stem
    frontmatter, body = _parse_markdown_command_template(template_path)
    description = str(frontmatter.get("description", "")).strip()

    if ai_assistant == "codex":
        return _render_codex_prompt(template_path)

    if ai_assistant in TOML_AGENTS:
        prompt_body = body.replace("$ARGUMENTS", "{{args}}").rstrip()
        lines = []
        if description:
            lines.append(f"description = {json.dumps(description, ensure_ascii=False)}")
            lines.append("")
        lines.append('prompt = """')
        lines.append(prompt_body)
        lines.append('"""')
        return f"speckit.{command_name}.toml", "\n".join(lines) + "\n"

    rendered_frontmatter = dict(frontmatter)
    if ai_assistant == "copilot":
        rendered_frontmatter["mode"] = f"speckit.{command_name}"
    frontmatter_text = yaml.safe_dump(
        rendered_frontmatter, sort_keys=False, allow_unicode=True
    ).strip()
    content = f"---\n{frontmatter_text}\n---\n\n{body.rstrip()}\n"
    return f"speckit.{command_name}.md", content


def _build_template_tree_from_source(
    source_root: Path, staging_root: Path, ai_assistant: str
) -> None:
    """Build a project template tree from a source checkout."""
    specify_root = staging_root / ".specify"
    templates_target = specify_root / "templates"
    scripts_target = specify_root / "scripts"

    shutil.copytree(source_root / "templates", templates_target, dirs_exist_ok=True)
    shutil.copytree(source_root / "scripts", scripts_target, dirs_exist_ok=True)

    vscode_settings = source_root / "templates" / "vscode-settings.json"
    if vscode_settings.exists():
        vscode_dir = staging_root / ".vscode"
        vscode_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(vscode_settings, vscode_dir / "settings.json")

    commands_source = source_root / "templates" / "commands"
    if not commands_source.exists():
        return

    if ai_assistant == "generic":
        command_target = staging_root / ".speckit" / "commands"
    else:
        agent_config = AGENT_CONFIG.get(ai_assistant, {})
        agent_folder = agent_config.get("folder")
        commands_subdir = agent_config.get("commands_subdir", "commands")
        if not agent_folder:
            return
        command_target = staging_root / agent_folder.rstrip("/") / commands_subdir

    command_target.mkdir(parents=True, exist_ok=True)
    for template_path in sorted(commands_source.glob("*.md")):
        filename, rendered = _render_agent_command(template_path, ai_assistant)
        (command_target / filename).write_text(rendered, encoding="utf-8")


def _copy_tree_into_project(
    source_dir: Path,
    project_path: Path,
    is_current_dir: bool,
    *,
    verbose: bool = True,
    tracker: StepTracker | None = None,
) -> None:
    """Copy a staged template tree into the target project path."""
    if is_current_dir:
        for item in source_dir.iterdir():
            dest_path = project_path / item.name
            if item.is_dir():
                if dest_path.exists():
                    for sub_item in item.rglob("*"):
                        if sub_item.is_file():
                            rel_path = sub_item.relative_to(item)
                            dest_file = dest_path / rel_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            if (
                                dest_file.name == "settings.json"
                                and dest_file.parent.name == ".vscode"
                            ):
                                handle_vscode_settings(
                                    sub_item, dest_file, rel_path, verbose, tracker
                                )
                            else:
                                shutil.copy2(sub_item, dest_file)
                else:
                    shutil.copytree(item, dest_path)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_path)
        return

    project_path.mkdir(parents=True, exist_ok=True)
    for item in source_dir.iterdir():
        dest_path = project_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest_path, dirs_exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_path)


def bootstrap_template_from_fallback_source(
    project_path: Path,
    ai_assistant: str,
    script_type: str,
    is_current_dir: bool = False,
    *,
    verbose: bool = True,
    tracker: StepTracker | None = None,
    debug: bool = False,
    offline: bool = False,
) -> Path:
    """Bootstrap a project from bundled assets, GitLab mirror, or local source."""
    clone_dir = None
    source_root = None
    clone_error = None
    source_label = None

    bundled_asset_fn = _resolve(
        "_bundled_asset_root_from_package", _bundled_asset_root_from_package
    )
    repo_root_fn = _resolve("_repo_root_from_source", _repo_root_from_source)

    if offline:
        if tracker:
            tracker.start("fetch", "纯离线模式：加载本地内置模板")
        source_root = bundled_asset_fn()
        if source_root is not None:
            source_label = "内置模板包"
            if tracker:
                tracker.complete("fetch", "纯离线模式：已加载内置模板包")
        else:
            source_root = repo_root_fn()
            if source_root is not None:
                source_label = "本地源码模板"
                if tracker:
                    tracker.complete("fetch", "纯离线模式：已加载本地源码模板")
            else:
                if tracker:
                    tracker.error("fetch", "未找到本地内置模板包")
                raise RuntimeError(
                    "离线模式下未找到内置模板资产包或本地源码模板。\n"
                    "请确认 specify-cli-zh 安装完整，或在联网状态下运行 specify-zh init。"
                )
    else:
        if tracker:
            tracker.start("fetch", "GitHub 不可用，尝试内置模板/备用源")

        source_root = bundled_asset_fn()
        if source_root is not None:
            source_label = "内置模板包"
            if tracker:
                tracker.complete("fetch", "已切换到内置模板包")
        else:
            try:
                temp_clone_parent = Path(
                    tempfile.mkdtemp(prefix="spec-kit-zh-fallback-")
                )
                clone_dir = temp_clone_parent / "repo"
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        FALLBACK_GITLAB_REPO_URL,
                        str(clone_dir),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                source_root = clone_dir
                source_label = "GitLab 镜像"
                if tracker:
                    tracker.complete("fetch", "已切换到 GitLab 镜像源")
            except Exception as exc:
                clone_error = str(exc)
                source_root = repo_root_fn()
                if source_root is not None:
                    source_label = "本地源码"
                    if tracker:
                        tracker.complete("fetch", "GitLab 不可用，改用本地源码模板")
                elif tracker:
                    tracker.error("fetch", f"GitLab 镜像失败：{clone_error}")

        if source_root is None:
            raise RuntimeError(
                "GitHub release 拉取失败，且无法从内置模板包、GitLab 镜像或本地源码构建模板。\n"
                f"可手动安装/更新：uv tool install specify-cli-zh --from {FALLBACK_GITLAB_INSTALL_URL}"
            )

    if tracker:
        tracker.add("download", "下载模板")
        tracker.skip("download", "已改用源码构建，无需下载 zip")
        tracker.add("extract", "解压模板")
        tracker.start("extract", "从源码构建模板树")

    build_tree_fn = _resolve(
        "_build_template_tree_from_source", _build_template_tree_from_source
    )
    copy_tree_fn = _resolve("_copy_tree_into_project", _copy_tree_into_project)

    with tempfile.TemporaryDirectory(prefix="spec-kit-zh-stage-") as staging_dir:
        staging_root = Path(staging_dir)
        build_tree_fn(source_root, staging_root, ai_assistant)
        copy_tree_fn(
            staging_root, project_path, is_current_dir, verbose=verbose, tracker=tracker
        )

    if tracker:
        tracker.complete("extract", f"已从 {source_label or '备用源'} 构建模板")
        tracker.add("cleanup", "清理临时压缩包")
        tracker.skip("cleanup", "未生成 zip 文件")

    if clone_dir is not None:
        shutil.rmtree(clone_dir.parent, ignore_errors=True)

    return project_path


def download_template_from_github(
    ai_assistant: str,
    download_dir: Path,
    *,
    script_type: str = "sh",
    verbose: bool = True,
    show_progress: bool = True,
    client: httpx.Client = None,
    debug: bool = False,
    github_token: str = None,
    mirror: str | None = None,
) -> Tuple[Path, dict]:
    repo_owner = "github"
    repo_name = "spec-kit"
    if client is None:
        client = httpx.Client(verify=ssl_context)

    auth_headers_fn = _resolve("_github_auth_headers", _github_auth_headers)
    format_limit_fn = _resolve("_format_rate_limit_error", _format_rate_limit_error)

    if verbose:
        console.print("[cyan]正在获取最新发布信息...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = client.get(
            api_url,
            timeout=30,
            follow_redirects=True,
            headers=auth_headers_fn(github_token),
        )
        status = response.status_code
        if status != 200:
            error_msg = format_limit_fn(status, response.headers, api_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
            raise RuntimeError(error_msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(
                f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}"
            )
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
        raise RuntimeError(
            "连接 GitHub API 超时或失败。\n"
            "如在国内网络环境下，请设置终端代理，例如：\n"
            "  export HTTPS_PROXY=http://127.0.0.1:7890\n"
            "  export HTTP_PROXY=http://127.0.0.1:7890\n"
            "或使用纯离线模式：specify-zh init --offline\n"
            f"原始错误：{e}"
        )
    except Exception as e:
        raise RuntimeError(str(e))

    assets = release_data.get("assets", [])
    pattern = f"spec-kit-template-{ai_assistant}-{script_type}"
    matching_assets = [
        asset
        for asset in assets
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        asset_names = [a.get("name", "?") for a in assets]
        raise RuntimeError(
            f"未找到匹配的发布资产：{ai_assistant}（期望模式：{pattern}）。\n"
            f"可用资产：{', '.join(asset_names) if asset_names else '（无资产）'}"
        )

    raw_download_url = asset["browser_download_url"]
    download_url = resolve_mirror_url(raw_download_url, mirror)
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        console.print(f"[cyan]已找到模板：[/cyan] {filename}")
        console.print(f"[cyan]大小：[/cyan] {file_size:,} 字节")
        console.print(f"[cyan]发布版本：[/cyan] {release_data['tag_name']}")
        if download_url != raw_download_url:
            console.print(f"[cyan]加速镜像下载：[/cyan] {download_url}")

    zip_path = download_dir / filename
    if verbose:
        console.print("[cyan]正在下载模板...[/cyan]")

    try:
        with client.stream(
            "GET",
            download_url,
            timeout=60,
            follow_redirects=True,
            headers=auth_headers_fn(github_token),
        ) as response:
            if response.status_code != 200:
                error_msg = format_limit_fn(
                    response.status_code, response.headers, download_url
                )
                if debug:
                    error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{response.text[:400]}"
                raise RuntimeError(error_msg)
            total_size = int(response.headers.get("content-length", 0))
            with open(zip_path, "wb") as f:
                if total_size == 0:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("下载中...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
        raise RuntimeError(
            "下载模板数据包网络连接超时或失败。\n"
            "如在国内网络环境下，请设置网络代理，或查阅 docs/china-network.md 获取加速方案。\n"
            f"原始错误：{e}"
        )
    except Exception as e:
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        raise RuntimeError(f"下载模板失败：{detail}")
    if verbose:
        console.print(f"已下载：{filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url,
    }
    return zip_path, metadata


def download_and_extract_template(
    project_path: Path,
    ai_assistant: str,
    script_type: str,
    is_current_dir: bool = False,
    *,
    verbose: bool = True,
    tracker: StepTracker | None = None,
    client: httpx.Client = None,
    debug: bool = False,
    github_token: str = None,
    offline: bool = False,
    mirror: str | None = None,
) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    download_github_fn = _resolve(
        "download_template_from_github", download_template_from_github
    )
    bootstrap_fallback_fn = _resolve(
        "bootstrap_template_from_fallback_source",
        bootstrap_template_from_fallback_source,
    )

    if offline:
        return bootstrap_fallback_fn(
            project_path,
            ai_assistant,
            script_type,
            is_current_dir,
            verbose=verbose,
            tracker=tracker,
            debug=debug,
            offline=True,
        )

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_github_fn(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token,
            mirror=mirror,
        )
        if tracker:
            tracker.complete(
                "fetch", f"release {meta['release']} ({meta['size']:,} bytes)"
            )
            tracker.add("download", "Download template")
            tracker.complete("download", meta["filename"])
    except Exception as e:
        if tracker is None and verbose:
            console.print(f"[yellow]GitHub 模板拉取失败，准备尝试备用源：[/yellow] {e}")
        try:
            return bootstrap_fallback_fn(
                project_path,
                ai_assistant,
                script_type,
                is_current_dir,
                verbose=verbose,
                tracker=tracker,
                debug=debug,
                offline=False,
            )
        except Exception as fallback_error:
            if tracker:
                tracker.error("fetch", str(fallback_error))
            else:
                if verbose:
                    console.print(f"[red]下载模板出错：[/red] {e}")
                    console.print(f"[red]备用源也失败：[/red] {fallback_error}")
            raise

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete(
                            "extracted-summary", f"temp {len(extracted_items)} items"
                        )
                    elif verbose:
                        console.print(
                            f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]"
                        )

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(
                                "[cyan]Found nested directory structure[/cyan]"
                            )

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(
                                        f"[yellow]Merging directory:[/yellow] {item.name}"
                                    )
                                for sub_item in item.rglob("*"):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(
                                            parents=True, exist_ok=True
                                        )
                                        if (
                                            dest_file.name == "settings.json"
                                            and dest_file.parent.name == ".vscode"
                                        ):
                                            handle_vscode_settings(
                                                sub_item,
                                                dest_file,
                                                rel_path,
                                                verbose,
                                                tracker,
                                            )
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(
                                    f"[yellow]Overwriting file:[/yellow] {item.name}"
                                )
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print(
                            "[cyan]Template files merged into current directory[/cyan]"
                        )
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete(
                        "extracted-summary", f"{len(extracted_items)} top-level items"
                    )
                elif verbose:
                    console.print(
                        f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]"
                    )
                    for item in extracted_items:
                        console.print(
                            f"  - {item.name} ({'dir' if item.is_dir() else 'file'})"
                        )

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(
                            "[cyan]Flattened nested directory structure[/cyan]"
                        )

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]解压模板出错：[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="解压错误", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "清理临时压缩包")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"已清理：{zip_path.name}")

    return project_path


def ensure_executable_scripts(
    project_path: Path, tracker: StepTracker | None = None
) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".specify" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat()
            mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400:
                new_mode |= 0o100
            if mode & 0o040:
                new_mode |= 0o010
            if mode & 0o004:
                new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (
            f", {len(failures)} failed" if failures else ""
        )
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(
                f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]"
            )
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")


def ensure_constitution_from_template(
    project_path: Path, tracker: StepTracker | None = None
) -> None:
    """Copy constitution template to memory if it doesn't exist (preserves existing constitution on reinitialization)."""
    memory_constitution = project_path / ".specify" / "memory" / "constitution.md"
    template_constitution = (
        project_path / ".specify" / "templates" / "constitution-template.md"
    )

    if memory_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.skip("constitution", "existing file preserved")
        return

    if not template_constitution.exists():
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", "template not found")
        return

    try:
        memory_constitution.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_constitution, memory_constitution)
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.complete("constitution", "copied from template")
        else:
            console.print("[cyan]已从模板初始化章程[/cyan]")
    except Exception as e:
        if tracker:
            tracker.add("constitution", "Constitution setup")
            tracker.error("constitution", str(e))
        else:
            console.print(f"[yellow]警告：无法初始化章程：{e}[/yellow]")


def _get_conventions_registry_path() -> Path | None:
    """Return the best available conventions registry path."""
    bundled_registry = BUNDLED_DOCS_DIR / "conventions.yml"
    if bundled_registry.exists():
        return bundled_registry

    repo_registry = Path(__file__).resolve().parents[2] / "docs" / "conventions.yml"
    if repo_registry.exists():
        return repo_registry

    return None


def ensure_coding_conventions_from_docs(
    project_path: Path, tracker: StepTracker | None = None
) -> None:
    """Copy default coding conventions into `.specify/memory/conventions/`."""
    registry_path = _get_conventions_registry_path()
    step_name = "conventions"

    if registry_path is None:
        if tracker:
            tracker.add(step_name, "初始化编码规范")
            tracker.skip(step_name, "未找到规范清单")
        return

    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        if tracker:
            tracker.add(step_name, "初始化编码规范")
            tracker.error(step_name, f"规范清单解析失败：{e}")
        else:
            console.print(f"[yellow]警告：无法解析编码规范清单：{e}[/yellow]")
        return

    conventions = data.get("conventions", [])
    if not isinstance(conventions, list):
        if tracker:
            tracker.add(step_name, "初始化编码规范")
            tracker.error(step_name, "规范清单格式无效")
        else:
            console.print("[yellow]警告：编码规范清单格式无效，跳过初始化[/yellow]")
        return

    target_dir = project_path / ".specify" / "memory" / CONVENTIONS_DIRNAME
    target_dir.mkdir(parents=True, exist_ok=True)

    copied: list[tuple[str, str]] = []
    preserved = 0
    skipped = 0

    for convention in conventions:
        if not isinstance(convention, dict):
            skipped += 1
            continue
        if not convention.get("enabled_by_default", False):
            continue

        title = str(convention.get("title", "")).strip()
        relative_path = str(convention.get("path", "")).strip()
        if not title or not relative_path:
            skipped += 1
            continue

        source_path = registry_path.parent / relative_path
        if not source_path.exists():
            skipped += 1
            continue

        destination = target_dir / source_path.name
        if destination.exists():
            preserved += 1
        else:
            shutil.copy2(source_path, destination)
            copied.append((title, destination.name))

    index_path = target_dir / "README.md"
    index_lines = [
        "# 项目编码规范索引",
        "",
        "以下规范在项目初始化时已启用。涉及对应领域实现时，应优先遵循这些项目规范。",
        "",
    ]

    enabled_entries: list[tuple[str, str]] = []
    for convention in conventions:
        if not isinstance(convention, dict) or not convention.get(
            "enabled_by_default", False
        ):
            continue
        title = str(convention.get("title", "")).strip()
        relative_path = str(convention.get("path", "")).strip()
        if not title or not relative_path:
            continue
        filename = Path(relative_path).name
        enabled_entries.append((title, filename))

    if enabled_entries:
        index_lines.append("## 已启用规范")
        index_lines.append("")
        for title, filename in enabled_entries:
            index_lines.append(f"- [{title}](./{filename})")
    else:
        index_lines.append("当前没有默认启用的编码规范。")

    index_lines.extend(
        [
            "",
            "## 使用说明",
            "",
            "- 在规划、拆任务、实现前，先阅读与当前工作最相关的规范文件。",
            "- 如项目规范与通用最佳实践冲突，以项目规范为准。",
            "- 若需新增规范，可继续在此目录补充文档并更新索引。",
        ]
    )
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    if tracker:
        tracker.add(step_name, "初始化编码规范")
        detail_parts = []
        if copied:
            detail_parts.append(f"新增 {len(copied)} 份")
        if preserved:
            detail_parts.append(f"保留 {preserved} 份")
        if skipped:
            detail_parts.append(f"跳过 {skipped} 份")
        tracker.complete(step_name, "，".join(detail_parts) or "已生成索引")
    else:
        console.print(
            f"[cyan]已初始化编码规范目录：{target_dir.relative_to(project_path)}[/cyan]"
        )


def _get_command_templates_dir() -> Path | None:
    """Return the best available command template directory."""
    bundled_dir = BUNDLED_TEMPLATES_DIR / "commands"
    if bundled_dir.exists():
        return bundled_dir

    repo_dir = Path(__file__).resolve().parents[2] / "templates" / "commands"
    if repo_dir.exists():
        return repo_dir

    return None


def ensure_codex_prompts_from_templates(
    project_path: Path, selected_ai: str, tracker: StepTracker | None = None
) -> None:
    """Materialize Codex prompt files into project and global prompt directories."""
    step_name = "codex-prompts"

    if selected_ai != "codex":
        if tracker:
            tracker.add(step_name, "补齐 Codex prompts")
            tracker.skip(step_name, "当前 agent 非 Codex")
        return

    templates_dir = _get_command_templates_dir()
    if templates_dir is None:
        if tracker:
            tracker.add(step_name, "补齐 Codex prompts")
            tracker.error(step_name, "未找到命令模板")
        else:
            console.print("[yellow]警告：未找到 Codex prompt 模板，跳过补齐[/yellow]")
        return

    command_templates = sorted(templates_dir.glob("*.md"))
    if not command_templates:
        if tracker:
            tracker.add(step_name, "补齐 Codex prompts")
            tracker.error(step_name, "命令模板目录为空")
        else:
            console.print("[yellow]警告：Codex prompt 模板目录为空，跳过补齐[/yellow]")
        return

    result = sync_codex_prompts_from_templates(
        command_templates,
        project_path,
        global_prompts_dir=CODEX_GLOBAL_PROMPTS_DIR,
        overwrite=True,
    )

    if tracker:
        tracker.add(step_name, "补齐 Codex prompts")
        detail_parts = []
        if result.created:
            detail_parts.append(f"新增 {result.created} 个")
        if result.updated:
            detail_parts.append(f"更新 {result.updated} 个")
        if result.preserved:
            detail_parts.append(f"保留 {result.preserved} 个")
        detail_parts.append(f"目标：{CODEX_GLOBAL_PROMPTS_DIR}")
        tracker.complete(step_name, "，".join(detail_parts))
    else:
        console.print(
            f"[cyan]已为 Codex 同步 prompts：[/cyan] "
            f"{result.project_prompts_dir} 和 {result.global_prompts_dir}"
        )


def install_ai_skills(
    project_path: Path, selected_ai: str, tracker: StepTracker | None = None
) -> bool:
    """Install Prompt.MD files from templates/commands/ as agent skills.

    Skills are written to the agent-specific skills directory following the
    `agentskills.io <https://agentskills.io/specification>`_ specification.
    Installation is additive — existing files are never removed and prompt
    command files in the agent's commands directory are left untouched.

    Args:
        project_path: Target project directory.
        selected_ai: AI assistant key from ``AGENT_CONFIG``.
        tracker: Optional progress tracker.

    Returns:
        ``True`` if at least one skill was installed or all skills were
        already present (idempotent re-run), ``False`` otherwise.
    """
    agent_config = AGENT_CONFIG.get(selected_ai, {})
    agent_folder = agent_config.get("folder", "")
    commands_subdir = agent_config.get("commands_subdir", "commands")
    if agent_folder:
        templates_dir = project_path / agent_folder.rstrip("/") / commands_subdir
    else:
        templates_dir = project_path / commands_subdir

    def _supported_command_files(directory: Path) -> list[Path]:
        return sorted([*directory.glob("*.md"), *directory.glob("*.toml")])

    def _parse_command_template(command_file: Path) -> tuple[dict, str, str]:
        content = command_file.read_text(encoding="utf-8")

        if command_file.suffix == ".toml":
            if tomllib is not None:
                data = tomllib.loads(content)
            else:
                data = {}
                desc_match = re.search(
                    r'^\s*description\s*=\s*"(?P<value>.*?)"\s*$', content, re.M
                )
                prompt_match = re.search(
                    r'^\s*prompt\s*=\s*"""\n(?P<value>.*?)\n"""\s*$',
                    content,
                    re.S | re.M,
                )
                if desc_match:
                    data["description"] = desc_match.group("value")
                if prompt_match:
                    data["prompt"] = prompt_match.group("value")
            frontmatter = {"description": data.get("description", "")}
            body = data.get("prompt", "").strip()
            return frontmatter, body, command_file.stem

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                if not isinstance(frontmatter, dict):
                    frontmatter = {}
                body = parts[2].strip()
            else:
                console.print(
                    f"[yellow]警告：{command_file.name} 的 frontmatter 不完整（缺少结束 ---），将按纯文本处理[/yellow]"
                )
                frontmatter = {}
                body = content
        else:
            frontmatter = {}
            body = content

        return frontmatter, body, command_file.stem

    if not templates_dir.exists() or not _supported_command_files(templates_dir):
        pkg = sys.modules.get("specify_cli")
        cli_file = getattr(pkg, "__file__", __file__) if pkg else __file__
        script_dir = Path(cli_file).parent.parent.parent
        fallback_dir = script_dir / "templates" / "commands"
        if fallback_dir.exists() and _supported_command_files(fallback_dir):
            templates_dir = fallback_dir

    if not templates_dir.exists() or not _supported_command_files(templates_dir):
        if tracker:
            tracker.error("ai-skills", "未找到命令模板")
        else:
            console.print("[yellow]警告：未找到命令模板，跳过 skills 安装[/yellow]")
        return False

    command_files = _supported_command_files(templates_dir)
    if not command_files:
        if tracker:
            tracker.skip("ai-skills", "没有可用命令模板")
        else:
            console.print("[yellow]没有可安装的命令模板[/yellow]")
        return False

    skills_dir = _get_skills_dir(project_path, selected_ai)
    skills_dir.mkdir(parents=True, exist_ok=True)

    if tracker:
        tracker.start("ai-skills")

    installed_count = 0
    skipped_count = 0
    for command_file in command_files:
        try:
            frontmatter, body, command_name = _parse_command_template(command_file)
            command_name = _normalize_speckit_name(command_name)
            skill_name = f"speckit-{command_name}"

            skill_dir = skills_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            original_desc = frontmatter.get("description", "")
            enhanced_desc = SKILL_DESCRIPTIONS.get(
                command_name, original_desc or f"Spec Kit 工作流命令：{command_name}"
            )

            source_name = command_file.name
            if source_name.endswith(".md") or source_name.endswith(".toml"):
                suffix = command_file.suffix
                stem = _normalize_speckit_name(command_file.stem)
                source_name = f"{stem}{suffix}"

            frontmatter_data = {
                "name": skill_name,
                "description": enhanced_desc,
                "compatibility": "Requires spec-kit project structure with .specify/ directory",
                "metadata": {
                    "author": "github-spec-kit",
                    "source": f"templates/commands/{source_name}",
                },
            }
            frontmatter_text = yaml.safe_dump(frontmatter_data, sort_keys=False).strip()
            skill_content = (
                f"---\n"
                f"{frontmatter_text}\n"
                f"---\n\n"
                f"# Speckit {command_name.title()} Skill\n\n"
                f"{body}\n"
            )

            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skipped_count += 1
                continue
            skill_file.write_text(skill_content, encoding="utf-8")
            installed_count += 1

        except Exception as e:
            console.print(
                f"[yellow]警告：安装 skill {command_file.stem} 失败：{e}[/yellow]"
            )
            continue

    if tracker:
        if installed_count > 0 and skipped_count > 0:
            tracker.complete(
                "ai-skills",
                f"{installed_count} new + {skipped_count} existing skills in {skills_dir.relative_to(project_path)}",
            )
        elif installed_count > 0:
            tracker.complete(
                "ai-skills",
                f"{installed_count} skills → {skills_dir.relative_to(project_path)}",
            )
        elif skipped_count > 0:
            tracker.complete("ai-skills", f"{skipped_count} skills already present")
        else:
            tracker.error("ai-skills", "未安装任何 skills")
    else:
        if installed_count > 0:
            console.print(
                f"[green]✓[/green] 已安装 {installed_count} 个 agent skills 到 {skills_dir.relative_to(project_path)}/"
            )
        elif skipped_count > 0:
            console.print(
                f"[green]✓[/green] {skills_dir.relative_to(project_path)}/ 中已有 {skipped_count} 个 agent skills"
            )
        else:
            console.print("[yellow]未安装任何 skills[/yellow]")

    return installed_count > 0 or skipped_count > 0


def _print_json_error(msg: str):
    sys.stdout.write(json.dumps({"status": "error", "message": msg}) + "\n")


def _validate_init_args(
    project_name: Optional[str],
    ai_assistant: Optional[str],
    ai_commands_dir: Optional[str],
    here: bool,
    ai_skills: bool,
    json_output: bool,
) -> Tuple[Optional[str], Optional[str], bool]:
    """Validate arguments for the init command and return resolved (project_name, ai_assistant, here)."""
    if ai_assistant and ai_assistant.startswith("--"):
        console.print(f"[red]Error:[/red] Invalid value for --ai: '{ai_assistant}'")
        console.print("[yellow]提示：[/yellow] 你可能忘了给 --ai 提供取值。")
        console.print("[yellow]示例：[/yellow] specify-zh init --ai claude --here")
        console.print(
            f"[yellow]可用 agents：[/yellow] {', '.join(AGENT_CONFIG.keys())}"
        )
        if json_output:
            _print_json_error(f"Invalid value for --ai: '{ai_assistant}'")
        raise typer.Exit(1)

    if ai_commands_dir and ai_commands_dir.startswith("--"):
        console.print(
            f"[red]Error:[/red] Invalid value for --ai-commands-dir: '{ai_commands_dir}'"
        )
        console.print(
            "[yellow]提示：[/yellow] 你可能忘了给 --ai-commands-dir 提供取值。"
        )
        console.print(
            "[yellow]示例：[/yellow] specify-zh init --ai generic --ai-commands-dir .myagent/commands/"
        )
        raise typer.Exit(1)

    if ai_assistant:
        ai_assistant = AI_ASSISTANT_ALIASES.get(ai_assistant, ai_assistant)

    if project_name == ".":
        here = True
        project_name = None

    if here and project_name:
        console.print("[red]错误：[/red] 不能同时指定项目名和 --here")
        if json_output:
            _print_json_error("不能同时指定项目名和 --here")
        raise typer.Exit(1)

    if not here and not project_name:
        if sys.stdin.isatty() and not json_output:
            project_name = typer.prompt(
                "请输入新项目目录名称（或输入 '.' 在当前目录初始化）"
            )
            if project_name == ".":
                here = True
                project_name = None
        else:
            console.print(
                "[red]错误：[/red] 必须提供项目名，或使用 '.' 表示当前目录，或使用 --here"
            )
            if json_output:
                _print_json_error("必须提供项目名")
            raise typer.Exit(1)

    if ai_skills and not ai_assistant:
        console.print("[red]错误：[/red] --ai-skills 必须搭配 --ai 使用")
        console.print(
            "[yellow]Usage:[/yellow] specify-zh init <project> --ai <agent> --ai-skills"
        )
        raise typer.Exit(1)

    return project_name, ai_assistant, here


__all__ = [
    "BUNDLED_CORE_DIR",
    "BUNDLED_DOCS_DIR",
    "BUNDLED_TEMPLATES_DIR",
    "CONVENTIONS_DIRNAME",
    "_build_template_tree_from_source",
    "_bundled_asset_root_from_package",
    "_copy_tree_into_project",
    "_get_command_templates_dir",
    "_get_conventions_registry_path",
    "_parse_markdown_command_template",
    "_print_json_error",
    "_render_agent_command",
    "_repo_root_from_source",
    "_validate_init_args",
    "bootstrap_template_from_fallback_source",
    "download_and_extract_template",
    "download_template_from_github",
    "ensure_coding_conventions_from_docs",
    "ensure_codex_prompts_from_templates",
    "ensure_constitution_from_template",
    "ensure_executable_scripts",
    "install_ai_skills",
]
