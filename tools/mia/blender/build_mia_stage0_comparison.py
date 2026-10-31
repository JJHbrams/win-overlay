"""Stage-0 non-destructive evidence scene for Mia reference candidates."""
import argparse, hashlib, json, math, sys
from array import array
from pathlib import Path

import bpy
from mathutils import Vector, Matrix

CAMERA_LOG=[]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def argv(): return sys.argv[sys.argv.index('--')+1:]
def coll(name):
    c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c
def bounds(objs):
    pts=[o.matrix_world@Vector(c) for o in objs if o.type=='MESH' for c in o.bound_box]
    if not pts: raise RuntimeError('candidate has no mesh bounds')
    return Vector(tuple(min(getattr(p,a) for p in pts) for a in 'xyz')),Vector(tuple(max(getattr(p,a) for p in pts) for a in 'xyz'))
def fp(obj):
    if not obj or obj.type!='MESH': return None
    m=obj.data; h=hashlib.sha256(); a=array('f',[0])* (len(m.vertices)*3);m.vertices.foreach_get('co',a);h.update(a.tobytes())
    uv={}
    for l in m.uv_layers:
        q=array('f',[0])*(len(l.data)*2);l.data.foreach_get('uv',q);uv[l.name]=hashlib.sha256(q.tobytes()).hexdigest()
    keys={}
    if m.shape_keys:
        for k in m.shape_keys.key_blocks:
            q=array('f',[0])*(len(k.data)*3);k.data.foreach_get('co',q);keys[k.name]=hashlib.sha256(q.tobytes()).hexdigest()
    return {'vertex_coordinates':h.hexdigest(),'uv_coordinates':uv,'shape_key_coordinates':keys}
