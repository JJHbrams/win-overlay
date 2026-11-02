$ErrorActionPreference='Stop'
$phase=[IO.Path]::GetFullPath($PSScriptRoot)
$repo=[IO.Path]::GetFullPath((Join-Path $phase '../../../..'))
$allowed=[IO.Path]::GetFullPath((Join-Path $phase 'integrated'))
$checks=@(
    @{path=(Join-Path $allowed 'Mia_v0.0.2_Review_R3b.blend');sha='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'},
    @{path=(Join-Path $allowed 'Mia_v0.0.2_Review_R2.blend');sha='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82'},
    @{path=(Join-Path $phase '../mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend');sha='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a'}
)
foreach($row in $checks){if((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha){throw 'Protected native differs'}}
$proof=Get-Content -LiteralPath (Join-Path $phase 'review/integrated-R3b/verification-completion.json') -Raw | ConvertFrom-Json
if($proof.sha256 -ne $checks[0].sha -or $proof.actual_frames -ne 101){throw 'Current101-frame proof missing'}
$targets=@(
    @{name='Mia_v0.0.2_Review_OP.blend';sha='69bb589a707ba07be9fe23356550935557c835ce71e61564bccddbe442b95a7e'},
    @{name='Mia_v0.0.2_Review_R3.blend';sha='855d6b105df1afdef459df1cbd2847f84690c2daaf46854e2c5fa2d9c0ed8a5a'}
)
$deleted=@();$before=(Get-PSDrive -Name C).Free
foreach($row in $targets){
    $file=[IO.Path]::GetFullPath((Join-Path $allowed $row.name))
    if([IO.Path]::GetDirectoryName($file) -ne $allowed){throw 'Target escaped exact integrated directory'}
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha){throw 'Obsolete native differs'}
    $relative=[IO.Path]::GetRelativePath($repo,$file).Replace('\','/')
    $tracked=@(& git -C $repo ls-files -- $relative)
    if($LASTEXITCODE -ne 0 -or $tracked.Count -ne 0){throw 'Refuse tracked file or failed Git query'}
    $size=(Get-Item -LiteralPath $file).Length
    Remove-Item -LiteralPath $file
    if(Test-Path -LiteralPath $file){throw 'Deletion did not complete'}
    $deleted+=@{path=$file;sha256=$row.sha;bytes=$size;reason='Superseded untracked full scene; OP abandoned, R3 failed mixed-state normalization. Exact small replays/maps/actual images/logs retained; currentR3b and replay baseR2 protected.'}
}
foreach($row in $checks){if((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha){throw 'Protected native changed during retirement'}}
$report=@{deleted_files=$deleted;deleted_count=$deleted.Count;deleted_bytes=($deleted | Measure-Object bytes -Sum).Sum;protected_current_natives=$checks;c_free_before_bytes=$before;c_free_after_bytes=(Get-PSDrive -Name C).Free;scope='Two exact single-file LiteralPath deletes only; no recursive operation or Git history changes. Removed native references are historical, not available current files.'}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $phase 'storage/post-R3b-native-retirement.json') -Encoding utf8
Write-Output ('RETIRED_OBSOLETE_NATIVE_FILES '+$deleted.Count+' '+$report.deleted_bytes)
