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
$sourceAtlas = Join-Path $repositoryRoot 'asset\bolttagu\build\atlas.png'
$publishedAssetRoot = Join-Path $publishRoot 'Assets\Bolttagu\build'
$publishedAtlas = Join-Path $publishedAssetRoot 'atlas.png'

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

    # The WPF single-file publish can bundle Content items instead of leaving them at
    # the path where RuntimeAnimationCatalog loads them. Keep the atlas beside the
    # already-published catalog so the packaged app does not silently use fallback art.
    if (-not (Test-Path -LiteralPath $sourceAtlas)) {
        throw "The built animation atlas was not found at '$sourceAtlas'."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $publishedAssetRoot 'catalog.json'))) {
        throw "The published animation catalog is missing from '$publishedAssetRoot'."
    }
    New-Item -ItemType Directory -Path $publishedAssetRoot -Force | Out-Null
    Copy-Item -LiteralPath $sourceAtlas -Destination $publishedAtlas -Force
    if ((Get-FileHash -LiteralPath $publishedAtlas -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $sourceAtlas -Algorithm SHA256).Hash) {
        throw 'The published animation atlas does not match the built atlas.'
    }

    $bytes = (Get-Item -LiteralPath $expectedExecutable).Length
    if ($bytes -le 0) { throw "Published executable '$expectedExecutable' is empty." }

    Write-Host "Published self-contained single-file executable: $expectedExecutable ($bytes bytes)"
}
catch {
    Write-Error "Bolttagu publish failed: $($_.Exception.Message)"
    exit 1
}
