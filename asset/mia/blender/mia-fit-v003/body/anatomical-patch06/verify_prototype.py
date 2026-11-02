"""Fresh actual topology/head/finite/orientation/contact check. CPU only."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;B=P.parent;sys.path.insert(0,str(P));sys.path.insert(0,str(B));sys.path.insert(0,str(B/'inputs'))
import install_prototype as patch,install_posed_target_05,scene_fingerprint as fp
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads((B/'current-body-audit.json').read_text());native=Path(d['native']);assert sha(native)==d['sha256'];bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();cache={};before={o.name:fp.object_fingerprint(o,cache) for o in bpy.data.objects};envelope=fp.scene_envelope()
source=bpy.data.objects['MIA_V27_SharedHeadBody']
def evaluated(ob):
    e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles();v=patch.coords(me.vertices).astype(float);m=np.array(e.matrix_world);v=v@m[:3,:3].T+m[:3,3]
    data=dict(world=v,triangles=np.array([t.vertices[:] for t in me.loop_triangles],np.int32),materials=np.array([me.polygons[t.polygon_index].material_index for t in me.loop_triangles]),normals=patch.coords(me.vertices,'normal').astype(float));e.to_mesh_clear();return data
base=evaluated(source);ob=patch.build();new=evaluated(ob);assert np.isfinite(new['world']).all() and np.isfinite(new['normals']).all()
head0=np.flatnonzero(base['world'][:,2]>=1.465);head1=np.flatnonzero(new['world'][:,2]>=1.465)
def ordered(q,ids):
    v=q['world'][ids];n=q['normals'][ids];order=np.lexsort((n[:,2],n[:,1],n[:,0],v[:,2],v[:,1],v[:,0]));return v[order],n[order]
a,an=ordered(base,head0);b,bn=ordered(new,head1);assert a.shape==b.shape
headerr=np.linalg.norm(a-b,axis=1);normalerr=np.linalg.norm(an-bn,axis=1)
assert headerr.max()<=2e-6,('Head moved',headerr.max());assert normalerr.max()<2e-4,('Head normal differs',normalerr.max())
# Semantic head correspondence is spatial+normal sorted, not evaluated index.
report=dict(prototype_sha256=sha(P/'prototype06.npz'),native_sha256=d['sha256'],static=True,rig_and_key_migration='UNVERIFIED',UV_new_corners='UNSEATED gray-only',
    evaluated_vertices=len(new['world']),evaluated_triangles=len(new['triangles']),protected_head_vertices=[len(head0),len(head1)],protected_head_correspondence='lexicographic world position + vertexnormal, independent of global evaluated indices',
    protected_head_position_bitexact=bool(np.array_equal(a,b)),protected_head_position_max_mm=float(headerr.max()*1000),protected_head_normal_vector_max=float(normalerr.max()),finite=True)
v=new['world'];t=new['triangles'];mi=new['materials'];tri=v[t];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
center=tri.mean(1);roi=(mi==1)&(center[:,2]>1.10)&(center[:,2]<1.425)&(np.abs(center[:,0])<.35)
assert areas[roi].min()>1e-12,('Degenerate evaluated body face',areas[roi].min())
norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);front=roi&(center[:,1]<-.08)&(np.abs(center[:,0])<.12)
backward=np.flatnonzero(front&(norm[:,1]>1e-10));report.update(min_roi_triangle_area_mm2=float(areas[roi].min()*1e6),front_selection_positive_Y_normal_count=len(backward),positive_Y_sample_ids=backward[:30].tolist(),normal_classification_limit='PositiveY alone is not reversal at lateral wrapping/underfold. Full count retained; winding/finite/contact are separate from form-continuity judgment.')
np.savez_compressed(P/'evaluated06.npz',world=v,triangles=t,triangle_materials=mi)
def segment(a,b,tr):
    d=b-a;e1=tr[1]-tr[0];e2=tr[2]-tr[0];h=np.cross(d,e2);det=e1@h
    if abs(det)<1e-13:return False
    inv=1/det;s=a-tr[0];u=inv*(s@h)
    if u<=1e-6 or u>=1-1e-6:return False
    q=np.cross(s,e1);vv=inv*(d@q)
    if vv<=1e-6 or u+vv>=1-1e-6:return False
    tt=inv*(e2@q);return 1e-6<tt<1-1e-6
def intersects(x,y):return any(segment(x[i],x[(i+1)%3],y) or segment(y[i],y[(i+1)%3],x) for i in range(3))
assert intersects(np.array([[0,0,0],[1,0,0],[0,1,0.]]),np.array([[.2,.2,-1],[.2,.2,1],[.8,.8,0.]]))
ids=np.flatnonzero(roi);sub=t[ids];tree=BVHTree.FromPolygons(v.tolist(),sub.tolist(),all_triangles=True);hits=[]
for i,j in tree.overlap(tree):
    if i>=j or np.intersect1d(sub[i],sub[j]).size:continue
    if intersects(v[sub[i]],v[sub[j]]):hits.append([int(ids[i]),int(ids[j])])
report.update(contact_triangles=len(ids),strict_nonadjacent_contacts=len(hits),contact_pairs=hits[:40],positive_contact_control=True)
cache={}
for name,signature in before.items():assert fp.object_fingerprint(bpy.data.objects[name],cache)==signature,('Original mutated',name)
assert fp.scene_envelope()==envelope and sha(native)==d['sha256']
report.update(original_owners_exact=len(before),native_unchanged=True,native_saved=False,gpu_used=False,
    status='CPU finite/winding/contact/protected-data diagnostic complete; form/source/continuity remain FAIL or UNVERIFIED. Root GPU token required.')
(P/'cpu-guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PATCH06_ACTUAL_CPU_DONE',json.dumps(report),flush=True)
assert len(hits)==0,('Actual selfcontact',hits[:10])
