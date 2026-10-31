"""Saved-native geometry, hair context and clean registered albedo calibration."""
import bpy,sys,math,json,ast,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import review_setup as r
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sh=r.sha(SOURCE)
def load(hide=True):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1)
 if hide:r.hairhide()
 return s
def render(s,name,v):r.camera(s,v);s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def constant(name,color,diffuse=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfDiffuse' if diffuse else 'ShaderNodeEmission');bs.inputs[0].default_value=(*color,1);o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(bs.outputs[0],o.inputs[0]);return m
def rig(s):
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 for o in s.objects:
  if o.type=='LIGHT':o.hide_render=True
 w=bpy.data.worlds.new('V22_CommonReviewWorld');w.use_nodes=True;w.node_tree.nodes.clear();bg=w.node_tree.nodes.new('ShaderNodeBackground');wo=w.node_tree.nodes.new('ShaderNodeOutputWorld');w.node_tree.links.new(bg.outputs[0],wo.inputs[0]);bg.inputs[0].default_value=(.18,.18,.18,1);bg.inputs[1].default_value=.1;s.world=w
 for name,loc,power,size in [('Key',(-.6,-1,2.2),60,1),('Fill',(.8,-.8,1.8),15,1.5),('Rim',(0,.9,2.05),8,.8)]:
  d=bpy.data.lights.new('V22_'+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);r.aim(o,loc,(0,0,1.55))
s=load(False)
for v in r.VIEWS:render(s,'hair_'+v['id'],v)
s=load();rig(s);clay=constant('V22_DIAG_Clay',(.18,.18,.18),True)
for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
 for slot in bpy.data.objects[name].material_slots:slot.material=clay
for o in s.objects:
 if any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
views=[dict(id=label,yaw=yaw,elevation=0,roll=0) for label,yaw in [('front',0),('left45',45),('right45',-45),('profile90',90)]]
for v in views:render(s,'clay_'+v['id'],v)
s=load();rig(s);base=constant('V22_FLAT_BASE_LINEAR',(.92,.69,.60));skin=bpy.data.objects['MIA_V14_SculptedSkin']
for name in [skin.name,'MIA_V06_BODY_SKIN']:
 for slot in bpy.data.objects[name].material_slots:slot.material=base
render(s,'calibration_front_flat',views[0]);(OUT/'calibration.json').write_text(json.dumps({'source':r.artifact(SOURCE),'camera':r.record(s,views[0],'Emission flat base, lighting bypassed for paint calibration'),'base_linear':[.92,.69,.60],'base_srgb_hex':'F6D9CB approximately','landmarks':r.landmarks(s,views[0]),'not_a_final_model_look':True},indent=2))
s=load();key=next(k for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'));key.value=.5;bpy.context.view_layer.update();render(s,'blink_half',views[0]);assert r.sha(SOURCE)==sh;print('EVIDENCE_DONE')
