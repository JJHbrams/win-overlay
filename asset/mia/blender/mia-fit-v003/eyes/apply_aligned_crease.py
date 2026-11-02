"""Actual-lid registered vector pigment; preserves current face/body shader routes."""
from pathlib import Path
import bpy,json,numpy as np,hashlib
P=Path(__file__).resolve().parent
def apply():
 cfg=json.loads((P/'upper-crease-vector.json').read_text());o=bpy.data.objects['MIA_V27_SharedHeadBody'];u=o.data.uv_layers['UVMap'];ar=np.empty(len(u.data)*2,np.float32);u.data.foreach_get('uv',ar);assert hashlib.sha256(ar.tobytes()).hexdigest()==cfg['original_face_UV_sha256']
 made=[]
 for name in ['MIA_V27_SharedHeadBody','V28G_InnerLid_-1','V28G_InnerLid_1']:
  ob=bpy.data.objects[name];old=ob.material_slots[0].material;ma=old.copy();ma.name='Mia_v003_AlignedCrease_'+name;n=ma.node_tree.nodes;l=ma.node_tree.links
  for key in ['V29_FoldGain','V30_FoldGain']:n[key].outputs[0].default_value=0.
  def math(op,x,y=0.):
   a=n.new('ShaderNodeMath');a.operation=op;a.name='Mia.v003.Crease.'+op
   for i,v in enumerate([x,y]):
    if hasattr(v,'node'):l.new(v,a.inputs[i])
    else:a.inputs[i].default_value=float(v)
   return a.outputs[0]
  uv=n['V30_ActualFaceUV'].outputs[0];sep=n.new('ShaderNodeSeparateXYZ');sep.name='Mia.v003.Crease.UV';l.new(uv,sep.inputs[0]);signals=[]
  for row in cfg['creases']:
   alpha=0.
   for a,b in zip(row['points'][:-1],row['points'][1:]):
    x,y=a['uv'];dx=b['uv'][0]-x;dy=b['uv'][1]-y;length2=dx*dx+dy*dy
    px=math('SUBTRACT',sep.outputs['X'],x);py=math('SUBTRACT',sep.outputs['Y'],y)
    dot=math('ADD',math('MULTIPLY',px,dx),math('MULTIPLY',py,dy));t=math('MINIMUM',1.,math('MAXIMUM',0.,math('DIVIDE',dot,length2)))
    rx=math('SUBTRACT',px,math('MULTIPLY',t,dx));ry=math('SUBTRACT',py,math('MULTIPLY',t,dy));distance=math('SQRT',math('ADD',math('MULTIPLY',rx,rx),math('MULTIPLY',ry,ry)))
    taper=.6+.4*np.sin(np.pi*((a['t']+b['t'])/2-.10)/.83);width=(a['half_width_uv']+b['half_width_uv'])*.5*taper
    coverage=math('MAXIMUM',0.,math('SUBTRACT',1.,math('DIVIDE',distance,width)))
    alpha=math('MAXIMUM',alpha,coverage)
   opening=n['V30_FoldOpen_'+('L' if row['side']==1 else 'R')].outputs[0]
   signals.append(math('MULTIPLY',alpha,opening))
  mask=math('MAXIMUM',signals[0],signals[1]);mask=math('MULTIPLY',mask,.65)
  if 'V30_FaceRootFade' in n:root=n['V30_FaceRootFade'].outputs[0]
  else:
   a=n.new('ShaderNodeAttribute');a.attribute_name='V29_CosmeticRootFade';root=a.outputs['Fac']
  mask=math('MULTIPLY',mask,root)
  source=n['V30_DirectSourcePigment_NoCleanup'].outputs['Color'];targets=[lk.to_socket for lk in list(source.links)]
  mix=n.new('ShaderNodeMixRGB');mix.name='Mia.v003.AlignedCreasePigment';mix.blend_type='MULTIPLY';l.new(mask,mix.inputs[0]);l.new(source,mix.inputs[1]);mix.inputs[2].default_value=(.44,.30,.28,1.)
  for socket in targets:l.new(mix.outputs[0],socket)
  ma['Mia_v003_crease']='UV-registered vector pigment on actual upper-lid skin; oldmisregisteredfoldgainsoff. No bitmap blur/replace or globalUVwarp. Existingfatigue/nose/lip/bodyandactual light/specular branches kept.'
  ob.material_slots[0].material=ma;made.append(dict(owner=name,old_material=old.name,new_material=ma.name))
 return dict(materials=made,scope='Upper crease registration only;0.17mm half-width/gap1.3..1.8mm; source finesse requires actual review.',native_saved=False)
