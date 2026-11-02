"""Preserve exact reattached art and its explicit new authority; not a model PASS."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image
P=Path(__file__).resolve().parent;M=P.parents[1];R=M/'references'
src=Path('C:/Users/antio/AppData/Local/Temp/codex-clipboard-9328aabc-959d-4864-ad92-bb3484143b5e.png');dest=R/'received/mia-body-v06-confirmed-20261102.png';old=R/'body-foundation/v06/mia-body-turnaround-v06.png'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if dest.exists():assert sha(dest)==sha(src)
else:shutil.copyfile(src,dest)
a,b=Image.open(dest).convert('RGBA'),Image.open(old).convert('RGBA');equal=a.size==b.size and a.tobytes()==b.tobytes()
provenance=dict(received='2026-11-02',source=str(src),path=dest.relative_to(R).as_posix(),sha256=sha(dest),size=list(a.size),pixel_sha256=hashlib.sha256(a.tobytes()).hexdigest(),canonical_v06=dict(path=old.relative_to(R).as_posix(),sha256=sha(old),pixel_equal=equal),authority='User explicitly reattached v06 and requires this whole-body target: larger/higher supported breasts, ribcage/shoulder/head-to-body proportion, then trapezius, underwearfit and neck/clavicle pigment. Design target approval is not model or exact orthographic-dimension approval.')
dest.with_suffix('.provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
f=R/'reference-catalog.json';d=json.loads(f.read_text(encoding='utf-8'))
identifier='MIA-BODY-V06-USER-CONFIRMED-20261102'
if not any(r['id']==identifier for r in d['assets']):d['assets'].append(dict(id=identifier,status='user_selected_body_design_target',role='whole_body_shape_underwear_neck_clavicle',path=dest.relative_to(R).as_posix(),sha256=sha(dest),size=list(a.size),mode=Image.open(dest).mode,provenance=dest.with_suffix('.provenance.json').relative_to(R).as_posix()))
for r in d['assets']:
 if r['id']=='MIA-BODY-V06':r['status']='pixel_equivalent_to_user_confirmed_target_20261102';r['confirmation']=identifier
d['reference_selection']['body_design_target']=identifier
d['reference_selection']['side_volume_revision']='Historic v04 not delivered; latest whole-body design target is user-confirmed v06. No model PASS implied.'
d['rules']=[('V06 was explicitly reattached and selected as the body design target on2026-11-02. Its illustrated views still have pose/projection uncertainty; this does not certify any model or exact dimensions.' if rule.startswith('V06 is an illustrated') else rule) for rule in d['rules']]
d['updated_date']='2026-11-02';f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sf=M/'CURRENT_STATE.json';s=json.loads(sf.read_text(encoding='utf-8'))
s['in_progress_v003']=dict(status='active',contract='blender/mia-fit-v003/PLAN.md',baseline_native=s['active_working_correction']['path'],baseline_sha256=s['active_working_correction']['sha256'],body_target=dest.relative_to(M).as_posix(),user_accepts_face_sculpt=True,eye_request='Small screen-right lower-lid curvature/height correction, not eyeball scaling; upper crease registration to real upper lid; source-supported brow visibility through bangs.',body_request='Wholeheight original-aspect v06 comparison FIRST. Larger/higher supported breasts and correctly sized/tapered thorax/shoulders/headratio; breast->trapezius->underwearUV->neck/clavicle pigment. Old fixedG3core constraint revoked.',hair_request='Rear locks/nape/tips and broken-color cause versus v29; braid source cleanup deferred until body/face fit, not removed. Partial source brow display requires isolated truebrow/crease/lash evidence.',new_full_native_saved=False,art_approved=False)
s['reference_roles']['body_target']=dest.relative_to(M).as_posix()
s['stage_status']['face_head_art']='User accepts current4dc1 facialsculpt; preserve contour/identity, only requested lower-right lid/crease/browvisibility. Earlier broad-face revision requests must not override this latest acceptance. Surface/fullMia approval separate.'
s['stage_status']['body_art']='User rejects current4dc1 wholebody: breasts too small/saggy, thorax too small/straight, shoulders narrow and headratio unlike user-confirmed v06. FixedG3core revoked; wholeheight corresponding views precede local edits.'
sf.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('BODY_TARGET_RECORDED',sha(dest),equal)
