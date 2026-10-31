if ((Get-FileHash -LiteralPath 'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/skin_light_contract.py' -Algorithm SHA256).Hash.ToLower() -ne '8a6415dc18f8a95222b598720ca362145268e1759e8b9537026912df9266fa96') { throw 'Immutable helper hash changed: skin_light_contract.py' }
if ((Get-FileHash -LiteralPath 'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-correction-v20/candidate-orbital-v21/main/exact-recipe.py' -Algorithm SHA256).Hash.ToLower() -ne '33239f453adbcf45a04ccb6d792a6ea0135e55f8e39f025a1d12d167e9c9dff4') { throw 'Immutable helper hash changed: legacy_snapshot_apply_interp.py' }
# Run in PowerShell; requires existing immutable producer/canonical helper paths recorded in delivery-manifest.json.
$blender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
$recipe = 'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/finish-4/replay'
$source = 'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend'
$dest = 'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/replay-new'
& $blender --background --python "$recipe/01_shape.py" -- --source $source --output-dir "$dest/shape"
& $blender --background --python "$recipe/02_paint.py" -- --source "$dest/shape/Mia_FaceShape_v22.blend" --plate 'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/paint-source/source-v2-not-model-render.png' --output-dir "$dest/paint"
& $blender --background --python "$recipe/03_eye.py" -- --source "$dest/paint/Mia_FaceFinish_v22.blend" --output-dir "$dest/eye"
& $blender --background --python "$recipe/04_surface.py" -- --source "$dest/eye/Mia_FaceFinish_v22.blend" --plate 'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/paint-source/source-v3-not-model-render.png' --output-dir "$dest/surface"
