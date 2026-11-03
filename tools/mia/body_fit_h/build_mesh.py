"""ONE H native GN VolumeCube/VTM guide. CPU, factory empty, no native save.

Frozen roof parameters only; no neck AP map, field retune or input copy.
Spatial lower restoration is limited to unique submicrometre roundoff. Larger
lower changes are a STOP, never an unreported sculpt mask or second mesh.
"""
from pathlib import Path
import sys,json,time,hashlib,importlib.util
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from field_numpy import Model
C=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');A=C/'asset/mia/blender/mia-fit-v003';O=C/'.mia-cache/body-h/shape'
ROOF_SHA='b4ccdc0b6c87157268abc8957092dd6f0a91186d19b47734849415aed7751f15'
SOURCE_SHA='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,data):Path(path).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def section(v,f,normal,offset):
    normal=np.asarray(normal,float);normal/=np.linalg.norm(normal);t=v[f].astype(float);h=t@normal-offset;hit=(h.min(1)<=0)&(h.max(1)>=0);t=t[hit];h=h[hit];segments=[]
    for tri,d in zip(t,h):
        q=[]
        for i,j in [(0,1),(1,2),(2,0)]:
            if abs(d[j]-d[i])>1e-15 and d[i]*d[j]<=0:q.append(tri[i]+(-d[i])/(d[j]-d[i])*(tri[j]-tri[i]))
        unique=[]
        for x in q:
            if not any(np.linalg.norm(x-y)<1e-10 for y in unique):unique.append(x)
        if len(unique)==2 and np.linalg.norm(unique[0]-unique[1])>1e-10:segments.append(unique)
    points=[];index={};edges=[]
    for seg in segments:
        edge=[]
        for q in seg:
            k=tuple(np.round(q,9))
            if k not in index:index[k]=len(points);points.append(q)
            edge.append(index[k])
        if edge[0]!=edge[1]:edges.append(edge)
    if not points:return dict(segment_count=0,loop_count=0,closed=False,loops=[])
    points=np.array(points);adj=[[] for _ in points]
    for i,j in edges:adj[i].append(j);adj[j].append(i)
    seen=set();loops=[]
    for start in range(len(points)):
        if start in seen:continue
        order=[];stack=[start]
        while stack:
            i=stack.pop()
            if i in seen:continue
            seen.add(i);order.append(i);stack.extend(adj[i])
        q=points[order];closed=all(len(adj[i])==2 for i in order)
        loops.append(dict(vertices=len(order),closed=closed,bounds=[q.min(0).tolist(),q.max(0).tolist()],bbox_center=((q.min(0)+q.max(0))/2).tolist(),mean=q.mean(0).tolist()))
    return dict(normal=normal.tolist(),offset=float(offset),segment_count=len(edges),loop_count=len(loops),closed=all(x['closed'] for x in loops),loops=loops,meaning='Actual evaluated mesh/plane intersections;1nm endpoint-key rounding only for connectivity, no mesh coordinate edits.')

def outer_roof(v,f,threshold=.085):
    best=None
    for sign in [-1,1]:
        tri=v[f].astype(float);inside=sign*tri[:,:,0]>=threshold
        for k in range(3):
            ids=np.flatnonzero(inside[:,k])
            if len(ids):
                j=ids[np.argmax(tri[ids,k,2])];q=tri[j,k]
                if best is None or q[2]>best['point'][2]:best=dict(point=q.tolist(),triangle=int(j),side=sign,type='meshvertex')
        for i,j in [(0,1),(1,2),(2,0)]:
            a=sign*tri[:,i,0]-threshold;b=sign*tri[:,j,0]-threshold;ids=np.flatnonzero((a*b<0)&(abs(a-b)>1e-15))
            if len(ids):
                tt=-a[ids]/(b[ids]-a[ids]);q=tri[ids,i]+tt[:,None]*(tri[ids,j]-tri[ids,i]);k=int(np.argmax(q[:,2]));point=q[k]
                if best is None or point[2]>best['point'][2]:best=dict(point=point.tolist(),triangle=int(ids[k]),side=sign,type='triangleclippedatabsXthreshold')
    return dict(threshold_absX_m=threshold,max_Z=None if best is None else best['point'][2],witness=best,meaning='Maximum actual triangle surface outsideabsX>=.085, including clippededgeintersections; stronger than vertices-only cap test.')