def make_world(scene):
    w=bpy.data.worlds.new('STAGE0_NEUTRAL_WORLD'); w.use_nodes=True; n=w.node_tree.nodes; bg=n.get('Background') or n.new('ShaderNodeBackground'); bg.inputs['Color'].default_value=(.12,.14,.17,1); bg.inputs['Strength'].default_value=.35; scene.world=w
    for loc,energy,size in [((2,-3,4),800,3),((-3,-2,2),450,2),((0,3,3),350,2)]:
        d=bpy.data.lights.new('STAGE0_LIGHT','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new('STAGE0_LIGHT',d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.58))-o.location).to_track_quat('-Z','Y').to_euler()
def camera(scene):
    d=bpy.data.cameras.new('STAGE0_CAMERA');o=bpy.data.objects.new('STAGE0_CAMERA',d);scene.collection.objects.link(o);scene.camera=o;d.type='ORTHO';return o
def aim(cam,target,yaw,scale,persp=False):
    r=scale*3; rad=math.radians(yaw);cam.location=target+Vector((r*math.sin(rad),-r*math.cos(rad),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP' if persp else 'ORTHO';cam.data.lens=55;cam.data.ortho_scale=scale
def append_native(path,c):
    with bpy.data.libraries.load(str(path),link=False) as (src,dst): dst.objects=list(src.objects)
    os=[o for o in dst.objects if o and o.type not in {'CAMERA','LIGHT'}]
    for o in os:c.objects.link(o)
    return os
def import_glb(path,c):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));os=[o for o in bpy.data.objects if o not in before]
    for o in os:
        for cc in list(o.users_collection):cc.objects.unlink(o)
        c.objects.link(o)
    return os
def render(scene,cam,out,label,target,scale,clay_material,clay_pass,view):
    aim(cam,target,view[1],scale,view[0]=='perspective');scene.camera=cam;bpy.context.view_layer.update();scene.view_layers[0].material_override=clay_material if clay_pass else None;scene.render.filepath=str(out/f'{label}_{view[0]}_{"clay" if clay_pass else "actual"}.png')
    dg=bpy.context.evaluated_depsgraph_get(); evaluated=cam.evaluated_get(dg)
    CAMERA_LOG.append({'file':Path(scene.render.filepath).name,'scene_camera':scene.camera.name,'matrix_world':[list(row) for row in cam.matrix_world],'evaluated_matrix_world':[list(row) for row in evaluated.matrix_world],'ortho_scale':cam.data.ortho_scale,'camera_type':cam.data.type,'constraints':len(cam.constraints),'animation_data':bool(cam.animation_data),'target':list(target)})
    if scene.camera != cam: raise RuntimeError('Stage0 active camera changed before render')
    bpy.ops.render.render(write_still=True);return Path(scene.render.filepath).name
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--pixal-single',required=True);p.add_argument('--pixal-mv',required=True);p.add_argument('--pixal-full',required=True);p.add_argument('--previous',required=True);p.add_argument('--latest',required=True);a=p.parse_args(argv());out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 sources=[('pixal_single',Path(a.pixal_single),'glb'),('pixal_mv',Path(a.pixal_mv),'glb'),('pixal_full',Path(a.pixal_full),'glb'),('previous0240',Path(a.previous),'blend'),('latest0416',Path(a.latest),'blend')]
 before={n:sha(x) for n,x,_ in sources}
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='MIA_STAGE0_NATIVE_COMPARISON';scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';make_world(scene);cam=camera(scene)
 clay=bpy.data.materials.new('STAGE0_NEUTRAL_CLAY');clay.diffuse_color=(.52,.55,.58,1)
 records=[];collections=[]
 for name,path,kind in sources:
  c=coll('CANDIDATE_'+name.upper());collections.append(c);os=import_glb(path,c) if kind=='glb' else append_native(path,c);lo,hi=bounds(os);span=hi-lo;scale_factor=1.0
  if kind=='glb':
   target_height=1.7 if name=='pixal_full' else .45; scale_factor=target_height/max(span.z,1e-6)
   for o in os:o.scale*=scale_factor
   bpy.context.view_layer.update();lo,hi=bounds(os)
   if name=='pixal_full':
    for o in os:o.location.z-=lo.z
    bpy.context.view_layer.update();lo,hi=bounds(os)
  face=next((o for o in os if o.name.startswith('Mia_Face_AnimeTopology')),None);body=next((o for o in os if o.name.startswith('Mia_Body_Anatomy_Skin')),None)
  if face:
   hlo,hhi=bounds([face]);head_bounds={'min':list(hlo),'max':list(hhi),'basis':'native Mia_Face_AnimeTopology bounds'}
  elif name=='pixal_full':
   hlo=Vector((lo.x,lo.y,lo.z+(hi.z-lo.z)*.70));hhi=hi.copy();head_bounds={'min':list(hlo),'max':list(hhi),'basis':'top 30% bbox proxy; no face landmark established'}
  else:
   hlo=Vector((lo.x,lo.y,lo.z+(hi.z-lo.z)*.45));hhi=hi.copy();head_bounds={'min':list(hlo),'max':list(hhi),'basis':'top 55% bbox proxy; no face landmark established'}
  root=bpy.data.objects.new('PREVIEW_ROOT_'+name,None);c.objects.link(root);preview_scale=.45/max(hhi.z-hlo.z,1e-6);root.scale=(preview_scale,preview_scale,preview_scale);root.location=Vector((0,0,1.58))-(hlo+hhi)*.5*preview_scale
  # Preserve armature/bone child relationships: only hierarchy roots receive preview normalization.
  for o in [item for item in os if item.parent is None]:
   o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
  bpy.context.view_layer.update();nlo,nhi=bounds(os);nhlo,nhhi=bounds([face]) if face else (root.matrix_world@hlo,root.matrix_world@hhi)
  records.append({'id':name,'path':str(path),'sha256_before':before[name],'kind':kind,'glb_import_uniform_scale':scale_factor,'preview_root_uniform_scale':preview_scale,'preview_root_location':list(root.location),'normalization':'preview root maps bbox head proxy to 0.45m and center (0,0,1.58); source object data/transforms are not saved','bounds_after':{'min':list(nlo),'max':list(nhi)},'head_bounds':{'min':list(nhlo),'max':list(nhhi),'basis':head_bounds['basis']},'native_fingerprints':{'face':fp(face),'body':fp(body)}})
  c.hide_render=True;c.hide_viewport=True
 views=[('front',0),('side',90),('back',180),('three_quarter_right',45),('three_quarter_left',315),('perspective',45)]
 for record,c in zip(records,collections):
  c.hide_render=False;c.hide_viewport=False;lo=Vector(record['head_bounds']['min']);hi=Vector(record['head_bounds']['max']);target=Vector((0,0,1.58));headscale=.55; files=[]
  for v in views:
   for isclay in (False,True):files.append(render(scene,cam,out,record['id'],target,headscale,clay,isclay,v))
  record['head_evidence']=files
  if record['id']=='pixal_full':
   lo=Vector(record['bounds_after']['min']);hi=Vector(record['bounds_after']['max']);target=(lo+hi)/2;fullscale=max(hi.z-lo.z,.6);full=[]
   for v in views[:-1]:
    for isclay in (False,True):full.append(render(scene,cam,out,'pixal_full_full',target,fullscale,clay,isclay,v))
   record['fullbody_evidence']=full
  c.hide_render=True;c.hide_viewport=True
 after={n:sha(x) for n,x,_ in sources}
 if before!=after:raise RuntimeError('source bytes changed during Stage0')
 report={'status':'UNVERIFIED — visual selection and Stage1 are not authorized by this comparison','sources_unchanged':True,'camera_note':'GLB forward axis intentionally not corrected: yaw probe renders must establish orientation before any comparison decision. Native source cameras/lights are excluded; native shader/material differences are preserved in actual pass; clay is a scene override only.','views':['front','side','back','three_quarter_right','three_quarter_left','perspective'],'records':records,'render_camera_manifest':CAMERA_LOG}
 (out/'source-inventory.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'mia-stage0-native-comparison.blend'))
if __name__=='__main__':main()
