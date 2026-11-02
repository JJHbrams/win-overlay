$ErrorActionPreference = 'Stop'
$phaseRoot = $PSScriptRoot
$bodyScope = [System.IO.Path]::GetFullPath('C:\Users\antio\.codex\worktrees\mia-v002-body\win-overlay\asset\mia\blender\mia-body-underwear-v002')
$bodyWorktree = 'C:\Users\antio\.codex\worktrees\mia-v002-body\win-overlay'
$receiptPath = Join-Path $phaseRoot 'storage\body-six-native-retirement.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Retirement already has a receipt; do not rerun blindly.' }
$manifest = Get-Content -LiteralPath (Join-Path $phaseRoot 'parts\body-G\native-retirement-allowlist.json') -Raw | ConvertFrom-Json
$fresh = Get-Content -LiteralPath (Join-Path $phaseRoot 'integrated\fresh-reopen-OP.json') -Raw | ConvertFrom-Json
if (-not $fresh.technical_preservation_pass -or $fresh.errors.Count -ne 0) { throw 'Current packed integration is not verified.' }
$protected = @(
    @{ path = $fresh.native; sha256 = $fresh.sha256 },
    @{ path = (Join-Path $bodyScope 'support-G\Mia_BodyUnderwear_v002_G.blend'); sha256 = 'e199c01b4c0a8fbc7942d5b667f8cdd0e1827d766d98cf28c99bd27ab12cf0da' },
    @{ path = (Join-Path $phaseRoot '..\mia-visible-art-v30\integrated\brows-C-outer-E\Mia_SourceLook_v31_Brows_Lashes.blend'); sha256 = '4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a' }
)
foreach ($item in $protected) {
    if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw 'Protected native changed.' }
}
$checked = @()
foreach ($item in $manifest.allowed_after_root_verification) {
    $absolute = (Resolve-Path -LiteralPath $item.path).ProviderPath
    if (-not $absolute.StartsWith($bodyScope + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw ('Outside owned body scope: ' + $absolute) }
    $file = Get-Item -LiteralPath $absolute
    if ($file.PSIsContainer -or $file.Length -ne $item.bytes) { throw 'Not the exact expected snapshot file.' }
    $digest = (Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($digest -ne $item.sha256) { throw 'Snapshot contains an unrecorded change.' }
    $relative = [System.IO.Path]::GetRelativePath($bodyWorktree, $absolute).Replace('\','/')
    $tracked = & git -C $bodyWorktree ls-files -- $relative
    if ($LASTEXITCODE -ne 0 -or $tracked) { throw ('Refuse tracked or unresolved file: ' + $relative) }
    $checked += @{ path = $absolute; bytes = $file.Length; sha256 = $digest }
}
if ($checked.Count -ne 6) { throw 'Unexpected retirement count.' }
$before = (Get-PSDrive C).Free
foreach ($item in $checked) {
    Remove-Item -LiteralPath $item.path -Force
    if (Test-Path -LiteralPath $item.path) { throw 'Single-file deletion did not complete.' }
}
foreach ($item in $protected) {
    if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw 'Protected native differs after retirement.' }
}
$result = @{
    user_authorization = 'Explicit intermediate artifact cleanup request; six superseded untracked B/C/D/F/F2 scenes retired only after current G packed integration/fresh data/source review.'
    deleted_files = $checked
    deleted_count = $checked.Count
    deleted_bytes = ($checked | Measure-Object -Property bytes -Sum).Sum
    c_free_before_bytes = $before
    c_free_after_bytes = (Get-PSDrive C).Free
    protected_current_natives = $protected
    original_art_small_deltas_maps_proof_and_git_history_unchanged = $true
    scope = 'Exact single-file LiteralPath operations; no wildcard or recursive deletion; no tracked file removal.'
    prior_cleanup_transition = 'Body D was protected as the then-current candidate during the earlier335-file cleanup. It is now superseded by verified G, not an original-art checkpoint.'
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output ('BODY_NATIVE_RETIREMENT_COMPLETE ' + $result.deleted_count + ' files / ' + $result.deleted_bytes + ' bytes')
