[CmdletBinding()]
param(
    [switch]$SkipAssetBuild,
    [switch]$KeepExistingOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$dotnetExecutable = Join-Path $repositoryRoot '.dotnet\dotnet.exe'
$appProject = Join-Path $repositoryRoot 'src\Bolttagu.App\Bolttagu.App.csproj'
$publishRoot = Join-Path $repositoryRoot 'artifacts\publish\win-x64'
$expectedExecutable = Join-Path $publishRoot 'Bolttagu.exe'

if (-not (Test-Path -LiteralPath $dotnetExecutable)) {
    Write-Host 'Installing the repository-local .NET SDK...'
    & (Join-Path $PSScriptRoot 'bootstrap.ps1')
}

if (-not (Test-Path -LiteralPath $dotnetExecutable)) {
    throw "The repository-local SDK was not found at '$dotnetExecutable'."
}

try {
    & $dotnetExecutable restore $appProject --runtime win-x64
    if ($LASTEXITCODE -ne 0) { throw "Restore failed with exit code $LASTEXITCODE." }

    if (-not $SkipAssetBuild) {
        & $dotnetExecutable run --project (Join-Path $repositoryRoot 'tools\Bolttagu.AssetBuild') -- all
        if ($LASTEXITCODE -ne 0) { throw "Asset build failed with exit code $LASTEXITCODE." }
    }

    if ((Test-Path -LiteralPath $publishRoot) -and -not $KeepExistingOutput) {
        Remove-Item -LiteralPath $publishRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Path $publishRoot -Force | Out-Null
    & $dotnetExecutable publish $appProject `
        --configuration Release `
        --runtime win-x64 `
        --self-contained true `
        --no-restore `
        -p:PublishSingleFile=true `
        -p:IncludeNativeLibrariesForSelfExtract=true `
        -p:DebugType=None `
        -p:DebugSymbols=false `
        --output $publishRoot
    if ($LASTEXITCODE -ne 0) { throw "Publish failed with exit code $LASTEXITCODE." }

    if (-not (Test-Path -LiteralPath $expectedExecutable)) {
        throw "Publish completed but '$expectedExecutable' was not created."
    }

    $bytes = (Get-Item -LiteralPath $expectedExecutable).Length
    if ($bytes -le 0) { throw "Published executable '$expectedExecutable' is empty." }

    Write-Host "Published self-contained single-file executable: $expectedExecutable ($bytes bytes)"
}
catch {
    Write-Error "Bolttagu publish failed: $($_.Exception.Message)"
    exit 1
}
