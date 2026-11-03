"""Fresh CPU reopen proof of the ONE shared-geometry two-state review native."""
from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import build_review_native as builder,review_fixture as fixture
cfg=builder.read_config();native=Path(bpy.data.filepath);saved=json.loads((P/'native/native-save.json').read_text());assert fixture.sha(native)==saved['sha256'];assert bpy.context.scene.name=='Underwear'
geometry=np.load(P/cfg['geometry']);surface=np.load(P/cfg['surface']);atlas=np.load(P/cfg['atlas']);api=builder.appearance_api(cfg);scenes={name:bpy.data.scenes[name] for name in ['SkinOnly','Underwear']};bodies={name:next(o for o in scene.objects if o.get('MIA12_static_review_body')) for name,scene in scenes.items()}
assert bodies['SkinOnly']!=bodies['Underwear'] and bodies['SkinOnly'].data==bodies['Underwear'].data
mesh=bodies['Underwear'].data;world=np.asarray([x.co[:] for x in mesh.vertices],np.float32);triangles=np.asarray([p.vertices[:] for p in mesh.polygons],np.int32);assert np.array_equal(world,geometry['world']) and np.array_equal(triangles,geometry['triangles'])
for body in bodies.values():assert not body.modifiers and not body.vertex_groups and not mesh.shape_keys and body.parent is None and np.array_equal(np.array(body.matrix_world),np.eye(4))
head=geometry['source_part']==1;uvs={}
for i,name in enumerate(['UVMap','MIA_BODY_V23_UV','MIA_V002_UnderwearUV']):
    uv=np.asarray([u.uv[:] for u in mesh.uv_layers[name].data],np.float32).reshape(-1,3,2);assert np.array_equal(uv[head],geometry['old_loop_uv'][head,:,i,:]);uvs[name]=hashlib.sha256(uv[head].tobytes()).hexdigest()
review=np.asarray([u.uv[:] for u in mesh.uv_layers['MIA_Review12UV'].data],np.float32).reshape(-1,3,2);assert np.array_equal(review,atlas['loop_uv']) and np.array_equal(review[surface['meshfaceid']],surface['loop_uv'])
bu=review[surface['meshfaceid']].astype(float);a,b=bu[:,1]-bu[:,0],bu[:,2]-bu[:,0];areas=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]);assert (areas>0).all()
assert mesh.uv_layers.active.name=='UVMap' and mesh.uv_layers['UVMap'].active_render
source=bpy.data.objects['MIA_V27_SharedHeadBody'];material_index=np.asarray([p.material_index for p in mesh.polygons]);assert np.array_equal(material_index[head],geometry['triangle_materials'][head]) and np.all(material_index[~head]==12)
mats={};packed={}
for state,ob in bodies.items():
    assert ob.material_slots[12].link=='OBJECT';mat=ob.material_slots[12].material;expected='skin' if state=='SkinOnly' else 'underwear';assert mat['mia12_variant']==expected
    for i in range(12):assert ob.material_slots[i].link=='DATA' and ob.material_slots[i].material==source.data.materials[i]
    mats[state]=api.audit_material(mat);assert mats[state]['UV_layer']=='MIA_Review12UV'
    assert len(mats[state]['images'])==5 and all(x['packed'] and x['packed_sha256']==x['expected_file_sha256'] and x['filepath'].startswith('//') for x in mats[state]['images']);packed[state]=mats[state]['images']
    for layer in scenes[state].view_layers:assert source.hide_get(view_layer=layer)
    camera=scenes[state].camera.data;assert camera.type=='ORTHO' and abs(camera.clip_start-.1)<1e-7 and camera.clip_end==10
assert bodies['SkinOnly'].material_slots[12].material.node_tree!=bodies['Underwear'].material_slots[12].material.node_tree
ad=np.load(P/'head-attributes.npz');am=json.loads((P/'head-attributes.json').read_text());sv=geometry['source_vertex'];protected=(sv>=0)&(world[:,2]>=1.469)
for rec in am['attributes']:
    actual=np.empty((len(world),rec['dimension']),np.float32);mesh.attributes[rec['name']].data.foreach_get(rec['property'],actual.ravel());assert np.array_equal(actual[protected],ad[rec['npz_key']][sv[protected]])
normal=np.asarray([x.vector[:] for x in mesh.corner_normals],np.float32).reshape(-1,3,3)[head].astype(float);expected=geometry['source_corner_normals'][head].astype(float);expected/=np.linalg.norm(expected,axis=2)[:,:,None];ang=np.degrees(np.arctan2(np.linalg.norm(np.cross(normal,expected),axis=2),(normal*expected).sum(2)));uncut=np.all(geometry['source_corner_bary'][head]==np.eye(3,dtype=np.float32)[None,:,:],axis=(1,2));assert ang[uncut].max()<.05
report=dict(status='Fresh saved-native CPU reopen PASS; actual appearance/source ART remains separate',native=dict(path=str(native),sha256=fixture.sha(native),bytes=native.stat().st_size),scenes=['SkinOnly','Underwear'],default_scene=bpy.context.scene.name,shared_mesh=mesh.name,world_sha256=hashlib.sha256(world.tobytes()).hexdigest(),triangles_sha256=hashlib.sha256(triangles.tobytes()).hexdigest(),ReviewUV_body_sha256=hashlib.sha256(review[surface['meshfaceid']].tobytes()).hexdigest(),minimum_body_UV_double_area=float(areas.min()),head_old3_UV_sha256=uvs,original_active_render_UV='UVMap',head_slots_and_POINT_attribute_exact=True,uncut_head_normal_max_degrees=float(ang[uncut].max()),clipped_neck_normal_max_degrees=float(ang[~uncut].max()),body_materials=mats,packed_images=packed,static_no_weights_keys_modifiers=True,native_saved=False,GPU_used=False)
(P/'native/reopen-proof.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');assert fixture.sha(native)==saved['sha256'];print('REVIEW12_NATIVE_REOPEN_PASS',saved['sha256'],flush=True)
