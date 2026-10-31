param([switch]$Execute, [switch]$Resume)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\antio\.codex\worktrees\mia-body-head-v06\win-overlay'
$archive = 'C:\Users\antio\.codex\worktree-archives\mia-20261031-v20'
$sources = @(
    'C:\Users\antio\.codex\worktrees\mia-face-lookdev-v07\win-overlay',
    'C:\Users\antio\.codex\worktrees\mia-final-garments-v12\win-overlay',
    'C:\Users\antio\.codex\worktrees\mia-final-hair-v12\win-overlay',
    'C:\Users\antio\.codex\worktrees\mia-head-refine-v06\win-overlay',
    'C:\Users\antio\.codex\worktrees\mia-layered-workflow\win-overlay',
    'C:\Users\antio\Desktop\Workspace\projects\win-overlay-worktrees\mia-reference-face-art',
    'C:\Users\antio\Desktop\Workspace\projects\win-overlay-worktrees\mia-reference-hair-surface'
)
function Git-Read([string]$Directory, [string[]]$Arguments) {
    $result = & git -C $Directory @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $Arguments $result" }
    return ($result -join "`n")
}
function Tree-Manifest([string]$Directory) {
    $children = @(Get-ChildItem -LiteralPath $Directory -Force -Recurse)
    if (@($children | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
        throw "Reparse point in $Directory; automatic archive refused"
    }
    $files = @($children | Where-Object { -not $_.PSIsContainer } | Sort-Object FullName)
    $rows = foreach ($file in $files) {
        [pscustomobject]@{
            path = [IO.Path]::GetRelativePath($Directory, $file.FullName)
            bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    return @($rows)
}
function Save-Json($Data, [string]$Path) {
    $Data | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding utf8
}
$archive = [IO.Path]::GetFullPath($archive)
if (-not $archive.StartsWith('C:\Users\antio\.codex\worktree-archives\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive outside allowed root' }
$initialPrune = Git-Read $repo @('worktree','prune','--dry-run','--verbose','--expire','now')
if ($initialPrune.Trim() -and -not $Resume) { throw "Pre-existing stale worktree metadata; refuse broad prune: $initialPrune" }
$common = [IO.Path]::GetFullPath((Git-Read $repo @('rev-parse','--git-common-dir')))
$processes = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(blender|python|pythonw|node)\.exe$' })
if ($Resume) {
    $plan = @(Get-Content -LiteralPath (Join-Path $archive 'plan.json') -Raw | ConvertFrom-Json)
    if ($plan.Count -ne $sources.Count) { throw 'Unexpected resume plan' }
    foreach ($item in $plan) {
        if ($item.source -notin $sources -or -not ([IO.Path]::GetFullPath($item.destination)).StartsWith($archive + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe resume path' }
    }
} else {
$plan = foreach ($source in $sources) {
    $resolved = (Resolve-Path -LiteralPath $source).Path
    if ($resolved -ne [IO.Path]::GetFullPath($source)) { throw 'Unexpected resolved source' }
    if ($resolved -eq $repo -or $resolved -like '*mia-reference-recovery*') { throw 'Active root or current cwd prohibited' }
    $label = if ((Split-Path $source -Leaf) -eq 'win-overlay') { Split-Path (Split-Path $source -Parent) -Leaf } else { Split-Path $source -Leaf }
    $target = [IO.Path]::GetFullPath((Join-Path (Join-Path $archive $label) 'tree'))
    if (-not $target.StartsWith($archive + '\', [StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $target)) { throw 'Unsafe/existing archive target' }
    foreach ($proc in $processes) {
        if ($proc.CommandLine -and ($proc.CommandLine.Replace('/','\').IndexOf($source, [StringComparison]::OrdinalIgnoreCase) -ge 0)) { throw "Process $($proc.ProcessId) refers to source; retain $label" }
    }
    $gitPointer = Get-Content -LiteralPath (Join-Path $source '.git') -Raw
    if (-not $gitPointer.StartsWith('gitdir: ')) { throw 'Not a linked worktree pointer' }
    $admin = [IO.Path]::GetFullPath($gitPointer.Substring(8).Trim())
    if (-not $admin.StartsWith((Join-Path $common 'worktrees') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected Git metadata path' }
    [pscustomobject]@{
        label = $label; source = $source; destination = $target; git_admin = $admin
        git_admin_id = Split-Path $admin -Leaf
        branch = Git-Read $source @('symbolic-ref','--short','HEAD')
        head = Git-Read $source @('rev-parse','HEAD')
        status = Git-Read $source @('status','--porcelain=v1','--untracked-files=all','--ignored')
    }
}
}
if (-not $Execute) {
    $plan | Select-Object label, source, destination, branch, head | Format-Table -AutoSize
    Write-Output 'DRY RUN ONLY. All paths verified; no files moved.'
    exit 0
}
New-Item -ItemType Directory -Path $archive -Force | Out-Null
Save-Json $plan (Join-Path $archive 'plan.json')
$completed = if ($Resume) { @(Get-Content -LiteralPath (Join-Path $archive 'completed.json') -Raw | ConvertFrom-Json) } else { @() }
foreach ($item in $plan) {
    $container = Split-Path $item.destination -Parent
    if ($item.label -in $completed.label) {
        $original = @(Get-Content -LiteralPath (Join-Path $container 'files-before.json') -Raw | ConvertFrom-Json)
        if (@(Compare-Object $original @(Tree-Manifest $item.destination) -Property path,bytes,sha256).Count) { throw 'Resume archive mismatch' }
        continue
    }
    New-Item -ItemType Directory -Path $container -Force | Out-Null
    $before = @(Tree-Manifest $item.source)
    Save-Json $before (Join-Path $container 'files-before.json')
    if (-not (Test-Path -LiteralPath (Join-Path $container 'git-admin-snapshot'))) { Copy-Item -LiteralPath $item.git_admin -Destination (Join-Path $container 'git-admin-snapshot') -Recurse }
    # Both paths are absolute, allowlisted and on C:. Move preserves every untracked/ignored file.
    try { Move-Item -LiteralPath $item.source -Destination $item.destination } catch [System.IO.IOException] {
        if (Test-Path -LiteralPath $item.destination) { throw 'Partial move requires inspection; refusing to proceed' }
        if (@(Compare-Object $before @(Tree-Manifest $item.source) -Property path,bytes,sha256).Count) { throw 'Locked source changed during archive attempt' }
        Write-Output "RETAINED LOCKED SOURCE: $($item.label) (all original hashes verified)"
        continue
    }
    $after = @(Tree-Manifest $item.destination)
    $difference = @(Compare-Object $before $after -Property path,bytes,sha256)
    Save-Json $after (Join-Path $container 'files-after.json')
    if ($difference.Count) { throw "Archive mismatch for $($item.label); originals retained at destination, metadata not pruned" }
    $completed += [pscustomobject]@{label=$item.label; source=$item.source; destination=$item.destination; branch=$item.branch; head=$item.head; files=$before.Count; bytes=($before | Measure-Object bytes -Sum).Sum; hash_verified=$true}
    Save-Json $completed (Join-Path $archive 'completed.json')
    Write-Output "ARCHIVED VERIFIED: $($item.label) ($($before.Count) files)"
}
$dry = Git-Read $repo @('worktree','prune','--dry-run','--verbose','--expire','now')
$lines = @($dry -split "`n" | Where-Object { $_.Trim() })
$archivedPlan = @($plan | Where-Object { $_.label -in $completed.label })
if ($lines.Count -ne $completed.Count) { throw "Unexpected prune target count; no metadata changed: $dry" }
foreach ($line in $lines) {
    $matches = @($archivedPlan | Where-Object { $line -match ('worktrees[/\\]' + [regex]::Escape($_.git_admin_id) + ':') })
    if ($matches.Count -ne 1) { throw "Non-allowlisted prune target: $line" }
}
$prune = Git-Read $repo @('worktree','prune','--verbose','--expire','now')
foreach ($item in $archivedPlan) {
    if ((Git-Read $repo @('rev-parse', $item.branch)).Trim() -ne $item.head.Trim()) { throw 'Branch head changed' }
    # Archive is a file snapshot, not an active Git worktree. Keep the original pointer bytes.
    Move-Item -LiteralPath (Join-Path $item.destination '.git') -Destination (Join-Path $item.destination '.git.archived-pointer')
}
$retained = @($plan | Where-Object { $_.label -notin $completed.label } | Select-Object label,source,branch,head)
$final = [pscustomobject]@{archive=$archive; original_source_trees_preserved=$true; metadata_pruned=$true; git_pointer_renamed_to='.git.archived-pointer'; worktrees=$completed; retained_locked=$retained; worktree_list=(Git-Read $repo @('worktree','list','--porcelain')); prune_log=$prune}
Save-Json $final (Join-Path $archive 'result.json')
@'
# Mia inactive worktree archive

Every original file, including ignored Blender backups, is preserved in each `tree` directory. `files-before.json` and `files-after.json` record matching SHA-256/size/path inventories before the `.git` pointer was renamed to `.git.archived-pointer`.

These are inactive file snapshots, not current production or active Git worktrees. Branch heads remain in the main repository. `plan.json` records original paths; `git-admin-snapshot` preserves the previous linked-worktree metadata. To recover, create a new Git worktree for the recorded branch and reconcile the archived files; do not restore the stale `.git` pointer blindly. No source model was deleted and no dirty force removal was used.
'@ | Set-Content -LiteralPath (Join-Path $archive 'README.md') -Encoding utf8
Write-Output "COMPLETE: archived $($completed.Count) worktrees without data loss or forced removal. $archive"
