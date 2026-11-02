"""C changes only breast primitive to one convex affine ellipsoid per side."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;B=P.parent/'B';sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
p=json.loads((B/'parameters.json').read_text(encoding='utf-8'));s=p['source_consumed_before_geometry'];assert len(s['section_support_bands'])==4
assert sha(p['sources']['v06_path'])==p['sources']['v06_sha256'] and sha(p['sources']['low_path'])==p['sources']['low_sha256']
p['version']='design-sculpt07-C';p['parent_failed_B_parameters_sha256']=sha(B/'parameters.json');p['hypothesis']='BREAST ONLY: convex affine ellipsoid with buried posterior closure. B thorax/shoulders/arms/anterior/posterior roots/context/cameras unchanged. No station-exact forcing or independent CY/RY interpolation.'
p['breast']=dict(center_x=p['breast']['center_x'],center_y=-.030,center_z=1.266,radii=[.077,.125,.080],yz_shear=.25,posterior_cap_y=.012,interbreast_blend=.003,thorax_blend=.016,
 manual_justification='One convex triaxial ellipsoid sheared Y by0.25*(Z−centerZ). Center is behind thorax skin. Vertical extent1.186..1.346m straddles observed v06 stations1.220..1.309. Nominal front at center−155mm; shear shifts actual front maximum slightly lower. Width and F2 support are weak source priors to be measured, not exact fitted cloth or fixed inferred tangent targets. Parameters are a bounded anatomical hypothesis; actual residuals retained.')
p['B_preserved_components']={k:sha(B/'parameters.json') for k in ['thorax','shoulder','upper_arm','anterior_fan','posterior_wall','trapezius','pose','mesher','context_mask_B']}
(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8');print('SCULPT07_C_CONVEX_BREAST_PARAMETERS_FROZEN',flush=True)
