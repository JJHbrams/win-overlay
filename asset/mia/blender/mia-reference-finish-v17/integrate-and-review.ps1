param(
  [Parameter(Mandatory=$true)][string]$HairNative,
  [Parameter(Mandatory=$true)][string]$HairSha256,
  [string]$RunName = ''
)
$ErrorActionPreference = 'Stop'
$MiaRepo = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$MiaBlender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$MiaRunRoot = $PSScriptRoot
if ($RunName) {
  if ($RunName -notmatch '^[a-z0-9-]+$') { throw 'RunName must be a simple folder label' }
  $MiaRunRoot = Join-Path $PSScriptRoot $RunName
  if (Test-Path -LiteralPath $MiaRunRoot) { throw 'Run folder already exists' }
  New-Item -ItemType Directory -Path $MiaRunRoot | Out-Null
}
$MiaGeometry = Join-Path $MiaRunRoot 'geometry-integrated'
$MiaPaint = Join-Path $MiaRunRoot 'final'
$MiaReview = Join-Path $MiaRunRoot 'fresh-review'
if ((Get-FileHash -LiteralPath $HairNative -Algorithm SHA256).Hash -ne $HairSha256) { throw 'Hair source changed before integration' }
foreach ($MiaTarget in @($MiaGeometry, $MiaPaint, $MiaReview)) {
  if (Test-Path -LiteralPath $MiaTarget) { throw "Refusing to overwrite existing integration: $MiaTarget" }
}
& $MiaBlender --background --python-exit-code 1 --python (Join-Path $MiaRepo 'tools/mia/blender/refine_mia_face_surface_v17b.py') -- --source $HairNative --output-dir $MiaGeometry --resolution 1000 --quick *> (Join-Path $MiaRunRoot 'integration-geometry.log')
if ($LASTEXITCODE -ne 0) { throw 'Face geometry replay failed; inspect integration-geometry.log' }
& $MiaBlender --background --python-exit-code 1 --python (Join-Path $MiaRepo 'tools/mia/blender/project_mia_face_paint_v17.py') -- --source (Join-Path $MiaGeometry 'Mia_FaceSurface_v17b.blend') --output-dir $MiaPaint --plate (Join-Path $PSScriptRoot 'front-paint-source-v2-not-model-render.png') --resolution 1000 *> (Join-Path $MiaRunRoot 'integration-paint.log')
if ($LASTEXITCODE -ne 0) { throw 'UV paint replay failed; inspect integration-paint.log' }
$MiaCombinedNative = Join-Path $MiaPaint 'Mia_HeadHair_v17.blend'
Copy-Item -LiteralPath (Join-Path $MiaPaint 'Mia_FacePainted_v17.blend') -Destination $MiaCombinedNative
& $MiaBlender --background --python-exit-code 1 --python (Join-Path $PSScriptRoot 'review_saved_reference_v17.py') -- --source $MiaCombinedNative --output-dir $MiaReview --hair-collection MIA_V17_PIXAL_HAIR *> (Join-Path $MiaRunRoot 'fresh-review.log')
if ($LASTEXITCODE -ne 0) { throw 'Fresh saved-native review failed; inspect fresh-review.log' }
if ((Get-FileHash -LiteralPath $HairNative -Algorithm SHA256).Hash -ne $HairSha256) { throw 'Hair source changed during integration' }
Get-FileHash -LiteralPath $MiaCombinedNative -Algorithm SHA256 | Select-Object Path, Hash | ConvertTo-Json
