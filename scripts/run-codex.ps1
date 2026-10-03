param(
    [string]$Tasks = 'safe-path',
    [string]$Model = '',
    [ValidateRange(1, 100)][int]$Runs = 1,
    [ValidateRange(1, 32)][int]$Workers = 1,
    [string]$Arms = 'paws,caveman,ponytail'
)

$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$arguments = @((Join-Path $project 'bench/runners/codex.py'),
               '--task', $Tasks, '--arms', $Arms,
               '--runs', [string]$Runs, '--workers', [string]$Workers)
if ($Model) { $arguments += @('--model', $Model) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Codex benchmark failed; inspect results.json and _codex.stderr.txt' }
