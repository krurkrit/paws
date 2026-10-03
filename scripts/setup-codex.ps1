param([switch]$WithTemplate)

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$template = Join-Path $project 'bench/fixtures/full-stack-fastapi-template'

foreach ($command in @('python', 'codex')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $command"
    }
}

if ($WithTemplate) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Required command not found: git' }
    if (-not (Test-Path -LiteralPath $template)) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $template) | Out-Null
        & git clone 'https://github.com/tiangolo/full-stack-fastapi-template.git' $template
        if ($LASTEXITCODE -ne 0) { throw 'Template clone failed' }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $template '.git'))) {
        throw "Existing template directory is not a Git checkout: $template"
    }
    & git -C $template checkout --detach 'cd83fc1'
    if ($LASTEXITCODE -ne 0) { throw 'Template checkout failed' }
    $revision = (& git -C $template rev-parse HEAD).Trim()
    if (-not $revision.StartsWith('cd83fc1')) { throw "Unexpected template revision: $revision" }
}

& python (Join-Path $project 'bench/runners/codex.py') --selftest
if ($LASTEXITCODE -ne 0) { throw 'Benchmark selftest failed' }
Write-Host 'Setup complete. Run .\run-codex.ps1 for a small comparison.'
