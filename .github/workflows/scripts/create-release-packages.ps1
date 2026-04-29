param(
    [string]$OutputDir = "",
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $RootDir "dist\release-packages"
}
if ([string]::IsNullOrWhiteSpace($Version)) {
    $pyproject = Get-Content (Join-Path $RootDir "pyproject.toml") -Raw
    if ($pyproject -match '^version = "([^"]+)"') {
        $Version = $matches[1]
    } else {
        $Version = "0.0.0"
    }
}

$AllAgents = @(
    'agy','amp','auggie','bob','claude','codebuddy','codex','copilot','cursor-agent','gemini',
    'generic','kiro-cli','kilocode','opencode','qodercli','qwen','roo','shai','tabnine','vibe','windsurf'
)
$AllScripts = @('sh', 'ps')

function Get-AgentCommandDir([string]$Agent) {
    switch ($Agent) {
        'copilot' { return '.github/agents' }
        'codex' { return '.codex/prompts' }
        'windsurf' { return '.windsurf/workflows' }
        'kilocode' { return '.kilocode/workflows' }
        'agy' { return '.agent/workflows' }
        'kiro-cli' { return '.kiro/prompts' }
        'opencode' { return '.opencode/command' }
        'shai' { return '.shai/commands' }
        'tabnine' { return '.tabnine/agent/commands' }
        default { return ".$Agent/commands" }
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

foreach ($Agent in $AllAgents) {
    foreach ($ScriptKind in $AllScripts) {
        $StageDir = Join-Path $OutputDir "spec-kit-template-$Agent-$ScriptKind-$Version"
        $PackageDir = Join-Path $StageDir ".specify"
        if (Test-Path $StageDir) {
            Remove-Item $StageDir -Recurse -Force
        }

        New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "templates") | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "scripts\bash") | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "scripts\powershell") | Out-Null

        Copy-Item (Join-Path $RootDir "templates\*") (Join-Path $PackageDir "templates") -Recurse -Force
        Copy-Item (Join-Path $RootDir "scripts\bash\*") (Join-Path $PackageDir "scripts\bash") -Recurse -Force
        Copy-Item (Join-Path $RootDir "scripts\powershell\*") (Join-Path $PackageDir "scripts\powershell") -Recurse -Force

        $TargetDir = Join-Path $StageDir (Get-AgentCommandDir $Agent)
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

        if ($Agent -eq 'tabnine') {
            @"
prompt = "See .specify/templates/commands/plan.md"
args = "{{args}}"
"@ | Set-Content (Join-Path $TargetDir "speckit-plan.toml") -Encoding utf8
        } else {
            Copy-Item (Join-Path $RootDir "templates\commands\plan.md") (Join-Path $TargetDir "speckit-plan.md") -Force
        }

        $ZipPath = Join-Path $OutputDir "spec-kit-template-$Agent-$ScriptKind-$Version.zip"
        if (Test-Path $ZipPath) {
            Remove-Item $ZipPath -Force
        }
        Compress-Archive -Path $StageDir -DestinationPath $ZipPath -Force
        Remove-Item $StageDir -Recurse -Force
    }
}
