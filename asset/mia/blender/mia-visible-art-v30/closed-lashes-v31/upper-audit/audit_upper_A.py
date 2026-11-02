"""Independent upper A25-state preservation/structure/whole-front contact."""
import bpy,numpy as np,json,sys,hashlib,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;W=P.parent
B=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Review.blend')
A=W/'Mia_LashPose_v31_A.blend';BSHA='c3557e9eaa2163ae0d6f712a8c51362c0a6abdab628bcabe3e9673511323813c';ASHA='d98e80ceb438b3b4fab1028f2f4b5b4a85152a6de1930a538321f6cd732b2a24'
assert hashlib.sha256(B.read_bytes()).hexdigest()==BSHA and hashlib.sha256(A.read_bytes()).hexdigest()==ASHA
sys.path.insert(0,str(W.parent/'mia-eye-lash-v29'));from audit_mesh_helpers import snapshot
bo,_,bm,bi=snapshot(B)
names=['V30_UpperLashes_-1','V30_UpperLashes_1'];before={n:np.array([[v.co[:] for v in k.data] for k in bpy.data.objects[n].data.shape_keys.key_blocks]) for n in names};raw={n:np.array([v.co[:] for v in bpy.data.objects[n].data.vertices]) for n in names}
ao,_,am,ai=snapshot(A)
master=bpy.data.objects['MIA_V27_Foundation_Face'];keys=master.data.shape_keys.key_blocks;kn=[k.name for k in keys]
checks={'all_nonupper_mesh_records_exact':all(bo[n]==ao[n] for n in bo if n not in names),'all_upper_noncoordinate_fields_exact':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k!='coordinates') for n in names),'all_material_graphs_exact':bm==am,'all_images_exact':bi==ai}
for n in names:
    side=int(n.rsplit('_',1)[1]);allowed={'Face.M_F00_000_00_Fcl_EYE_Close','Face.M_F00_000_00_Fcl_EYE_Close_'+('R' if side<0 else 'L')};ob=bpy.data.objects[n];after=np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks]);checks[n+'_raw_neutral_exact']=np.array_equal(raw[n],np.array([v.co[:] for v in ob.data.vertices]));checks[n+'_all_other_keys_exact']=all(np.array_equal(before[n][i],after[i]) for i,nm in enumerate(kn) if nm not in allowed)
meta=json.loads((W.parent/'mia-eye-visible-v30/lash-M-audit.json').read_text());info={d['owner']:d for d in meta['created'] if 'Upper' in d['owner']}
topo={};ownership={}
for n in names:
    ob=bpy.data.objects[n];me=ob.data;me.calc_loop_triangles();tri=np.array([t.vertices[:] for t in me.loop_triangles]);adj=collections.defaultdict(set);ec=collections.Counter()
    for f in me.polygons:
        vs=list(f.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):adj[a].add(b);adj[b].add(a);ec[tuple(sorted((a,b)))]+=1
    todo=set(range(len(me.vertices)));components=[]
    while todo:
        v=todo.pop();vis={v};stack=[v]
        while stack:
            for j in adj[stack.pop()]&todo:todo.remove(j);vis.add(j);stack.append(j)
        components.append(np.array(sorted(vis)))
    topo[n]={'tri':tri,'components':components,'all_edges_two_faces':all(c==2 for c in ec.values()),'boundary_or_nonmanifold_edges':sum(c!=2 for c in ec.values())}
    ownership[n]={}
    for st in info[n]['station_bindings']:
        ids=st['vertex_indices']
        for row,(front,back) in enumerate(zip(ids[::2],ids[1::2])):ownership[n][front]={'back':back,'station_t':st['t'],'row':row,'root':bool(st['attached'] and row==0),'attached_station':st['attached']}
