[CmdletBinding()]
param(
    [switch]$SkipAssetBuild,
    [switch]$Wait
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = $PSScriptRoot
$dotnetExecutable = Join-Path $repositoryRoot '.dotnet\dotnet.exe'
$solution = Join-Path $repositoryRoot 'Bolttagu.slnx'
$appProject = Join-Path $repositoryRoot 'src\Bolttagu.App\Bolttagu.App.csproj'
$appExecutable = Join-Path $repositoryRoot 'src\Bolttagu.App\bin\Debug\net10.0-windows\Bolttagu.exe'

$runningProcess = Get-Process -Name Bolttagu -ErrorAction SilentlyContinue |
    Where-Object {
        try { $_.Path -eq $appExecutable }
        catch { $false }
    } |
    Select-Object -First 1

if ($null -ne $runningProcess) {
    Write-Host "Bolttagu is already running (PID $($runningProcess.Id)). Exit it from the tray before rebuilding."
    exit 0
}

if (-not (Test-Path -LiteralPath $dotnetExecutable)) {
    Write-Host 'Installing the repository-local .NET SDK...'
    & (Join-Path $repositoryRoot 'scripts\bootstrap.ps1')
}

if (-not (Test-Path -LiteralPath $dotnetExecutable)) {
    throw "The repository-local SDK was not found at '$dotnetExecutable'. Run scripts/bootstrap.ps1 and try again."
}

try {
    & $dotnetExecutable restore $solution
    if ($LASTEXITCODE -ne 0) { throw "Restore failed with exit code $LASTEXITCODE." }

    if (-not $SkipAssetBuild) {
        & $dotnetExecutable run --project (Join-Path $repositoryRoot 'tools\Bolttagu.AssetBuild') -- all
        if ($LASTEXITCODE -ne 0) { throw "Asset build failed with exit code $LASTEXITCODE." }
    }

    & $dotnetExecutable build $appProject --configuration Debug --no-restore
    if ($LASTEXITCODE -ne 0) { throw "Debug build failed with exit code $LASTEXITCODE." }

    if (-not (Test-Path -LiteralPath $appExecutable)) {
        throw "Build completed but '$appExecutable' was not created."
    }

    $process = Start-Process -FilePath $appExecutable -WorkingDirectory $repositoryRoot -PassThru -Wait:$Wait
    Write-Host "Bolttagu started (PID $($process.Id)). Use the tray icon or right-click menu to exit."
}
catch {
    Write-Error "Bolttagu could not start: $($_.Exception.Message)"
    exit 1
}
