"""Explicit portable mouth copy and current five-component integration recipe."""
from pathlib import Path
import argparse, hashlib, json, shutil
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--mouth',required=True);ap.add_argument('--variant',default='C');ap.add_argument('--config',default='integration-recipe.json');a=ap.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=Path(a.mouth).resolve();target=P/'parts'/('mouth-'+a.variant)
files=['portable_mouth_delta.py','guard_helpers.py','payload/mouth-rig-'+a.variant+'.json','payload/mouth-rig-'+a.variant+'.npz','audit/input-guards.json']
rows=[]
for name in files:
    src=source/name;dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert sha(dst)==sha(src),'Do not replace a copied candidate'
    else:shutil.copyfile(src,dst)
    assert sha(src)==sha(dst);rows.append(dict(source=str(src),path=name,sha256=sha(dst),bytes=dst.stat().st_size))
(target/'portable-files.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
stages=[]
def stage(id,entry,function,owners,kwargs=None,path_kwargs=None):
    stages.append(dict(id=id,entry=entry,entry_sha256=sha(P/entry),function=function,
                       allowed_existing_owners=owners,kwargs=kwargs or {},path_kwargs=path_kwargs or []))
stage('mouth-'+a.variant,'parts/mouth-'+a.variant+'/portable_mouth_delta.py','apply_to_current_scene',['MIA_V27_Foundation_Face','MIA_V27_SharedHeadBody'],{'variant':a.variant})
stage('body-G','parts/body-G/replay_current_scene.py','apply',['MIA_V27_SharedHeadBody'])
hair=json.loads((P/'parts/hair-MN/bundle/manifest.json').read_text())
stage('hair-MN-bound','parts/hair-MN/apply_bundle_M.py','apply',[x['owner'] for x in hair['actors'] if x['existing']],{'folder':'parts/hair-MN/bundle','include_binding':True},['folder'])
stage('face-D2','parts/face-D2/portable_face_delta.py','apply_to_current_scene',['MIA_V27_SharedHeadBody','V28G_InnerLid_-1','V28G_InnerLid_1'])
stage('source-controls-gaze','expressions/expression_control_delta.py','apply_to_current_scene',['V28G_Iris_-1','V28G_Iris_1'])
cfg=dict(baseline='../mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend',
    baseline_sha256='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a',
    stages=stages,scope='Technical integration candidate. Optional hair binding requires actual pose review. No source ART or final animation approval.')
file=P/a.config;assert not file.exists(),'Use a new immutable recipe filename';file.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
print('PORTABLE_INTEGRATION_RECIPE_READY',file)