def topology(v,f):
    e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);direction=np.where(e[:,0]<e[:,1],1,-1);u,inv,count=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True);w=np.bincount(inv,weights=direction,minlength=len(u));cross=np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]);area=np.linalg.norm(cross,axis=1)
    parent=np.arange(len(v))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in u:
        a,b=find(int(i)),find(int(j))
        if a!=b:parent[b]=a
    components=len({find(i) for i in range(len(v))});volume=float(np.einsum('ij,ij->i',v[f[:,0]].astype(float),np.cross(v[f[:,1]].astype(float),v[f[:,2]].astype(float))).sum()/6)
    return dict(vertices=len(v),triangles=len(f),finite=bool(np.isfinite(v).all()),zero_area_faces=int((area<=1e-16).sum()),boundary_edges=int((count==1).sum()),nonmanifold_edges=int((count>2).sum()),inconsistent_oriented_edges=int((w!=0).sum()),connected_components=components,signed_volume_m3=volume,minimum_double_area_m2=float(area.min()))

def main():
    capacity=load('H_mesh_capacity',A/'integration/workspace-storage-20261103/storage_guard.py').inspect(128*1024*1024)
    if capacity['violations']:raise RuntimeError(json.dumps(capacity))
    roof_path=O/'roof-fit.json';source=A/'body/shoulder11/shoulder11-canonical.npz';assert sha(roof_path)==ROOF_SHA and sha(source)==SOURCE_SHA
    raw_path=O/'H-guide-raw.npz';final_path=O/'H-guide.npz';report_path=O/'H-guide-build.json';assert not raw_path.exists() and not final_path.exists() and not report_path.exists(),'ONE approved mesh; never overwrite/rebuild'
    model=Model(C);params=np.array(json.loads(roof_path.read_text(encoding='utf-8'))['params'][:5]);expr=model.expression(params);base=model.base;spec=model.p['mesher'];report=dict(status='BUILDING_ONE_UNSELECTED_H_GUIDE',roof_fit_sha256=ROOF_SHA,source11_sha256=SOURCE_SHA,params5=params.tolist(),model=model.metadata(params),capacity=capacity,blender_version=bpy.app.version_string,native_opened=False,native_saved=False,GPU_used=False,neck_AP_map_applied=False,inputs_copied=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Same native GN field implementation checked at both old and edited sites.
    probes=np.array([[0,-.01,1.25],[-.066,-.155,1.257],[.066,-.155,1.257],[.14,-.03,1.31],[.18,0,1.30],[.27,0,1.12],[0,-.19,1.25],[.30,.10,1.4],[.14,-.014,1.375],[.04,0,1.42],[.07,.035,1.39],[.155,-.014,1.36]],np.float32)
    pm=bpy.data.meshes.new('H_FieldProbePoints');pm.from_pydata(probes.tolist(),[],[]);po=bpy.data.objects.new(pm.name,pm);bpy.context.scene.collection.objects.link(po);pg=bpy.data.node_groups.new('H_FieldProbe','GeometryNodeTree');pg.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');pg.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');pin=pg.nodes.new('NodeGroupInput');pout=pg.nodes.new('NodeGroupOutput');store=pg.nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='FLOAT';store.domain='POINT';store.inputs['Name'].default_value='H_actual_field';pg.links.new(pin.outputs[0],store.inputs['Geometry']);pg.links.new(base.nodes(pg,expr),store.inputs['Value']);pg.links.new(store.outputs[0],pout.inputs[0]);po.modifiers.new('H_FieldProbe','NODES').node_group=pg;bpy.context.view_layer.update();ev=po.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();actual=np.array([x.value for x in mesh.attributes['H_actual_field'].data]);expected=model.reference(probes,params);error=float(abs(actual-expected).max());assert error<2e-6,('Nativefieldprobe',error);ev.to_mesh_clear();report['field_probe_max_abs_error_not_distance']=error
    me=bpy.data.meshes.new('H_Empty');ob=bpy.data.objects.new('H_FROZEN_ROOF_GUIDE',me);bpy.context.scene.collection.objects.link(ob);ng=bpy.data.node_groups.new('H_OneNativeVolumeCube','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');out=ng.nodes.new('NodeGroupOutput');density=base.ma(.5-expr/spec['density_scale_m'],0.);den=base.nodes(ng,density);vol=ng.nodes.new('GeometryNodeVolumeCube');vol.inputs['Background'].default_value=spec['background'];vol.inputs['Min'].default_value=spec['bounds_min'];vol.inputs['Max'].default_value=spec['bounds_max'];extent=np.array(spec['bounds_max'])-spec['bounds_min'];res=np.ceil(extent/spec['voxel_m']).astype(int)+1
    for axis,n in zip('XYZ',res):vol.inputs['Resolution '+axis].default_value=int(n)
    assert res.tolist()==[225,120,175];ng.links.new(den,vol.inputs['Density']);vm=ng.nodes.new('GeometryNodeVolumeToMesh');vm.inputs['Threshold'].default_value=spec['threshold'];vm.inputs['Adaptivity'].default_value=0.;ng.links.new(vol.outputs['Volume'],vm.inputs['Volume']);ng.links.new(vm.outputs['Mesh'],out.inputs['Geometry']);ob.modifiers.new('H_OneNativeMesher','NODES').node_group=ng
    start=time.time();bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();v=np.empty(len(mesh.vertices)*3,np.float32);mesh.vertices.foreach_get('co',v);v=v.reshape(-1,3);f=np.array([t.vertices[:] for t in mesh.loop_triangles],np.int32);assert len(v)>1000 and np.isfinite(v).all();np.savez_compressed(raw_path,world=v,triangles=f);report.update(raw_mesh_sha256=sha(raw_path),mesher_seconds=time.time()-start,resolution=res.tolist(),actual_grid_step_m=(extent/(res-1)).tolist(),node_count=len(ng.nodes),raw_topology=topology(v,f));write(report_path,report)
    # Spatial proof, never same-index assumptions across a new VDB mesh.
    old=np.load(source);oldv=old['world'];oldf=old['triangles'];ids=np.flatnonzero(oldv[:,2]<=1.34);tree=KDTree(len(v))
    for i,q in enumerate(v):tree.insert(Vector(q),i)
    tree.balance();mapped=[];dist=[];ambiguous=[]
    for i in ids:
        nn=tree.find_n(Vector(oldv[i]),2);mapped.append(nn[0][1]);dist.append(nn[0][2])
        if len(nn)>1 and nn[1][2]-nn[0][2]<1e-7 and nn[0][2]>1e-9:ambiguous.append(int(i))
    mapped=np.array(mapped,np.int32);dist=np.array(dist);unique=len(np.unique(mapped))==len(mapped);newlow=np.flatnonzero(v[:,2]<=1.34);oldnew=dict(old_count=len(ids),new_count=len(newlow),unique_mapping=unique,ambiguous_old_ids=ambiguous,max_raw_distance_m=float(dist.max()),submicrometre_threshold_m=1e-6,raw_exact_count=int(np.all(v[mapped]==oldv[ids],axis=1).sum()))
    can=unique and not ambiguous and np.all(dist<=1e-6) and set(newlow.tolist())==set(mapped.tolist());report['lower_spatial_guard']=oldnew
    report['sections']={str(z):section(v,f,[0,0,1],z) for z in [1.397,1.415,1.42,1.434]};report['outer_cap_roof']=outer_roof(v,f)
    endpoint={};endpoint['waistZ1.145']=section(v,f,[0,0,1],1.145)
    for sign,label in [(1,'armR'),(-1,'armL')]:
        axis=np.array([sign*np.sin(np.radians(25)),0.,-np.cos(np.radians(25))]);point=np.array([sign*.236,0,1.17])-.020*axis;endpoint[label]=section(v,f,axis,float(point@axis))
    report['E_endpoint_coverage']=endpoint
    if not can:
        report['status']='STOP_LOWER_PHYSICAL_HOLD_NOT_ROUNDOFF';report['final_mesh_written']=False;write(report_path,report);raise RuntimeError('Raw lower geometry change exceeds approved unique submicrometre restoration; no mask/rebuild')
    raw=v.copy();changed=ids[np.any(v[mapped]!=oldv[ids],axis=1)];changed_new=mapped[np.any(v[mapped]!=oldv[ids],axis=1)];v[mapped]=oldv[ids];assert np.array_equal(v[mapped],oldv[ids]);restoration=[dict(old_id=int(i),new_id=int(j),raw=raw[j].tolist(),restored=v[j].tolist(),distance_m=float(np.linalg.norm(raw[j].astype(float)-v[j]))) for i,j in zip(changed,changed_new)]
    mapping=np.full(len(oldv),-1,np.int32);mapping[ids]=mapped;oldtris=oldf[np.all(oldv[oldf,2]<=1.34,axis=1)];newtris=f[np.all(v[f,2]<=1.34,axis=1)];oldkeys={tuple(sorted(x)) for x in mapping[oldtris]};newkeys={tuple(sorted(x)) for x in newtris};exact_tri=oldkeys==newkeys
    normal_delta=0.
    if len(changed_new):
        incident=f[np.isin(f,changed_new).any(1)];nr=np.cross(raw[incident[:,1]].astype(float)-raw[incident[:,0]],raw[incident[:,2]].astype(float)-raw[incident[:,0]]);nf=np.cross(v[incident[:,1]].astype(float)-v[incident[:,0]],v[incident[:,2]].astype(float)-v[incident[:,0]]);nr/=np.linalg.norm(nr,axis=1)[:,None];nf/=np.linalg.norm(nf,axis=1)[:,None];normal_delta=float(np.degrees(np.arccos(np.clip(np.sum(nr*nf,axis=1),-1,1))).max())
    report['lower_spatial_guard'].update(final_coordinates_byte_exact=True,old_lower_triangles=len(oldtris),new_lower_triangles=len(newtris),physical_vertex_triplets_exact=exact_tri,missing_triangle_count=len(oldkeys-newkeys),extra_triangle_count=len(newkeys-oldkeys));report['numerical_restoration']=dict(count=len(restoration),vertices=restoration,maximum_incident_geometric_normal_delta_degrees=normal_delta,meaning='ONLY unique <=1micrometre native roundoff restoration; no wholeROI sculpt mask. RawNPZ retained unchanged.')
    if not exact_tri:
        report['status']='STOP_LOWER_TRIANGLE_CORRESPONDENCE';report['final_mesh_written']=False;write(report_path,report);raise RuntimeError('Lower physical triangle triplets changed; no silent topology patch')
    report['final_topology']=topology(v,f);top=report['final_topology'];assert top['finite'] and top['zero_area_faces']==0 and top['boundary_edges']==0 and top['nonmanifold_edges']==0 and top['inconsistent_oriented_edges']==0 and top['connected_components']==1 and top['signed_volume_m3']>0
    geom=load('H_triangle_helpers',A/'body/posterior-continuity08/geometry.py');tree=BVHTree.FromPolygons([Vector(x) for x in v],f.tolist(),all_triangles=True);upper=np.flatnonzero(np.any(v[f,2]>1.34,axis=1));utree=BVHTree.FromPolygons([Vector(x) for x in v],f[upper].tolist(),all_triangles=True);seen=set();intersections=[]
    for local,j in utree.overlap(tree):
        i=int(upper[local]);j=int(j);key=tuple(sorted((i,j)))
        if i==j or key in seen or np.intersect1d(f[i],f[j]).size:continue
        seen.add(key)
        if geom.triangle_intersects(v[f[i]].astype(float),v[f[j]].astype(float)):intersections.append(key)
    report['changed_upper_vs_whole_mesh_intersections']=intersections;report['intersection_candidate_pairs']=len(seen);assert not intersections
    oldvol=geom.volume(oldv.astype(float),oldf);report['upperguide_volume_delta_m3']=top['signed_volume_m3']-oldvol;report['volume_scope']='Wholeclosedstaticupperguide including temporaryneckstub, not medical anatomy/fullbodyvolume.'
    np.savez_compressed(final_path,world=v,triangles=f);np.savez_compressed(O/'H-lower-correspondence.npz',old_ids=ids.astype(np.int32),H_ids=mapped)
    report.update(status='ONE_H_GUIDE_CPU_READY_UNSELECTED_NOT_ART',final_mesh_written=True,final_mesh_path=str(final_path),final_mesh_sha256=sha(final_path),world_sha256=hashlib.sha256(v.tobytes()).hexdigest(),triangles_sha256=hashlib.sha256(f.tobytes()).hexdigest(),source11_bytes_held=sha(source)==SOURCE_SHA,roof_fit_bytes_held=sha(roof_path)==ROOF_SHA)
    write(report_path,report);ev.to_mesh_clear();assert report['source11_bytes_held'] and report['roof_fit_bytes_held'];print('H_ONE_GUIDE_READY',str(final_path),report['final_mesh_sha256'],json.dumps(report['lower_spatial_guard']),flush=True)

if __name__=='__main__':main()
