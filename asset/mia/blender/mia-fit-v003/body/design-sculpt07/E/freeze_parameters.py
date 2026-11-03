"""One E support-state hypothesis, immutable D inputs, no native writes."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;D=P.parent/'D';CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
p=json.loads((D/'parameters.json').read_text(encoding='utf-8'));assert len(p['source_consumed_before_geometry']['section_support_bands'])==4
assert sha(p['sources']['v06_path'])==p['sources']['v06_sha256'] and sha(p['sources']['low_path'])==p['sources']['low_sha256']
p['version']='design-sculpt07-E';p['parent_D_parameters_sha256']=sha(D/'parameters.json');p['parent_D_mesh_sha256']=sha(D/'sculpt07-D.npz');p['contract_sha256']=sha(CAN/'blender/mia-fit-v003/UPPERBODY_SUPPORT_E_PLAN.md')
p['hypothesis']='One upper-inner support coordinate map per signed D breast plus later separately recorded bounded local posterior fair. Outer/inferior rails are actual-surface constraints, not primitive extrema. No whole thorax/head rewrite.'
p['breast']['support_map']=dict(medial_gather_m=.004,height_scale=1.09,z0=1.205,x_full=.090,x_zero=.125,y_full=-.030,y_zero=.005,z_full=1.240,weight='C2 quintic products; x even via abs with constant inner plateau, signed maps per breast avoid a sign(x) seam.',mapping='xprime=x+sign*.004*w;zprime=z−w*(z−1.205)*(1−1/1.09);evaluate signed D breast primitive at xprime,y,zprime including its original upper posterior warp. D world-Z union support and all11 nonbreast fields held.')
p['posterior_fair_status']='PENDING actual hit-seed/band data; no global smoothing or mass rewrite authorized.'
p['temporary_bra_diagnostic']='Source-derived fixed3Dcoverage attribute on private D/E surfaces, no UV/garment-force/production claim. Source necklines/band/straps remain distinct, hidden closure labelled/unpainted.'
(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
(P/'D-protected-hashes.json').write_text(json.dumps({str(f.relative_to(D)):sha(f) for f in sorted(D.rglob('*')) if f.is_file() and '__pycache__' not in f.parts},indent=2)+'\n',encoding='utf-8');print('E_SUPPORT_PARAMETERS_FROZEN')
