"""Install source-panel expression, head and bounded surface-projected gaze controls.

No file open/save. Existing eye bones are deliberately not reused: their pivots do
not match the rebuilt eyes. Gaze is a small toon iris motion on the actual sclera.
"""
from pathlib import Path
import json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent

def apply_to_current_scene():
 master=bpy.data.objects['MIA_V27_Foundation_Face'];sk=master.data.shape_keys
 assert not sk.animation_data or not sk.animation_data.drivers
 assert 'Mia_FacialControls_v002' not in bpy.data.objects
 rows=json.loads((P/'expression-intents.json').read_text(encoding='utf-8'))['panels']
 available={k.name.split('_Fcl_')[-1] for k in sk.key_blocks}
 assert not ({s for r in rows for s in r['initial_key_recipe']}-available), 'Install the chosen source mouth correction before expression presets'
 ctrl=bpy.data.objects.new('Mia_FacialControls_v002',None);bpy.context.scene.collection.objects.link(ctrl)
 ctrl.empty_display_type='PLAIN_AXES';ctrl.empty_display_size=.025;ctrl.location=(.20,-.12,1.55)
 def prop(name,value=0.,minimum=0.,maximum=1.,description=''):
  ctrl[name]=value;ctrl.id_properties_ui(name).update(min=minimum,max=maximum,description=description)
 prop('Strength',1.,description='Facial source-preset intensity; original Manual channels are independent.')
 prop('HeadPoseStrength',1.,description='Estimated local head pitch/yaw/roll; zero isolates facial deformation.')
 prop('GazeStrength',1.,description='Bounded iris-on-sclera motion, not a full eyeball/spring runtime.')
 for r in rows:
  r['control_property']=f"P{r['panel']:02}_{r['id']}";prop(r['control_property'],description=r['label'])
 prop('PresetTotal');d=ctrl.driver_add('["PresetTotal"]').driver;d.type='SUM'
 for r in rows:
  v=d.variables.new();v.name='p'+str(r['panel']);v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+r['control_property']+'"]'
 def bind(d,name,path,id=None,id_type=None):
  v=d.variables.new();v.name=name;v.type='SINGLE_PROP'
  if id_type:v.targets[0].id_type=id_type
  v.targets[0].id=ctrl if id is None else id;v.targets[0].data_path=path
 def compose(d,manual,amounts,strength,scale=1.,clamp=None):
  d.type='SCRIPTED';bind(d,'m','["'+manual+'"]');bind(d,'s','["'+strength+'"]');bind(d,'t','["PresetTotal"]');terms=[]
  for r,amount in zip(rows,amounts):
   if amount:
    name='p'+str(r['panel']);bind(d,name,'["'+r['control_property']+'"]');terms.append(f'{amount:g}*{name}')
  expr='m+s*('+('+'.join(terms) or '0')+')/max(1,t)'
  if clamp:expr=f'min({clamp[1]:g},max({clamp[0]:g},'+expr+'))'
  d.expression=f'({expr})*{scale:.12g}' if scale!=1 else expr
 for k in list(sk.key_blocks)[1:]:
  suffix=k.name.split('_Fcl_')[-1] if '_Fcl_' in k.name else 'EyeExtra_On';manual='Manual_'+suffix
  prop(manual,float(k.value),description='Original facial channel '+k.name)
  compose(k.driver_add('value').driver,manual,[r['initial_key_recipe'].get(suffix,0.) for r in rows],'Strength',clamp=(0,1))
 rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');head=rig.pose.bones['J_Bip_C_Head'];before=head.matrix.copy()
 assert not rig.animation_data or not any('J_Bip_C_Head' in d.data_path for d in rig.animation_data.drivers), 'Existing head drivers need explicit composition'
 assert all(abs(head.matrix_basis[i][j]-(1. if i==j else 0.))<1e-6 for i in range(4) for j in range(4)), 'Nonneutral head needs explicit base-pose composition'
 head.rotation_mode='XYZ'
 for axis,name in enumerate(['HeadPitch','HeadYaw','HeadRoll']):
  prop(name,0.,-25.,25.,'Degrees on the verified rebuilt head local axis; preset angles remain estimates.')
  compose(head.driver_add('rotation_euler',axis).driver,name,[r['estimated_head_delta_xyz_deg'][axis] for r in rows],'HeadPoseStrength',scale=math.pi/180)
 for axis,name in enumerate(['GazeX','GazeY']):
  prop(name,0.,-1.,1.,'Positive world-X / upward head-space tangent motion; bounded at1.8/1.2mm.')
  prop('_Effective'+name,0.,-1.,1.)
  compose(ctrl.driver_add('["_Effective'+name+'"]').driver,name,[r['estimated_gaze_xy_deg'][axis]/(8. if axis==0 else 5.) for r in rows],'GazeStrength',clamp=(-1,1))
 gaze_report=[]
 for sign in [-1,1]:
  iris=bpy.data.objects['V28G_Iris_'+str(sign)];sclera=bpy.data.objects['V28G_Sclera_'+str(sign)]
  sb=sclera.data.shape_keys.key_blocks[0];sv=[sclera.matrix_world@v.co for v in sb.data]
  tree=BVHTree.FromPolygons(sv,[tuple(f.vertices) for f in sclera.data.polygons])
  raw=[iris.matrix_world@v.co for v in iris.data.shape_keys.key_blocks[0].data];inv=iris.matrix_world.inverted()
  def front(x,z):
   hit=tree.ray_cast(Vector((x,-.25,z)),Vector((0,1,0)),.5)
   return hit[0].y if hit[0] is not None else None
  base_front=[front(v.x,v.z) for v in raw]
  for name,dx,dz,channel,polarity in [('Right',.0018,0,'X',1),('Left',-.0018,0,'X',-1),('Up',0,.0012,'Y',1),('Down',0,-.0012,'Y',-1)]:
   key=iris.shape_key_add(name='Mia.Gaze.'+name,from_mix=False);key.value=0.;misses=0;max_depth=0.
   for i,v in enumerate(raw):
    new=v+Vector((dx,0,dz));ny=front(new.x,new.z)
    if ny is None or base_front[i] is None:misses+=1
    else:new.y=ny+(v.y-base_front[i]);max_depth=max(max_depth,abs(new.y-v.y))
    key.data[i].co=inv@new
   assert misses<max(4,int(len(raw)*.02)),('Gaze outside actual sclera',sign,name,misses)
   d=key.driver_add('value').driver;d.type='SCRIPTED';bind(d,'g','["_EffectiveGaze'+channel+'"]')
   for vn,suffix in [('c','EYE_Close'),('j','EYE_Joy'),('s','EYE_Close_L' if sign==1 else 'EYE_Close_R'),('q','EYE_Joy_L' if sign==1 else 'EYE_Joy_R')]:
    bind(d,vn,'key_blocks["Face.M_F00_000_00_Fcl_'+suffix+'"].value',sk,'KEY')
   d.expression=f'max(0,{polarity}*g)*(1-min(1,max(c,j,s,q)))'
   gaze_report.append(dict(owner=iris.name,key=key.name,dx_m=dx,dz_m=dz,uncovered_vertices=misses,max_depth_adjustment_m=max_depth))
 ctrl['README']='P01..P16 blend source impressions. Manual_* channels remain editable. Head/gaze presets are estimated and require actual per-panel review; hand gesture07 is separate. No final action or physics is added.'
 ctrl.update_tag();bpy.context.scene.frame_set(bpy.context.scene.frame_current);bpy.context.view_layer.update()
 assert max(abs(head.matrix[i][j]-before[i][j]) for i in range(4) for j in range(4))<1e-6
 return dict(controller=ctrl.name,master=master.name,rig=rig.name,gaze=gaze_report,default_head_unchanged=True,
  scope='Source expressions with local head axes and small surface-projected iris motion. No old eye-bone pivot reuse, no full-globe claim, no final motion/physics.')

def set_source_pose(panel):
 c=bpy.data.objects['Mia_FacialControls_v002']
 for name in c.keys():
  if name.startswith('P') and name[:3][1:].isdigit():c[name]=1. if int(name[1:3])==panel else 0.
 c.update_tag();bpy.context.scene.frame_set(panel+1);bpy.context.view_layer.update()
