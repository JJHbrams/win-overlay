"""Actual candidate scope/sections/intersections. CPU evidence, never ART PASS."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import json,hashlib
import numpy as np
from geometry import normals,volume,line_hits,roof,changed_intersections,triangle_intersects
P=Path(__file__).resolve().parent;meta=json.loads((P/'build-report.json').read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=np.load(meta['source_breast_step']['path']);new=np.load(P/'posterior08.npz');old=base['world'];v=new['world'];f=new['triangles'];delta=np.load(P/'delta.npz');active=delta['indices'];fixed=delta['fixed_indices']
assert sha(meta['source_breast_step']['path'])==meta['source_breast_step']['sha256']
assert sha(P/'posterior08.npz')==meta['candidate_sha256'] and np.array_equal(f,base['triangles'])
assert np.isfinite(v).all();mask=np.zeros(len(v),bool);mask[active]=True
assert np.array_equal(v[~mask],old[~mask]) and np.array_equal(v[fixed],old[fixed])
n0,vn0=normals(old.astype(float),f);n1,vn1=normals(v.astype(float),f)
dot=np.einsum('ij,ij->i',n0,n1);assert dot.min()>0
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1);assert area.min()>1e-12
edges,counts=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0,return_counts=True)
assert np.all(counts==2)
front=(vn0[:,1]<=0)|(old[:,1]<=.005)
assert np.array_equal(v[front],old[front])
changed_faces=np.flatnonzero(mask[f].any(1));intersections,pairs=changed_intersections(v,f,changed_faces)
inherited,pairs0=changed_intersections(old,f,changed_faces)
assert not intersections,intersections[:10]
# Positive crossing and separated controls for the actual narrow-phase function.
a=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])*.01
b=np.array([[.002,.002,-.002],[.002,.002,.002],[.008,.002,0.]])
assert triangle_intersects(a,b) and not triangle_intersects(a,b+np.array([0,0,.1]))
curves=[]
for side in [1,-1]:
    for y in [.018,.020,.025,.030]:
        xvalues=np.arange(.135,.170001,.00125);before=[];after=[];rows=[]
        for xx in xvalues:
            h0=roof(old,f,side*xx,y);h1=roof(v,f,side*xx,y)
            if h0 and h1:
                before.append(h0['world']);after.append(h1['world']);rows.append(dict(x=float(side*xx),before=h0,after=h1,delta_z_mm=(h1['world'][2]-h0['world'][2])*1000))
        def turns(q):
            q=np.asarray(q);d=q[3:]-q[:-3];d/=np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-30)
            angle=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',d[3:],d[:-3]),-1,1)))
            return dict(chord_span_mm=3.75,adjacent_span_mm=3.75,maximum_degrees=float(angle.max()) if len(angle) else None,p95_degrees=float(np.percentile(angle,95)) if len(angle) else None)
        curves.append(dict(side=side,plane_Y=y,matched_samples=len(rows),before_turn=turns(before),after_turn=turns(after),samples=rows))
gaps=[]
for z in [1.240,1.250,1.260]:
    for y in [-.020,0.,.010,.020,.030]:
        samples=[]
        for label,q in [('before',old),('after',v)]:
            hits=[h for h in line_hits(q,f,0,{1:y,2:z}) if 0<h['world'][0]<.30]
            # Torso center is inside this connected design at the stated line.
            intervals=[[hits[i]['world'][0],hits[i+1]['world'][0]] for i in range(0,len(hits)-1,2)]
            samples.append(dict(state=label,hits=hits,air_intervals=intervals,widths_mm=[1000*(b-a) for a,b in intervals]))
        gaps.append(dict(z=z,y=y,comparison=samples))
low_main=next(r for r in gaps if r['z']==1.260 and r['y']==0.)
assert low_main['comparison'][1]['air_intervals'],'The demonstrated lower passage closed'
# First15 and D bytes are protected individually; unrelated new namespace files may appear.
protected=json.loads((P/'protected-input-hashes.json').read_text(encoding='utf-8'))
protected={p:h for p,h in protected.items() if 'bra-diagnostic' not in Path(p).parts}
for path,h in protected.items():assert sha(path)==h,('Frozen input changed',path)
(P/'protected-input-hashes.json').write_text(json.dumps(protected,indent=2)+'\n',encoding='utf-8',newline='\n')
turn=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',n0[changed_faces],n1[changed_faces]),-1,1)))
report=dict(status='CPU_GEOMETRY_GUARDS_PASS; FORM/ART UNVERIFIED',candidate_sha256=sha(P/'posterior08.npz'),active_vertices=len(active),fixed_vertices=len(fixed),changed_faces=len(changed_faces),
    original_topology_exact=True,finite=True,boundary_edges=int((counts==1).sum()),nonmanifold_edges=int((counts>2).sum()),euler_characteristic=int(len(v)-len(edges)+len(f)),minimum_double_triangle_area_m2=float(area.min()),
    orientation_reversals=int((dot<=0).sum()),outside_vertices_exact=int((~mask).sum()),front_or_opposite_vertices_exact=int(front.sum()),breast_support_coordinates_exact=True,
    candidate_local_vs_all_nonadjacent_intersections=intersections,baseline_same_pairs_intersections=inherited,narrow_phase_pairs=pairs,baseline_pairs=pairs0,positive_intersection_control=True,
    maximum_displacement_mm=float(np.linalg.norm(v-old,axis=1).max()*1000),median_active_displacement_mm=float(np.median(np.linalg.norm(v[active]-old[active],axis=1))*1000),
    volume_delta_m3=volume(v.astype(float),f)-volume(old.astype(float),f),changed_face_normal_difference_degrees=np.percentile(turn,[50,90,95,99,100]).tolist(),
    frozen_D_E_files_checked=len(protected),mesh_field_C2_not_an_ART_proof=True,roof_curve_comparisons=curves,actual_line_gap_comparisons=gaps,
    limitations='Roof turns use matched physical planes and3.75mm chords; not universal anatomy thresholds. Local changed-triangle/all-mesh intersection check excludes shared-vertex pairs. Actual eight-view gray/Normal review and independent root judgment required.',native_saved=False,GPU_used=False)
(P/'CPU-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR08_CPU',json.dumps({k:report[k] for k in ['status','active_vertices','changed_faces','narrow_phase_pairs','maximum_displacement_mm','volume_delta_m3']}),flush=True)
for r in curves:print('ROOF',r['side'],r['plane_Y'],r['before_turn'],r['after_turn'])
