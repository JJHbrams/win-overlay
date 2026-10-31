"""One diagnosed root-lining shadow correction; no geometry repair claim."""
import bpy,sys,argparse,hashlib,json,struct
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);SRC=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC)
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;cam=scene.camera;owner='MIA_V17_RootLining_MIA_V06_BODY_SKIN';root=bpy.data.objects[owner]
def snapshot():
 r={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  data=b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<2f',*v.uv) for l in o.data.uv_layers for v in l.data)
  if o.data.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in o.data.shape_keys.key_blocks for v in k.data)
  r[o.name]=hashlib.sha256(data).hexdigest()
 return r
base=snapshot();slots={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.data.objects if o.type=='MESH' and o.name!=owner};packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
scene.render.resolution_x=scene.render.resolution_y=1000;cam.location=(2,0,1.46);cam.rotation_euler=(Vector((0,0,1.46))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.64
def render(prefix):
 scene.render.filepath=str(OUT/(prefix+'_profile.png'));bpy.ops.render.render(write_still=True)
render('before')
hair=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=hair.data;bv=BVHTree.FromPolygons([hair.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons]);diagnosis=[]
for y,z in [(.060,1.628),(.063,1.628),(.060,1.634),(.052,1.628),(.072,1.628),(.060,1.618)]:
 hit,n,idx,dist=bv.ray_cast(Vector((2,y,z)),Vector((-1,0,0)));r=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((2,y,z)),Vector((-1,0,0)));diagnosis.append({'y':y,'z':z,'hair_first_x':hit.x if hit else None,'scene_first_owner':r[4].name if r[0] else None,'scene_first_x':r[1].x if r[0] else None})
old=root.material_slots[0].material;mat=bpy.data.materials.new('MIA_V17G_RootLining_WarmHairShadow');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links;out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.3,-.65,.7);l.new(geo.outputs['Normal'],dot.inputs[0]);mr=n.new('ShaderNodeMapRange');mr.inputs['From Min'].default_value=-1;mr.inputs['From Max'].default_value=1;mr.inputs['To Min'].default_value=.62;mr.inputs['To Max'].default_value=1.;l.new(dot.outputs['Value'],mr.inputs['Value']);mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[1].default_value=(.15,.125,.122,1);l.new(mr.outputs[0],mul.inputs[2]);l.new(mul.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0]);root.material_slots[0].material=mat
for image in bpy.data.images:
 if image.packed_file:image.use_fake_user=True
native=OUT/'Mia_HairRootShadow_v17g.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera;assert snapshot()==base;assert all([s.material.name if s.material else None for s in bpy.data.objects[name].material_slots]==v for name,v in slots.items());assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};render('after');assert sha(SRC)==source_sha
r={'source_sha256':source_sha,'native_sha256':sha(native),'recipe_sha256':sha(Path(__file__)),'changed_owner':owner,'changed_material':'MIA_V17G_RootLining_WarmHairShadow','geometry_uv_key_meshes_exact':len(base),'other_material_owners_exact':len(slots),'packed_images_byte_exact':len(packed),'ray_evidence':diagnosis,'diagnosis':'Near-side source hair hole reveals root liner; not liner protrusion. Material shadow continuity only, no restored strands or geometry clipping fix.','shadow_linear_rgb':[.15,.125,.122]};(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE_SHA',r['native_sha256'])
