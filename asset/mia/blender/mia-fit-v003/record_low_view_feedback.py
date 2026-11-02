"""Preserve the reattached E2/F2 and its newly explicit upper-body role."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image

P=Path(__file__).resolve().parent;M=P.parents[1];R=M/'references'
source=Path('C:/Users/antio/AppData/Local/Temp/codex-clipboard-61c7b3a4-d339-492e-bdb8-8879c7ce5979.png')
dest=R/'received/mia-low-view-axilla-reaffirmed-20261103.png'
prior=R/'body-foundation/v06/supplements/low-pelvis-E2-F2-v01.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if dest.exists():assert sha(dest)==sha(source)
else:shutil.copyfile(source,dest)
a,b=Image.open(dest).convert('RGBA'),Image.open(prior).convert('RGBA')
assert a.size==b.size and a.tobytes()==b.tobytes()
identifier='MIA-LOW-AXILLA-USER-REAFFIRMED-20261103'
provenance=dict(received='2026-11-03',source=str(source),path=dest.relative_to(R).as_posix(),
    sha256=sha(dest),size=list(a.size),pixel_sha256=hashlib.sha256(a.tobytes()).hexdigest(),
    prior_generated_supplement=dict(path=prior.relative_to(R).as_posix(),sha256=sha(prior),pixel_equal=True),
    authority='User explicitly reattached E2/F2 as evidence for full rounded supported breast mass and breast-root/axilla/thorax overlap. This newly explicit upper-body comparison role supersedes a blanket auxiliary-only dismissal. Original v06 still anchors wholebody proportions; no model hip widening or exact inferred camera/anatomical dimensions follows.',
    production_feedback='Pointy breast from isolated fixed-pole constraints rejected. Guide presence without consuming source constraints is insufficient. Brow thickness and source-supported fringe gaps require actual geometry/source comparison; central rear hair needs real new filling mesh, not U removal alone.')
dest.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
file=R/'reference-catalog.json';d=json.loads(file.read_text(encoding='utf-8'))
row=dict(id=identifier,status='user_reaffirmed_upper_body_axilla_comparison',role='rounded_supported_mass_and_axillary_overlap',
    path=dest.relative_to(R).as_posix(),sha256=sha(dest),size=list(a.size),mode=Image.open(dest).mode,
    provenance=dest.with_suffix('.provenance.json').relative_to(R).as_posix())
d['assets']=[x for x in d['assets'] if x['id']!=identifier]+[row]
d['reference_selection']['low_view_upper_body_axilla']=identifier;d['updated_date']='2026-11-03'
file.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
file=R/'files.json';d=json.loads(file.read_text(encoding='utf-8'));row={k:row[k] for k in ['path','sha256','size','mode']}
d['images']=[x for x in d['images'] if x['path']!=row['path']]+[row]
file.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
file=M/'CURRENT_STATE.json';d=json.loads(file.read_text(encoding='utf-8'));state=d['in_progress_v003']
state['latest_low_view_body_reference']=dest.relative_to(M).as_posix()
state['latest_user_feedback']='2026-11-03: E2/F2 rounded full mass/axillary overlap must constrain actual surface. 01 shelf and02 hard-pole cone rejected;03 old-shape seed alone insufficient. Latest request authorizes source-matched brow thickness and fine fringe geometry/gaps, superseding blanket front-fringe freeze. Rear central gap requires actual new source-traced mesh; U deletion alone not completion.'
state['body_method']='Complete below-head guide exists, but actual surface source gate is open. Tensor resampling of connected rows is useful; final target must consume source-derived broad breast/root/axillary bands and explicit branch treatment. Do not restore old q0/q1 shape as source truth or accept rectangular-chart Jacobians for folded branch triangles. No new production body/native approved.'
file.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('LOW_VIEW_FEEDBACK_RECORDED',sha(dest),'pixels_match_prior',True)