states=[('neutral',None,0)]+[(label+'@'+str(v),'Face.M_F00_000_00_Fcl_EYE_Close'+suffix,v) for label,suffix in [('Close',''),('Close_R','_R'),('Close_L','_L')] for v in [.125,.25,.375,.5,.625,.75,.875,1.]]
rows=[]
for label,control,value in states:
    for k in keys:k.value=value if k.name==control else 0
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();se=bpy.data.objects['MIA_V27_SharedHeadBody'].evaluated_get(dg);sm=se.to_mesh();sp=np.array([se.matrix_world@v.co for v in sm.vertices]);bv=BVHTree.FromPolygons(sp,[list(f.vertices) for f in sm.polygons]);frontY=float(sp[:,1].min()-.20);se.to_mesh_clear();state={'state':label,'control':control,'value':value,'owners':{}}
    for n in names:
        ob=bpy.data.objects[n];ev=ob.evaluated_get(dg);me=ev.to_mesh();q=np.array([ev.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear();tr=topo[n]['tri'];tq=q[tr];area=np.linalg.norm(np.cross(tq[:,1]-tq[:,0],tq[:,2]-tq[:,0]),axis=1)/2*1e6;volumes=[]
        for ids in topo[n]['components']:
            use=np.isin(tr[:,0],ids);t=(q-q[ids].mean(0))[tr[use]];volumes.append(float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6*1e9))
        root=[];nonroot=[];centre=[];miss=[];backhit=[];buried=[];nearest=[]
        for i,bind in ownership[n].items():
            pt=q[i];h=bv.ray_cast(Vector((pt[0],frontY,pt[2])),Vector((0,1,0)))
            if h[0] is None:miss.append({'vertex':i,**bind,'point':pt.tolist()});continue
            if h[1].y>=-.05:backhit.append({'vertex':i,**bind,'normal_y':h[1].y,'point':pt.tolist()});continue
            c=float((h[0].y-pt[1])*1000);(root if bind['root'] else nonroot).append(c)
            cp=(pt+q[bind['back']])/2;ch=bv.ray_cast(Vector((cp[0],frontY,cp[2])),Vector((0,1,0)))
            if ch[0] is not None and ch[1].y<-.05:centre.append(float((ch[0].y-cp[1])*1000))
            if not bind['root'] and c<-.01:buried.append({'vertex':i,**bind,'forward_clearance_mm':c,'world':pt.tolist(),'actual_skin_hit':list(h[0]),'skin_normal_y':h[1].y})
            nh=bv.find_nearest(Vector(pt));nearest.append(float(np.dot(pt-np.array(nh[0]),np.array(nh[1]))*1000))
        stat=lambda vals:[float(min(vals)),float(np.median(vals)),float(max(vals))] if vals else None
        state['owners'][n]={'all_edges_two_faces':topo[n]['all_edges_two_faces'],'boundary_or_nonmanifold_edges':topo[n]['boundary_or_nonmanifold_edges'],'component_signed_volumes_mm3':volumes,'nonpositive_component_count':sum(v<=0 for v in volumes),'minimum_triangle_area_mm2':float(area.min()),'zero_area_triangle_count':int((area==0).sum()),'collapsed_below1e_minus12_mm2':int((area<1e-12).sum()),'whole_nonroot_front_forward_clearance_mm_min_median_max':stat(nonroot),'attached_root_front_forward_clearance_mm_min_median_max':stat(root),'all_section_centre_forward_clearance_mm_min_median_max':stat(centre),'front_nearest_normal_signed_mm_min_median_max':stat(nearest),'nonroot_front_below_minus10microns_count':len(buried),'buried_nonroot_front_examples':sorted(buried,key=lambda d:d['forward_clearance_mm'])[:16],'no_forward_skin_hit':miss,'first_hit_not_frontfacing':backhit,'measured_nonroot_front_count':len(nonroot),'measured_root_front_count':len(root)}
    rows.append(state);print('UPPER_A_GUARD',label,{n:{'min_nonroot':d['whole_nonroot_front_forward_clearance_mm_min_median_max'][0] if d['whole_nonroot_front_forward_clearance_mm_min_median_max'] else None,'buried':d['nonroot_front_below_minus10microns_count'],'minvolume':min(d['component_signed_volumes_mm3']),'zeroarea':d['zero_area_triangle_count'],'nohit':len(d['no_forward_skin_hit'])} for n,d in state['owners'].items()},flush=True)
allrows=[d for s in rows for d in s['owners'].values()]
summary={'states':len(states),'preservation_checks_all_true':all(checks.values()),'nonpositive_volume_components':sum(d['nonpositive_component_count'] for d in allrows),'zero_area_triangles':sum(d['zero_area_triangle_count'] for d in allrows),'collapsed_below1e_minus12_mm2':sum(d['collapsed_below1e_minus12_mm2'] for d in allrows),'min_component_volume_mm3':min(v for d in allrows for v in d['component_signed_volumes_mm3']),'minimum_nonroot_front_forward_clearance_mm':min(d['whole_nonroot_front_forward_clearance_mm_min_median_max'][0] for d in allrows if d['whole_nonroot_front_forward_clearance_mm_min_median_max']),'nonroot_front_below_minus10microns_samples':sum(d['nonroot_front_below_minus10microns_count'] for d in allrows),'no_forward_skin_hit_samples':sum(len(d['no_forward_skin_hit']) for d in allrows),'nonmanifold_owners':sum(not topo[n]['all_edges_two_faces'] for n in names)}
report={'native':str(A),'sha256':ASHA,'baseline':str(B),'baseline_sha256':BSHA,'checks':checks,'summary':summary,'states':rows,'method':'Actual saved-native evaluated meshes in25single-control states: neutral+Close/R/L at.125increments. Closed component centered signed volumes, exact topology2faces-peredge, trianglearea, and WHOLE nominalfront upper fan point-to-actualskin forwardYray clearance. Attachedrootrows separated. No-hit/nonfrontfacing firsthit are explicit rather than accepted clearances.','limits':'Positive volume alone cannot establish contact or style. Vertex contact can miss between-vertex intersections; no camera/raster appearance or fullcollision certification. Free wing outside face may have no forward skin hit. Roots intentionally embed separately. No arbitrary additive controls/headfollow. No GPU/native saves.','inputs_unchanged':{'baseline':hashlib.sha256(B.read_bytes()).hexdigest()==BSHA,'A':hashlib.sha256(A.read_bytes()).hexdigest()==ASHA}}
(P/'upper-A-guard.json').write_text(json.dumps(report,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v)),encoding='utf8')
print('UPPER_A_GUARD_SUMMARY',json.dumps(summary),flush=True)
