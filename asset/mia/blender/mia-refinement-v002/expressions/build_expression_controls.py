"""Portable source-panel blend controls over the existing facial master.

No mesh/material/UV/weight/key-array edit. Hypotheses remain subject to actual art review.
"""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native);output=Path(a.output)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(native)==a.sha256 and not output.exists()
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
# The actual key-array and base digests include every scene mesh, not just the face.
def geometry():
 import numpy as np
 result={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;b=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',b)
  keydata=[]
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    ar=np.empty(len(k.data)*3,dtype=np.float32);k.data.foreach_get('co',ar);keydata.append(ar.tobytes())
  result[o.name]=hashlib.sha256(b.tobytes()+b''.join(keydata)).hexdigest()
 return result
before=geometry()
master=bpy.data.objects['MIA_V27_Foundation_Face'];sk=master.data.shape_keys
assert not sk.animation_data or len(sk.animation_data.drivers)==0
assert 'Mia_FacialControls_v002' not in bpy.data.objects
ctrl=bpy.data.objects.new('Mia_FacialControls_v002',None);bpy.context.scene.collection.objects.link(ctrl)
ctrl.empty_display_type='PLAIN_AXES';ctrl.empty_display_size=.025;ctrl.location=(.20,-.12,1.55)
ctrl['Strength']=1.;ctrl.id_properties_ui('Strength').update(min=0.,max=1.,description='Blend source-panel presets; manual controls remain independent.')
rows=json.loads((P/'expression-intents.json').read_text(encoding='utf-8'))['panels']
for row in rows:
 prop=f"P{row['panel']:02}_{row['id']}";ctrl[prop]=0.
 ctrl.id_properties_ui(prop).update(min=0.,max=1.,description=row['label']+' — source-panel hypothesis; actual review required.')
 row['control_property']=prop
ctrl['PresetTotal']=0.
fc=ctrl.driver_add('["PresetTotal"]');d=fc.driver;d.type='SUM'
for row in rows:
 v=d.variables.new();v.name='p'+str(row['panel']);v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+row['control_property']+'"]'
driver_specs=[]
for key in list(sk.key_blocks)[1:]:
 suffix=key.name.split('_Fcl_')[-1] if '_Fcl_' in key.name else 'EyeExtra_On'
 manual='Manual_'+suffix;ctrl[manual]=float(key.value)
 ctrl.id_properties_ui(manual).update(min=0.,max=1.,description='Direct original facial channel: '+key.name)
 f=key.driver_add('value');d=f.driver;d.type='SCRIPTED'
 def var(name,path):
  v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path='["'+path+'"]'
 var('m',manual);var('s','Strength');var('t','PresetTotal');terms=[]
 for row in rows:
  amount=row['initial_key_recipe'].get(suffix,0.)
  if amount:
   name='p'+str(row['panel']);var(name,row['control_property']);terms.append(f'{amount:g}*{name}')
 d.expression='min(1,max(0,m+s*('+('+'.join(terms) or '0')+')/max(1,t)))'
 driver_specs.append(dict(key=key.name,manual=manual,expression=d.expression))
ctrl['README']='P01..P16 blend source expressions; total above1 normalized. Manual_* offsets retain original channels. Head/gaze/hand pose are separate. ART UNVERIFIED.'
ctrl['SourceManifest']='asset/mia/blender/mia-refinement-v002/expressions/expression-intents.json'
bpy.context.view_layer.update()
assert all(abs(k.value)<1e-7 for k in list(sk.key_blocks)[1:])
assert geometry()==before
output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(output))
record=dict(input_native=str(native),input_sha256=a.sha256,native=str(output),native_sha256=sha(output),
    geometry_unchanged=True,original_key_arrays_unchanged=True,controller=ctrl.name,
    master=master.name,presets=rows,driver_specs=driver_specs,art_approved=False,
    pose_limits='Head/gaze/hand gestures are not encoded as face distortion; no final motion/action/physics is added.')
output.with_suffix('.controls.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(native)==a.sha256
print('EXPRESSION_CONTROLS_BUILT',sha(output),flush=True)
