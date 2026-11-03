"""Root-approved ONE small static shape guide. Factory empty, no R3b import."""
from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
import bpy,numpy as np
from mathutils import Matrix
P=Path(__file__).resolve().parent;N=P/'native';N.mkdir(exist_ok=True);target=N/'Mia_PosteriorUnion09_STATIC_ShapeGuide.blend';assert not target.exists(),'One static review file; do not overwrite'
data=np.load(P/'posterior09.npz');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();expected=sha(P/'posterior09.npz');assert expected=='d5bf574ea958923fc70fe6ade4de7e0b64ec970c3cf15156be5f135af3c9cdd2'
rows=json.loads((P/'actual8/render-records.json').read_text(encoding='utf-8'));extras=json.loads((P/'actual-extra3/render-records.json').read_text(encoding='utf-8'));held={str(f):sha(f) for folder in [P/'actual8',P/'actual-extra3'] for f in folder.rglob('*') if f.is_file()}
bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
mesh=bpy.data.meshes.new('PosteriorUnion09_STATIC_NoProductionUV');mesh.from_pydata(data['world'].tolist(),[],data['triangles'].tolist());mesh.update();body=bpy.data.objects.new('09_STATIC_UPPERBODY_SHAPE_GUIDE_ONLY',mesh);scene.collection.objects.link(body);body.matrix_world=Matrix.Identity(4)
for poly in mesh.polygons:poly.use_smooth=True
material=bpy.data.materials.new('09_StaticReview_PhysicalGray');material.use_nodes=True;nodes=material.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85;out=nodes.new('ShaderNodeOutputMaterial');material.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);mesh.materials.append(material)
world=bpy.data.worlds.new('09_StaticReview_GrayWorld');world.use_nodes=True;nodes=world.node_tree.nodes;nodes.clear();bg=nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.18,.18,.18,1);bg.inputs['Strength'].default_value=.2;out=nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);scene.world=world
for tree in [material.node_tree,world.node_tree]:
    for node in tree.nodes:node.name=node.bl_label
for i,spec in enumerate(r for r in rows[0]['actual_lights'] if not r['hidden']):
    light=bpy.data.lights.new('09_Review_Area_'+str(i),'AREA');light.energy=spec['energy'];light.size=spec['size'];light.shape='DISK';light.use_shadow=spec['use_shadow'];ob=bpy.data.objects.new(light.name,light);scene.collection.objects.link(ob);ob.matrix_world=Matrix(spec['matrix'])
cameras={}
for row in rows+extras:
    view=row['view']
    if view in cameras:continue
    spec=row['camera'];cam=bpy.data.cameras.new('09_ORTHO_'+view);cam.type='ORTHO';cam.ortho_scale=spec['ortho_scale'];cam.clip_start=.1;cam.clip_end=10;ob=bpy.data.objects.new(cam.name,cam);scene.collection.objects.link(ob);ob.matrix_world=Matrix(spec['matrix']);ob['review_resolution']=spec['resolution'];cameras[view]=ob
scene.camera=cameras['rear140'];scene.frame_set(1);scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.unit_settings.system='METRIC'
for key,value in rows[0]['color_management'].items():setattr(scene.view_settings,key,value)
scope='STATIC UPPERBODY SHAPE GUIDE ONLY. NO production UV, rig, weights, facial keys, head/lowerbody integration, animation or whole-body ART approval.'
scene['REVIEW_SCOPE']=body['REVIEW_SCOPE']=scope;body['source_NPZ_sha256']=expected;body['posterior_wall_constant_blend_m']=.014;body['actual_image_provenance']='Previous actual images were R3b private-context + this NPZ. They were NOT rendered from this standalone file.'
text=bpy.data.texts.new('00_STATIC_SCOPE_README');text.write(scope+'\n\n'+body['actual_image_provenance']+'\n\nCandidate raw/world coordinates and origin0 are unchanged from NPZ. Temporary design cap boundaries are not production seams.\n')
for ob in scene.objects:ob.select_set(False)
body.select_set(True);bpy.context.view_layer.objects.active=body
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_start=.1;space.clip_end=10;space.region_3d.view_location=(0,-.015,1.285);space.region_3d.view_distance=.70;space.region_3d.view_rotation=scene.camera.matrix_world.to_quaternion();space.region_3d.view_perspective='ORTHO'
for old in list(bpy.data.worlds):
    if old!=world and old.users==0:bpy.data.worlds.remove(old)
assert np.array_equal(np.asarray([v.co[:] for v in mesh.vertices],np.float32),data['world']) and len(bpy.data.objects)==1+3+len(cameras)
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True,check_existing=False)
assert target.stat().st_size<15_000_000 and sha(P/'posterior09.npz')==expected
for path,h in held.items():assert sha(path)==h
report=dict(path=str(target),sha256=sha(target),bytes=target.stat().st_size,mesh_NPZ_sha256=expected,scope=scope,objects=len(bpy.data.objects),meshes=1,cameras=len(cameras),lights=3,raw_vertices=len(mesh.vertices),triangles=len(mesh.polygons),matrix_world=[list(r) for r in body.matrix_world],native_source='Factory empty, one static NPZ only; no originalR3b data imported',actual_image_provenance=body['actual_image_provenance'],GPU_used=False)
(N/'export-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('POSTERIOR09_SMALL_STATIC_SAVED',json.dumps(report),flush=True)
