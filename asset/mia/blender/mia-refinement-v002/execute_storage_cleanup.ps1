param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference = 'Stop'
$miaPlan = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
if ($miaPlan.status -ne 'PREPARED_NOT_EXECUTED') { throw 'Unexpected cleanup plan state' }
$miaResultPath = Join-Path (Split-Path -Parent $Manifest) 'cleanup-result.json'
if (Test-Path -LiteralPath $miaResultPath) { throw 'A cleanup result already exists; do not rerun blindly' }
# Validate every exact file before deleting anything. No wildcard or recursive delete.
foreach ($miaRow in $miaPlan.candidates) {
    $miaPath = [IO.Path]::GetFullPath($miaRow.path)
    $miaScope = [IO.Path]::GetFullPath((Join-Path $miaRow.repository 'asset/mia/blender')) + [IO.Path]::DirectorySeparatorChar
    if (-not $miaPath.StartsWith($miaScope,[StringComparison]::OrdinalIgnoreCase) -or -not $miaPath.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside intended C workspace scope' }
    if ($miaRow.tracked -ne $false) { throw 'Tracked file in cleanup plan' }
    if ([IO.Path]::GetExtension($miaPath) -notin @('.blend','.blend1','.blend@')) { throw 'Unexpected file type' }
    $miaFile = Get-Item -LiteralPath $miaPath
    if ($miaFile.PSIsContainer -or ($miaFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $miaFile.Length -ne $miaRow.bytes) { throw 'Candidate changed after inventory' }
    $miaAncestor = $miaFile.Directory
    while ($null -ne $miaAncestor -and $miaAncestor.FullName.Length -ge $miaScope.TrimEnd('\').Length) {
        if ($miaAncestor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Candidate passes through junction' }
        $miaAncestor = $miaAncestor.Parent
    }
}
foreach ($miaProtected in $miaPlan.protected) {
    if ((Get-FileHash -LiteralPath $miaProtected.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $miaProtected.sha256) { throw 'Protected checkpoint changed before cleanup' }
}
$miaFreeBefore = (Get-PSDrive -Name C).Free
$miaLedger = @()
try {
    foreach ($miaRow in $miaPlan.candidates) {
        Remove-Item -LiteralPath $miaRow.path -ErrorAction Stop
        $miaLedger += [pscustomobject]@{path=$miaRow.path;bytes=$miaRow.bytes;reason=$miaRow.reason;deleted=$true}
    }
}
finally {
    [pscustomobject]@{status='EXECUTION_LEDGER';manifest=$Manifest;planned_count=$miaPlan.count;deleted_count=$miaLedger.Count;deleted_bytes=($miaLedger | Measure-Object -Property bytes -Sum).Sum;c_free_before=$miaFreeBefore;c_free_after=(Get-PSDrive -Name C).Free;files=$miaLedger} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $miaResultPath -Encoding utf8
}
foreach ($miaProtected in $miaPlan.protected) {
    if ((Get-FileHash -LiteralPath $miaProtected.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $miaProtected.sha256) { throw 'Protected checkpoint changed during cleanup' }
}
$miaResult = Get-Content -LiteralPath $miaResultPath -Raw | ConvertFrom-Json
$miaResult.status = 'COMPLETE_PROTECTED_HASHES_UNCHANGED'
$miaResult | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $miaResultPath -Encoding utf8
[pscustomobject]@{deleted_files=$miaResult.deleted_count;deleted_bytes=$miaResult.deleted_bytes;c_free_before=$miaResult.c_free_before;c_free_after=$miaResult.c_free_after;protected_hashes_unchanged=$true} | ConvertTo-Json
