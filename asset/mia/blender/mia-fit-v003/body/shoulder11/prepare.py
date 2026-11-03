"""Freeze the single approved nested construction and computed sampling halo."""
from pathlib import Path
import copy,hashlib,json,math
import numpy as np
P=Path(__file__).resolve().parent;B=P.parent/'posterior-union09';T=P.parent/'shoulder10'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not (P/'parameters.json').exists() and not (P/'shoulder11.npz').exists(),'One construction only'
assert sha(B/'posterior09.npz')=='d5bf574ea958923fc70fe6ade4de7e0b64ec970c3cf15156be5f135af3c9cdd2'
p=json.loads((B/'parameters.json').read_text());old=copy.deepcopy(p['trapezius']);r=np.array(old['radii']);c=np.array(old['center']);th=math.radians(old['angle_y_degrees']);axis=np.array([math.sin(th),0.,math.cos(th)]);pole=c-r[2]*axis
p['trapezius']['center']=(pole+.8*(c-pole)).tolist();p['trapezius']['radii']=(.8*r).tolist()
extent=np.array(p['mesher']['bounds_max'])-p['mesher']['bounds_min'];res=np.ceil(extent/p['mesher']['voxel_m']).astype(int)+1;step=extent/(res-1);gate0=1.36+3*step[2]
p['shoulder11']=dict(scale=.8,old_trapezius=old,local_Z_world_axis_right=axis.tolist(),local_negative_Z_pole_right=pole.tolist(),gate_zero_z=gate0,gate_full_z=1.395,
    source='User-designated tied-hair visibility guide3cb29ca5; same frozen09 wholeheight registration.',
    formula='Ffinal=Fold+quinticSmooth01((Z-gatezero)/(gatefull-gatezero))*(Fhom-Fold)',
    mathematical_nesting='u=Aold(p-cold),a=1-s. fhom-fold=minr*(||u+a*ez||-||u||+a)>=0 byreverseTriangle. Fixed smoothminimum is monotone in each argument; nesting survives accumulation. 0<=gate<=1 givesFfinal>=Fold.',
    limits='Homothety reduces all3radii20%, notheightonly; field is approximate, not SDF. C2 field/gradients do not guarantee natural skin.')
write(P/'parameters.json',p)
v=np.load(B/'posterior09.npz')['world'];protected=v[v[:,2]<=1.36];maxcell=int(np.floor((protected[:,2]-p['mesher']['bounds_min'][2])/step[2]).max())
halo=dict(grid_resolution=res.tolist(),grid_step_m=step.tolist(),lower_protected_vertices=len(protected),highest_protected_Z=float(protected[:,2].max()),containing_cell_max_z=maxcell,
    first_bounding_plane=maxcell+1,conservative_last_preserved_sample_plane=maxcell+3,that_plane_world_z=float(p['mesher']['bounds_min'][2]+(maxcell+3)*step[2]),
    gate_zero_z=gate0,gate_full_z=1.395,gate_derivative_bound=1.875/(1.395-gate0),
    status='Conservative3sample-step collar from actual09 grid; undocumentedVDBstencil not assumed. Fresh actual protected physical triangles must pass or STOP; no postmesh coordinate mask.')
write(P/'mesher-halo.json',halo)
write(P/'parameter-proof.json',dict(baseline_parameters_sha256=sha(B/'parameters.json'),new_parameters_sha256=sha(P/'parameters.json'),
    primitive_changes=dict(before=old,after=p['trapezius']),all_other_baseline_keys_exact=all(json.loads((B/'parameters.json').read_text())[k]==p[k] for k in p if k not in ['trapezius','shoulder11']),
    posterior_join_blend=p['posterior_wall']['blend'],single_authorized_construction=True))
(P/'source-rails.json').write_bytes((T/'source-rails.json').read_bytes())
held=json.loads((B/'protected-input-hashes.json').read_text())
held.update({str(f):sha(f) for f in B.rglob('*') if f.is_file() and '__pycache__' not in f.parts})
for f in [T/'shoulder10.npz',T/'native/Mia_Shoulder10_STATIC_ShapeGuide.blend',*(T/'actual').glob('*')]:
    if f.is_file():held[str(f)]=sha(f)
write(P/'protected-input-hashes.json',held)
print('SHOULDER11_ONE_PARAMETERS_FROZEN',json.dumps(p['shoulder11']),flush=True)
