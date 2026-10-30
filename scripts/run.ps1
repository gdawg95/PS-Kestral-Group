<#
PowerShell mirror of the Makefile, because the owner's laptop has no `make`
(DECISIONS.md D-013: the laptop is the reference environment for running the pipeline).
Usage:  .\scripts\run.ps1 all        .\scripts\run.ps1 ingest       .\scripts\run.ps1 test
        .\scripts\run.ps1 classify -Fresh
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('all', 'ingest', 'validate', 'classify', 'analyse', 'figures', 'export', 'test', 'lint', 'hooks', 'nlp-check')]
    [string]$Target,
    [switch]$Fresh
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

function Step($name, $cmd) {
    Write-Host ">>> $name" -ForegroundColor Cyan
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { throw "$name failed with exit code $LASTEXITCODE" }
}

$fresh = if ($Fresh) { ' --fresh' } else { '' }

switch ($Target) {
    'ingest'    { Step 'ingest'   'uv run python -m src.ingest' }
    'validate'  { Step 'validate' 'uv run python -m src.validate' }
    'classify'  { Step 'classify' "uv run python -m src.classify$fresh" }
    'analyse'   { Step 'analyse'  'uv run python -m src.analyse' }
    'figures'   { Step 'figures'  'uv run python -m src.figures' }
    'export'    { Step 'export'   'uv run python -m src.export' }
    'test'      { Step 'test'     'uv run pytest -q' }
    # Formatting is deliberately not gated - see the lint target in the Makefile.
    'lint'      { Step 'lint'     'uv run ruff check .' }
    'hooks'     { Step 'hooks'    'uv run pre-commit install' }
    'nlp-check' { Step 'nlp-check' 'uv run python scripts/check_nlp_env.py' }
    'all' {
        Step 'ingest'   'uv run python -m src.ingest'
        Step 'validate' 'uv run python -m src.validate'
        Step 'classify' "uv run python -m src.classify$fresh"
        Step 'analyse'  'uv run python -m src.analyse'
        Step 'figures'  'uv run python -m src.figures'
    }
}
Write-Host "done: $Target" -ForegroundColor Green
