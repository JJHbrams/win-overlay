[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$sdkDirectory = Join-Path $repositoryRoot '.dotnet'
$dotnetExecutable = Join-Path $sdkDirectory 'dotnet.exe'

if (Test-Path -LiteralPath $dotnetExecutable) {
    Write-Host "Project SDK already exists: $dotnetExecutable"
    exit 0
}

$installer = Join-Path ([System.IO.Path]::GetTempPath()) 'dotnet-install-bolttagu.ps1'
Invoke-WebRequest -UseBasicParsing 'https://dot.net/v1/dotnet-install.ps1' -OutFile $installer
& powershell -NoProfile -ExecutionPolicy Bypass -File $installer `
    -Version '10.0.401' `
    -InstallDir $sdkDirectory `
    -NoPath

if (-not (Test-Path -LiteralPath $dotnetExecutable)) {
    throw "SDK install completed without creating $dotnetExecutable"
}

Write-Host "Installed project SDK: $dotnetExecutable"

