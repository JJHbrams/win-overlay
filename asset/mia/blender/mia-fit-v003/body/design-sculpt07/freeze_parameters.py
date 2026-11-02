"""Consume observed source bands BEFORE creating a fresh design hypothesis."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;B=P.parent
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=json.loads((B/'source-binding/constraints.json').read_text());bands=s['section_support_bands'];fold=s['anterior_fold_bands']
assert len(bands)==4 and len(fold)==3
v06=CAN/'references/received/mia-body-v06-confirmed-20261102.png';low=Path(s['source'])
assert sha(v06)=='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1'
assert sha(low)==s['source_sha256']
half=max(r['source_front_width_m'] for r in bands)*.5
cx=half*.51;rx=half-cx+.004;cy=-.074;ry=.081
# Small explicit naked-form hypotheses relative to clothed v06 profiles.
# The lower support differs most between drawings; retain that residual.
front_offsets=[.008,.008,.007,.014]
radial=[(r['world_z'],((-r['v06_front_profile_y']+off+cy)/ry)**2) for r,off in zip(bands,front_offsets)]
radial=sorted([(1.174,0.),(1.190,.22)]+radial+[(1.337,.10),(1.351,0.)])
p=dict(version='design-sculpt07-A',status='NEW STATIC DESIGN HYPOTHESIS; UNSELECTED; NO UV/KEY/WEIGHT MIGRATION',
  sources=dict(v06_path=str(v06),v06_sha256=sha(v06),low_path=str(low),low_sha256=sha(low),constraints_sha256=sha(B/'source-binding/constraints.json')),
  source_consumed_before_geometry=dict(section_support_bands=bands,anterior_fold_bands=fold,display_metric=s['display_metric'],cameras=s['cameras'],
    excluded_as_hard_targets=['inferred_lateral_x','chosen_lateral_y','inferred_x','inferred_y'],
    interpretation='Observed support/pixel intervals and v06 Z/profile constrain envelope; naked root and posterior wall remain anatomical inference. Actual support maximizer may move.'),
  pose=dict(name='static low-A',upper_arm_outward_from_vertical_degrees=25.,note='One declared design pose. Original rig/head not edited; source skin axes are not internal bone axes.'),
  mesher=dict(voxel_m=.003,bounds_min=[-.335,-.205,1.025],bounds_max=[.335,.15,1.545],density_scale_m=.012,threshold=.5,background=0.,
    field='Approximate implicit radial/ellipsoid field, NOT an exact SDF. Density=max(0,0.5-field/0.012). Native VolumeCube / VolumeToMesh.'),
  thorax=dict(z_min=1.035,z_max=1.525,
    x_radius=[[1.035,.105],[1.12,.108],[1.18,.120],[1.25,.134],[1.32,.139],[1.365,.132],[1.40,.102],[1.435,.055],[1.47,.037],[1.525,.034]],
    y_radius=[[1.035,.065],[1.12,.070],[1.20,.076],[1.30,.078],[1.365,.073],[1.40,.061],[1.435,.045],[1.47,.036],[1.525,.033]],
    center_y=[[1.035,-.006],[1.20,-.010],[1.365,-.008],[1.435,-.006],[1.525,-.004]]),
  breast=dict(center_x=cx,center_y=cy,radius_x=rx,radius_y=ry,z_min=1.174,z_max=1.351,squared_radial_profile=radial,interbreast_blend=.003,thorax_blend=.016,
    manual_justification=dict(center_x='51% of measured E2 maximum halfwidth; broad bilateral roots, not recovered landmarks.',radius_x='Remaining measured E2 halfwidth + 4mm hidden-root allowance.',front_profile_offsets_m=front_offsets,limits='Offsets are inferred soft-tissue/cloth registration allowance, not recovered naked dimensions. Measure actual final projection.' )),
  shoulder=dict(center=[.158,-.004,1.362],radii=[.043,.051,.060],angle_y_degrees=-12.,blend=.014),
  upper_arm=dict(center=[.206,-.001,1.253],radii=[.035,.039,.139],angle_y_degrees=-25.,blend=.012),
  anterior_fan=dict(center=[.126,-.047,1.339],radii=[.060,.031,.050],angle_y_degrees=-24.,blend=.012),
  posterior_wall=dict(center=[.130,.037,1.321],radii=[.053,.030,.071],angle_y_degrees=-27.,blend=.010),
  trapezius=dict(center=[.082,.010,1.405],radii=[.078,.041,.037],angle_y_degrees=12.,blend=.016),
  construction_limits=['All components are buried positive volumes merged into one field; no drilled holes/collider subtraction/flat axillary membrane.',
    'Fresh continuous radial profiles are derived from observed priors, not compressed rows or coordinates from01/05/06.',
    'No nipple, garment, pigment, final sculpt detail, retopology, keys, weights or UV authored.',
    'Lower abdomen/neck/arm cut boundaries are private context seams, not watertight final body integration.'])
(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8')
print('SCULPT07_PARAMETERS_FROZEN source bands consumed',flush=True)
