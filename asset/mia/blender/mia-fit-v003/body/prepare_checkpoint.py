"""Curate only scoped v003 checkpoint files; no git/native/GPU mutation."""
from pathlib import Path
import hashlib, json

P=Path(__file__).resolve().parent
old='C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/pose-space/mapping-frame1.npz'
for name in ['fit_posed_target_01.py','build_fullbody_scaffold.py','build_neck_supplement.py','verify_posed_target_01.py']:
    f=P/name
    text=f.read_text(encoding='utf-8')
    text=text.replace("Path('"+old+"')", "(Path(__file__).resolve().parent/'inputs/mapping-frame1.npz')")
    text=text.replace("np.load('"+old+"')", "np.load(P/'inputs/mapping-frame1.npz')")
    text=text.replace("str(P.parents[1]/'mia-body-underwear-v002/integration-guard-R3')", "str(P/'inputs')")
    f.write_text(text,encoding='utf-8',newline='\n')

sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
can=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
dependencies=[]
for role,path in [
    ('exact native',can/'blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'),
    ('user-confirmed original-aspect source',can/'references/received/mia-body-v06-confirmed-20261102.png'),
    ('source lighting fixture records',can/'blender/mia-refinement-v002/review/integrated-R3b/source/render-records.json'),
    ('existing hair ownership classifier',can/'blender/mia-visible-art-v30/component_ownership.py')]:
    dependencies.append(dict(role=role,path=str(path),sha256=sha(path)))
(P/'checkpoint-dependencies.json').write_text(json.dumps(dict(external_read_only=dependencies,local_frozen_mapping=dict(path='inputs/mapping-frame1.npz',sha256=sha(P/'inputs/mapping-frame1.npz')),local_verification_helper=dict(path='inputs/scene_fingerprint.py',sha256=sha(P/'inputs/scene_fingerprint.py')),historical='Old A/B/C/D/audit scripts are retained historical recipes; current target01 replay uses its NPZ, current native, local inputs, and recorded canonical fixture/ownership. No old G native or rest56 replay is required.'),indent=2)+'\n',encoding='utf-8')

# Keep current runtime and source constraints, actual essential images, and small
# historical failures. Exclude generated Python caches and redundant eval caches.
keep=[]
for f in P.rglob('*'):
    if not f.is_file() or '__pycache__' in f.parts:
        continue
    r=f.relative_to(P)
    if len(r.parts)==1:
        if f.suffix in ['.py','.md'] or f.name in ['.gitattributes','current-body-audit.json','current-body-limit.npz','current-body-weights.npz','current-rig-rest.json','protected-current-data.json','current-v06-boards.json','SOURCE_GATE_C.md','checkpoint-dependencies.json']:
            keep.append(f)
    elif r.parts[0] in ['inputs','current-source4','posed-target']:
        keep.append(f)
    elif r.parts[0]=='scaffold-fullbody':
        if 'unselected' in f.name:
            continue
        if r.parts[1] in ['actual-R4-oblique','actual-ghost-guides'] or len(r.parts)==2 and (f.suffix in ['.json','.md'] or f.name in ['actual3D-projected-on-source.png','neck-R4-projection.png']):
            keep.append(f)
    elif r.parts[0]=='scaffold-D':
        if len(r.parts)==2 and (f.suffix in ['.json','.md'] and 'unselected' not in f.name or f.name=='source-contours-overlay.png'):
            keep.append(f)
    elif r.parts[0] in ['renders-form-C-ablation','renders-form-D-gray','renders-form-D-ablation']:
        keep.append(f)

manifest=[dict(path=str(f.relative_to(P)).replace('\\','/'),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(set(keep))]
(P/'checkpoint-files.json').write_text(json.dumps(dict(status='COARSE TARGET01 REJECTED; no ART/rig/native promotion',files=manifest,total_bytes=sum(x['bytes'] for x in manifest),excluded='Redundant A/B/C/D evaluated caches, repeated boards, pycache, all old v002 ownership, and any full native.'),indent=2)+'\n',encoding='utf-8')
print('CHECKPOINT_CURATED',len(manifest),sum(x['bytes'] for x in manifest),flush=True)
