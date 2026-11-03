"""Actual body-only packed reviewUV; oldhead UV/cornerdata never unwrapped."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,math,time,sys,importlib.util
P=Path(__file__).resolve().parent;wide='--revision-E' in sys.argv;geometry=P/('joined-expanded-E.npz' if wide else 'joined-static.npz');surfacePath=P/('surface-v8-expanded-E.npz' if wide else 'surface.npz');metaPath=surfacePath.with_suffix('.json');atlasPath=P/('atlas-E.npz' if wide else 'atlas.npz');assembly=json.loads((P/('assembly-E.json' if wide else 'assembly.json')).read_text());d=np.load(geometry);v=d['world'];f=d['triangles'];body=d['source_part']!=1
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
assert not surfacePath.exists(),'Final atlas payload must not silentlyoverwrite'
bpy.ops.wm.read_factory_settings(use_empty=True);me=bpy.data.meshes.new('Review12_JoinedStatic_ForAtlas');me.from_pydata(v.tolist(),[],f.tolist());me.update();ob=bpy.data.objects.new('Review12_CPU_ATLAS_ONLY',me);bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
for i,name in enumerate(['UVMap','MIA_BODY_V23_UV','MIA_V002_UnderwearUV']):
    uv=me.uv_layers.new(name=name);uv.data.foreach_set('uv',d['old_loop_uv'][:,:,i,:].ravel())
before=[np.asarray([a.uv[:] for a in uv.data],np.float32) for uv in me.uv_layers]
me.uv_layers.new(name='MIA_Review12UV',do_init=False);me.uv_layers.active_index=len(me.uv_layers)-1
bpy.context.tool_settings.mesh_select_mode=(False,False,True);bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(me);bm.faces.ensure_lookup_table()
for face in bm.faces:face.select_set(bool(body[face.index]))
bm.select_flush_mode();bmesh.update_edit_mesh(me,loop_triangles=False,destructive=False)
assert sum(face.select for face in bm.faces)==int(body.sum())
assert bm.loops.layers.uv.active.name=='MIA_Review12UV',bm.loops.layers.uv.active.name
print('ACTUAL_UV_SELECTION',int(body.sum()),bm.loops.layers.uv.active.name,flush=True);start=time.time()
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,area_weight=0.,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
review=me.uv_layers['MIA_Review12UV'];uvall=np.asarray([a.uv[:] for a in review.data],np.float32).reshape(-1,3,2)
for i,old in enumerate(before):assert np.array_equal(old,np.asarray([a.uv[:] for a in me.uv_layers[i].data],np.float32))
assert np.isfinite(uvall[body]).all() and uvall[body].min()>=-1e-6 and uvall[body].max()<=1.000001
dua=uvall[body,1]-uvall[body,0];dub=uvall[body,2]-uvall[body,0];uvarea=abs(dua[:,0]*dub[:,1]-dua[:,1]*dub[:,0])
if not (uvarea>0).all():
    bad=np.flatnonzero(body)[uvarea==0];q=v[f[bad]].astype(float);failure=dict(face_ids=bad.tolist(),uv=uvall[bad].tolist(),world=q.tolist(),physical_double_area_m2=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1).tolist())
    (P/'E-UV-microtriangle-failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8',newline='\n')
    if wide:
        assert bad.tolist()==[218348,218349] and max(failure['physical_double_area_m2'])<1e-12
        rawPath=P/'atlas-E-raw.npz'
        if not rawPath.exists():np.savez_compressed(rawPath,loop_uv=uvall)
        beforeUV=uvall[bad].copy();origin=beforeUV[0,0].copy();assert np.all(beforeUV==origin)
        # A collapsed two-face submicron island is restored as its connected fan
        # at ONE float32 ULP per axis. No other face/channel/world point changes.
        upU=np.nextafter(origin[0],np.float32(np.inf));downU=np.nextafter(origin[0],np.float32(-np.inf));upV=np.nextafter(origin[1],np.float32(np.inf))
        keys=[95603,110110,110111,110112];points={keys[0]:origin,keys[1]:np.array([upU,origin[1]],np.float32),keys[2]:np.array([origin[0],upV],np.float32),keys[3]:np.array([downU,origin[1]],np.float32)}
        assert f[bad].tolist()==[[95603,110110,110111],[95603,110111,110112]]
        repairs=[]
        for j,faceid in enumerate(bad):
            restored=np.array([points[int(vi)] for vi in f[faceid]],np.float32);assert abs(restored-beforeUV[j]).max()<=1e-7
            uvall[faceid]=restored;da=restored[1].astype(float)-restored[0];db=restored[2].astype(float)-restored[0];assert da[0]*db[1]-da[1]*db[0]>0
            repairs.append(dict(face=int(faceid),old_uv=beforeUV[j].tolist(),new_uv=restored.tolist(),old_signed_double_area=0.,new_signed_double_area=float(da[0]*db[1]-da[1]*db[0])))
        raw=np.load(rawPath)['loop_uv'];changedUV=np.flatnonzero(np.any(raw!=uvall,axis=(1,2)));assert changedUV.tolist()==bad.tolist()
        adjacent=np.flatnonzero(np.isin(f,f[bad].ravel()).any(1)&~np.isin(np.arange(len(f)),bad));assert np.array_equal(raw[adjacent],uvall[adjacent])
        (P/'E-UV-microtriangle-restoration.json').write_text(json.dumps(dict(scope='Root-approved two-face float32 UV micro-island restoration only, one ULP per axis. Submicron world triangles/topology/alloldheadUV unchanged; no ART claim.',raw_atlas_path=str(rawPath),raw_atlas_sha256=sha(rawPath),repairs=repairs,changed_face_ids=changedUV.tolist(),adjacent_faces_unchanged=adjacent.tolist(),maximum_uv_delta=float(abs(uvall[bad]-beforeUV).max()),shared_internal_uv_edge_exact=True),indent=2)+'\n',encoding='utf-8',newline='\n')
        dua=uvall[body,1]-uvall[body,0];dub=uvall[body,2]-uvall[body,0];uvarea=abs(dua[:,0]*dub[:,1]-dua[:,1]*dub[:,0])
assert (uvarea>0).all(),('ZEROAREA_BODY_UV',int((uvarea==0).sum()))
cent=v[f].mean(1);limb=d['vertex_limb_weights'][f].mean(1);region=np.where(cent[:,1]<-.006,1,2).astype(np.int16)
arms=(np.maximum(limb[:,0],limb[:,1])>.45)|((abs(cent[:,0])>.175)&(cent[:,2]<1.35))
region[arms&(cent[:,0]>=0)]=6;region[arms&(cent[:,0]<0)]=7
legs=(np.maximum(limb[:,2],limb[:,3])>.55)&(cent[:,2]<.98)&~arms
region[legs&(cent[:,0]>=0)]=10;region[legs&(cent[:,0]<0)]=11
pelvis=(cent[:,2]<1.10)&~arms&~legs;region[pelvis&(cent[:,1]<-.006)]=8;region[pelvis&(cent[:,1]>=-.006)]=9
neck=(cent[:,2]>1.40)&(abs(cent[:,0])<.085);region[neck]=3
shoulder=(cent[:,2]>1.34)&(abs(cent[:,0])>=.085);region[shoulder&(cent[:,1]<-.006)]=4;region[shoulder&(cent[:,1]>=-.006)]=5
collar=d['source_part']==3;region[collar&(cent[:,2]>1.40)]=12;region[collar&(abs(cent[:,0])<.17)&(cent[:,2]<1.2)]=13;region[collar&(cent[:,0]>.17)]=14;region[collar&(cent[:,0]<-.17)]=15
if wide:
    # Source branches and actual implicit upper-arm ownership prevent paint on hands/innerarms.
    arms=(d['source_part']==0)&(np.maximum(limb[:,0],limb[:,1])>.45)
    guideCandidate=np.flatnonzero((d['source_part']==2)&(abs(cent[:,0])>.12)&(cent[:,2]<1.34))
    spec=importlib.util.spec_from_file_location('review12_E_sourcefield',P.parent/'shoulder11/field.py');field=importlib.util.module_from_spec(spec);spec.loader.exec_module(field);_,reg=field.make(json.loads((P.parent/'shoulder11/parameters.json').read_text()))
    q=cent[guideCandidate].astype(float);av=np.minimum(field.evaluate(reg['upper_arm_R'],q),field.evaluate(reg['upper_arm_L'],q));ov=np.minimum.reduce([field.evaluate(reg[k],q) for k in ['curved_tapered_thorax_neck','breast_pair','anterior_fan_R','anterior_fan_L','posterior_wall_R','posterior_wall_L','shoulder_R','shoulder_L']]);arms[guideCandidate[av<ov]]=True
    region[arms&(cent[:,0]>=0)]=6;region[arms&(cent[:,0]<0)]=7
    # Exact construction ancestry, never a global height/width mask for collars.
    for name,label in [('neck',12),('waist',13),('armR',14),('armL',15)]:
        lo,hi=assembly['collar_triangle_ranges'][name];region[lo:hi]=label
ids=np.flatnonzero(body);uv=uvall[body];tri=f[body]
np.savez_compressed(atlasPath,loop_uv=uvall)
np.savez_compressed(surfacePath,world=v,triangles=tri,loop_uv=uv,face_region=region[body],meshfaceid=ids.astype(np.int32))
labels={1:'torso_front',2:'torso_back',3:'neck',4:'shoulder_front',5:'shoulder_back',6:'arm_positiveX_characterL',7:'arm_negativeX_characterR',8:'pelvis_front',9:'pelvis_back',10:'leg_positiveX_characterL',11:'leg_negativeX_characterR',12:'neck_join_collar',13:'waist_join_collar',14:'arm_join_positiveX',15:'arm_join_negativeX'}
source=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/underwear-fit/baseline-inputs.json');sourceContext=json.loads(source.read_text(encoding='utf-8'))
meta=dict(schema_version=1,scope='NEW staticjoined fullbodyreview BODY-only faces; originalhead/face excluded. NotproductionUV/rig.',uv_layer='MIA_Review12UV',
    world_shape=list(v.shape),triangles_shape=list(tri.shape),loop_uv_shape=list(uv.shape),geometry_world_sha256=ah(v),triangles_sha256=ah(tri),loop_uv_sha256=ah(uv),surface_npz_sha256=sha(surfacePath),surface_npz_path=str(surfacePath),assembly_geometry_path=str(geometry),atlas_path=str(atlasPath),payload_version='v8-expanded-E' if wide else 'B',
    region_labels=labels,region_counts={str(i):int((region[body]==i).sum()) for i in labels},meshfaceid_definition='Indexofpoly/triangle in joined-static.npz/nativejoinedbody; source_part1excludedhead.',
    allowed_regions=dict(bra=[1,2,3,4,5,12],briefs=[8,9,10,11,13],clavicle=[1,3,4,12]),
    uv_method=dict(method='ActualBlenderSmartUVprojection, bodyfacesonly; packedrealcornerUV atlas, no oldheadUV edits.',angle_limit_degrees=66,island_margin_requested=.004,seconds=time.time()-start,
        chart_layout='Packedactualislands, no hardcodedrectangles; fixed3Dmaskbake crossesverifiedchartseams. Nonoverlap/pixelconflicts must becheckedbybaker.'),
    collar_bounds=assembly['collars'],
    landmarks=dict(neck_donor_ring_center=[.000095,.004961,1.465],neck_guide_ring_center=[.000049,-.006494,1.445],clavicle_field_region='Actualneck/shoulder/fronttorso partlabels; sourcepixelmisses requiredeclaredanatomicalartistfit, notheightmask.',
                   hip_waist_join_z=[1.005,1.145] if wide else [1.035,1.115],body_center_x=0.,front_direction=[0,-1,0],up=[0,0,1]),
    source_context=sourceContext,source_registration_limit='Oldbaselinefourcameras/wholeheightSRT are referenceprojection context only, notacceptedseatedpaths. Newartistfit/residuals required.',
    retained_old_UV_layers_exact=True,head_faces_in_surface_payload=0,native_saved=False,GPU_used=False)
metaPath.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_SURFACE_ATLAS_READY',json.dumps({k:meta[k] for k in ['uv_layer','world_shape','triangles_shape','surface_npz_sha256','region_counts']}),flush=True)
