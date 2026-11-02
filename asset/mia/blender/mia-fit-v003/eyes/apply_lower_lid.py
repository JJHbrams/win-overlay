"""Add a sparse lower-rim corrective to the current scene, no native replay."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent
def arr(c):
 a=np.empty(len(c)*3,np.float32);c.foreach_get('co',a);return a.reshape(-1,3)
def apply():
 meta=json.loads((P/'lower-lid-balance.json').read_text());file=P/'lower-lid-balance.npz';assert hashlib.sha256(file.read_bytes()).hexdigest()==meta['payload_sha256'];data=np.load(file)
 master=bpy.data.objects['MIA_V27_Foundation_Face'].data.shape_keys;created=[]
 for row in meta['entries']:
  o=bpy.data.objects[row['owner']];assert len(o.data.vertices)==row['vertex_count'];assert row['key'] not in o.data.shape_keys.key_blocks,'Apply once'
  ids=data[row['prefix']+'_ids']
  for name,digest in row['original_key_ROI_hashes'].items():assert hashlib.sha256(arr(o.data.shape_keys.key_blocks[name].data)[ids].tobytes()).hexdigest()==digest,('Changed prerequisite eye ROI',o.name,name)
  q=arr(o.data.shape_keys.key_blocks[0].data);q[ids]+=data[row['prefix']+'_delta'];k=o.shape_key_add(name=row['key'],from_mix=False);k.data.foreach_set('co',q.ravel());k.value=0.;k.slider_min=0.;k.slider_max=1.
  d=k.driver_add('value').driver;d.type='SCRIPTED'
  for var,suffix in [('c','EYE_Close'),('j','EYE_Joy'),('l','EYE_Close_L'),('q','EYE_Joy_L'),('s','EYE_Surprised'),('a','EYE_Angry')]:
   v=d.variables.new();v.name=var;v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master;v.targets[0].data_path='key_blocks["Face.M_F00_000_00_Fcl_'+suffix+'"].value'
  d.expression='(1-min(1,max(0,c,j,l,q)))*(1-0.5*min(1,max(0,s)))*(1-0.8*min(1,max(0,a)))'
  created.append(dict(owner=o.name,key=k.name,vertices=len(ids),maximum_delta_mm=row['maximum_delta_mm']))
 bpy.context.view_layer.update()
 return dict(created=created,screen='right',side=1,method=meta['method'],native_replay=False,native_saved=False,scope='Subtle lower-rim curvature; no eyeball scaling, original key-array edits, upper-lid/canthus/whole-face redesign.')
