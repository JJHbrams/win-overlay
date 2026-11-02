"""Copy explicit frozen small R3 deltas; no full-scene producer snapshots."""
from pathlib import Path
import hashlib,json,shutil
P=Path(__file__).resolve().parent
ROOT=Path('C:/Users/antio/.codex/worktrees')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
copies=[]
def copy_group(source,target,files):
    for name,expected in files.items():
        src=source/name;dst=P/'parts'/target/name
        actual=sha(src)
        if expected:assert actual==expected,(str(src),actual)
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():assert sha(dst)==actual,'Refuse to replace frozen input'
        else:shutil.copyfile(src,dst)
        copies.append(dict(source=str(src),path=str(dst.relative_to(P)),sha256=actual,bytes=dst.stat().st_size))
copy_group(ROOT/'mia-v002-face/win-overlay/asset/mia/blender/mia-expression-refine-v003','eye-A',{
    'portable_expression_refine.py':'434a8b3f2e9465e06cdc23a5758b6fbe60b7e17e82724fbe6a6e96ac570e411b',
    'payload/surprise-A.json':'7df2d49a59607d7a526b47a772d098ff436bc8239630700856467951d7237ab7',
    'payload/surprise-A.npz':'28800963d89635d5c5ba6588a3adb649151fc6a567df534ce57d9a90b9bd13f0',
    'HANDOFF.md':None,'handoff-manifest.json':None,'audit/CPU-guards-A.json':None,
    'review/A-quick10/paired/P12-source-baseline-A.png':None,
    'review/A-quick10/paired/P03-source-baseline-A.png':None,
    'review/A-quick10/paired/closure-wink-depth.png':None,
    'review/A-quick10/paired/actual-diagnostics.json':None})
copy_group(ROOT/'mia-v002-body/win-overlay/asset/mia/blender/mia-body-underwear-v002/brow-angry-R3','brow-support',{
    'replay_brow_support.py':'1882ec0698db383d1c06f9ca677eca6b921847eb96296cea2f76fbcb86f673bb',
    'brow-support-metadata.json':'c21ea7a06bb6ede3c688b45c31237cc8592ad8679ff063634aed913bc46b8173',
    'brow_support_guard.py':'35387b7b50745a7495861e79db2e9688d702edd48e2af1e99b63394d034d1266',
    'HANDOFF.md':None,'portable-support-manifest.json':None,'actual-image-comparison.json':None,
    'P05-source-before-after.png':None,'P15-source-before-after.png':None})
copy_group(ROOT/'mia-v002-hair/win-overlay/asset/mia/blender/mia-hair-refine-v002/surface-R','hair-surface-R',{
    'apply_surface_R.py':'f91a5b82712981254437548060f1660b72d72fb57e2997d245ab35c27b948ce1',
    'pigment-envelope.npz':'fe6de6e75f25d505b2c522ae27f762983e711224908d8116cda21c7fe9158ebf',
    'manifest.json':None,'HANDOFF.md':None,'fresh-guards.json':None,
    'profile-production-gray-board.png':None,'opposite018-production-gray-board.png':None,
    'pixel-difference-report.json':None,'rejected-first-compile.json':None})
stages=[]
def stage(id,entry,function,owners,kwargs=None,path_kwargs=None):
    stages.append(dict(id=id,entry=entry,entry_sha256=sha(P/entry),function=function,
        allowed_existing_owners=owners,kwargs=kwargs or {},path_kwargs=path_kwargs or []))
eye=['MIA_V27_SharedHeadBody','Mia_FacialControls_v002','MIA_v002_UpperDentalCrowns','MIA_v002_LowerDentalCrowns']
eye += [f'{name}_{side}' for name in ['V28G_InnerLid','V30_UpperLashes','V30_LowerLashes','V28G_Iris','V28G_Sclera'] for side in [-1,1]]
stage('eye-A-dental-display','parts/eye-A/portable_expression_refine.py','apply_to_current_scene',eye)
stage('brow-final-support','parts/brow-support/replay_brow_support.py','apply',['V31_SourceBrow_-1','V31_SourceBrow_1'])
stage('hair-surface-R','parts/hair-surface-R/apply_surface_R.py','apply',['MIA_V17_PIXAL_DetailedHair'],{'folder':'parts/hair-surface-R'},['folder'])
stage('smile-preset-calibration','expressions/apply_smile_preset_calibration.py','apply_to_current_scene',['MIA_V27_Foundation_Face','Mia_FacialControls_v002'])
stage('source-pose-calibration','expressions/apply_pose_calibration_r3.py','apply_to_current_scene',['MIA_V06_RIG','Mia_FacialControls_v002'])
recipe=P/'integration-recipe-R3-preflight.json'
assert not recipe.exists(),'Use a new immutable recipe'
recipe.write_text(json.dumps(dict(baseline='integrated/Mia_v0.0.2_Review_R2.blend',
    baseline_sha256='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82',stages=stages,
    scope='In-memory post-R2 bounded corrections. Crown-S UV/paint not yet integrated. Head rolls remain estimates pending actual16 review. No full ART/animation approval.'),indent=2)+'\n',encoding='utf-8')
(P/'parts/portable-copy-R3.json').write_text(json.dumps(dict(files=copies,copied_bytes=sum(r['bytes'] for r in copies),full_native_copies=0),indent=2)+'\n',encoding='utf-8')
print('R3_SMALL_INPUTS_READY',len(copies),sum(r['bytes'] for r in copies))
