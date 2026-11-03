"""Finite/manifold/connected and actual mesh-section/source support audit."""
from pathlib import Path
import json,hashlib,math,sys
import numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import field
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((P/'parameters.json').read_text());data=np.load(P/'sculpt07-E.npz');v=data['world'].astype(float);tri=data['triangles'];parts=v[tri]
edges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1);uniq,counts=np.unique(edges,axis=0,return_counts=True)
parent=np.arange(len(v));rank=np.zeros(len(v),np.uint8)
def root(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i
for a,b in uniq:
    a=root(a);b=root(b)
    if a!=b:
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
labels=np.array([root(i) for i in range(len(v))]);component_sizes=np.unique(labels,return_counts=True)[1]
normal=np.cross(parts[:,1]-parts[:,0],parts[:,2]-parts[:,0]);area=np.linalg.norm(normal,axis=1)*.5
def section(z):
    delta=parts[:,:,2]-z;active=parts[(delta.min(1)<=0)&(delta.max(1)>=0)];pts=[]
    for a,b in [(0,1),(1,2),(2,0)]:
        left=active[:,a];right=active[:,b];ok=(left[:,2]-z)*(right[:,2]-z)<0
        aa=left[ok];bb=right[ok];pts.append(aa+(bb-aa)*((z-aa[:,2])/(bb[:,2]-aa[:,2]))[:,None])
    return np.concatenate(pts)
rows=[];yaw=math.radians(p['source_consumed_before_geometry']['cameras']['F2']['yaw_degrees']);direction=np.array([-math.cos(yaw),-math.sin(yaw)])
f,reg=field.make(p)
sections={}
for b in p['source_consumed_before_geometry']['section_support_bands']:
    pts=section(b['world_z']);pts=pts[(abs(pts[:,0])<.18)&(pts[:,1]<-.05)];assert len(pts)
    support=(pts[:,:2]-[0,-.018])@direction;k=int(np.argmax(support));actual=float(support[k]);expected=b['oblique_support_m'];unc=b['oblique_support_uncertainty_m']
    # Retain the broad ROI result above, including any arm/fan contamination.
    # Separately declare a breast-support region by nearest positive primitive.
    values={key:field.evaluate(expr,pts) for key,expr in reg.items()};breast=values['breast_pair'];other=np.minimum.reduce([a for key,a in values.items() if key!='breast_pair']);semantic=pts[breast<=other+.002]
    semsupport=(semantic[:,:2]-[0,-.018])@direction;kk=int(np.argmax(semsupport));semactual=float(semsupport[kk])
    rows.append(dict(z=b['world_z'],source_v06_y=b['v06_source_y'],source_E2_y=b['source_E2_y'],source_F2_y=b['source_F2_y'],actual_F2_support_m=actual,source_F2_support_m=expected,support_residual_mm=(actual-expected)*1000,support_uncertainty_mm=unc*1000,within_support_band=abs(actual-expected)<=unc,actual_support_maximizer=pts[k].tolist(),actual_front_x_interval_m=[float(pts[:,0].min()),float(pts[:,0].max())],observed_E2_width_m=b['source_front_width_m'],front_width_residual_mm=(float(np.ptp(pts[:,0]))-b['source_front_width_m'])*1000,actual_front_profile_y_m=float(pts[:,1].min()),source_v06_front_profile_y_m=b['v06_front_profile_y'],profile_residual_mm=(float(pts[:,1].min())-b['v06_front_profile_y'])*1000,semantic_breast_support_m=semactual,semantic_breast_support_residual_mm=(semactual-expected)*1000,semantic_breast_support_maximizer=semantic[kk].tolist(),semantic_region_definition='Actual mesh intersection where breast_pair primitive field <= other positive primitive minimum +2mm; broad ROI retained separately, not silently replaced.',semantic_breast_width_m=float(np.ptp(semantic[:,0]))))
    sections['z_'+str(round(b['world_z'],6))]=pts
# Anatomical air from placement, never subtraction. Cross-corridor probes are
# diagnostics rather than a claim that the entire axillary tunnel is approved.
air=np.array([[.151,0,1.28],[.157,0,1.26],[.165,0,1.24],[.170,0,1.22],[-.151,0,1.28],[-.157,0,1.26]])
airfield=field.evaluate(f,air)
signed=float(np.einsum('ij,ij->i',parts[:,0],np.cross(parts[:,1],parts[:,2])).sum()/6)
r=dict(parameters_sha256=sha(P/'parameters.json'),mesh_sha256=sha(P/'sculpt07-E.npz'),finite=bool(np.isfinite(v).all()),connected_components=len(component_sizes),component_vertex_counts=component_sizes.tolist(),boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),zero_area_triangles=int((area<1e-13).sum()),euler_characteristic=int(len(v)-len(uniq)+len(tri)),signed_volume_m3=signed,source_support_rows=rows,air_corridor_probes=[dict(point=q.tolist(),field_m=float(d),outside_positive_volume=bool(d>0)) for q,d in zip(air,airfield)],status='CPU construction evidence only. Actual4/source art review required; no anatomy PASS.',limits='Cup/band drawings are clothed envelope priors; global v06 height and E2/F2 support may disagree. No inferred 3D tangent point is audited as recovered anatomy. Mesh is a new design volume, private context seams UNVERIFIED.')
assert r['finite'] and r['connected_components']==1 and r['boundary_edges']==0 and r['nonmanifold_edges']==0 and r['zero_area_triangles']==0 and signed>0
np.savez_compressed(P/'actual-sections.npz',**sections)
(P/'cpu-audit.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print('SCULPT07_E_CPU_AUDIT',json.dumps(r),flush=True)
