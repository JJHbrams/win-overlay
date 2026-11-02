"""One upper-root-only C2 warp, fixed C lower bowl/nonbreast components."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;C=P.parent/'C';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
p=json.loads((C/'parameters.json').read_text(encoding='utf-8'));assert len(p['source_consumed_before_geometry']['section_support_bands'])==4
assert sha(p['sources']['v06_path'])==p['sources']['v06_sha256'] and sha(p['sources']['low_path'])==p['sources']['low_sha256']
p['version']='design-sculpt07-D';p['parent_C_parameters_sha256']=sha(C/'parameters.json');p['hypothesis']='UPPER ROOT ONLY: posterior C2 breast-field warp abovecz and locally increased upper breast–thorax blend. C lower field, convex lower bowl, nonbreast11 fields, context, original head/keys held.'
p['breast']['upper_posterior_warp']=dict(k=.45,width_m=.009,formula='u=z-cz;v=clamp(u/w,0,1);H=w*(v^3−0.5v^4)+max(u−w,0); f=kH; evaluate C quadric at y−f. f=0 belowcz, f is C2, fsecond>=0.')
p['breast']['upper_thorax_blend']=dict(lower_m=.016,upper_m=.034,ramp_height_m=.040,ramp='C2 quintic10t^3−15t^4+6t^5, clamped overcz..cz+.040. Breast–thorax union only; other component blends fixed.')
p['breast']['manual_justification']+=' D adds at most a linear posterior upper shift after9mm C2 onset; explicit anatomical hypothesis to reduce excess upper profile and ball-like root, not source-station forcing. Lower bowl remains C.'
(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8');print('D_UPPER_ROOT_PARAMETERS_FROZEN')
