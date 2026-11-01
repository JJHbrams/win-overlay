"""Replay V28 D on e9 or e9 plus disjoint Body-prefix edits.
blender -b --python replay_patch.py -- INPUT.blend OUTPUT.blend
No canonical path is modified; output must be explicit.
"""
import bpy,numpy as np,json,sys,hashlib
from pathlib import Path
O=Path(__file__).parent;args=sys.argv[sys.argv.index('--')+1:];assert len(args) in [2,3],'INPUT OUTPUT [D or E] required';variant=args[2] if len(args)==3 else 'D';source=Path(args[0]);dest=Path(args[1]);assert source.resolve()!=dest.resolve(),'Source is immutable';bpy.ops.wm.open_mainfile(filepath=str(source));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];a=np.load(O/('v28'+variant+'-geometry-patch.npz'));names=[k.name for k in master.data.shape_keys.key_blocks];assert names==a['keys'].tolist();assert [k.name for k in skin.data.shape_keys.key_blocks]==names;assert len(skin.data.vertices)==4647;assert a['skin_indices'].min()>=3957
prefix=np.array([[v.co[:] for v in k.data[:3957]] for k in skin.data.shape_keys.key_blocks]);hair={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in bpy.data.objects if o.type=='MESH' and any(s in o.name for s in ['Hair','Braid','RootLining','Crown','Gather'])}
for ob,idx,delta in [(master,a['master_indices'],a['master_delta']),(skin,a['skin_indices'],a['skin_delta'])]:
 for ki,k in enumerate(ob.data.shape_keys.key_blocks):
  for j,d in zip(idx,delta[ki]):k.data[int(j)].co+=__import__('mathutils').Vector(d)
 for v,c in zip(ob.data.vertices,ob.data.shape_keys.key_blocks[0].data):v.co=c.co
features=np.load(O/('v28'+variant+'-features.npz'));metadata=json.loads((O/('v28'+variant+'-features.json')).read_text());rig=next(m.object for m in master.modifiers if m.type=='ARMATURE')
for rec in metadata:
 cs=features[rec['prefix']+'_coords'];faces=features[rec['prefix']+'_faces'];ob=bpy.data.objects.get(rec['name']);oldmat=ob.data.materials[0] if ob else bpy.data.materials[rec['material']];mesh=bpy.data.meshes.new(rec['name']+'_Replay');mesh.from_pydata(cs[0],[],faces);mesh.materials.append(oldmat)
 if ob:ob.data=mesh
 else:ob=bpy.data.objects.new(rec['name'],mesh);bpy.context.scene.collection.objects.link(ob)
 for ki,(name,c) in enumerate(zip(names,cs)):
  k=ob.shape_key_add(name=name,from_mix=False)
  for v,co in zip(k.data,c):v.co=co
  if ki:
   d=k.driver_add('value').driver;d.type='AVERAGE';v=d.variables.new();v.name='face_key';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks['+json.dumps(name)+'].value'
 g=ob.vertex_groups.get('J_Bip_C_Head') or ob.vertex_groups.new(name='J_Bip_C_Head');g.add(list(range(len(mesh.vertices))),1,'REPLACE');arm=next((m for m in ob.modifiers if m.type=='ARMATURE'),None) or ob.modifiers.new('V28_HeadFollow','ARMATURE');arm.object=rig;ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
mat=skin.data.materials[0].copy();mat.name='V28_Orbit_ActualUV_Replay';skin.data.materials[0]=mat;pixelpath=O/('v28'+variant+'-pigment-pixels.npz')
if pixelpath.exists():
 pp=np.load(pixelpath);W,H=pp['size'];image=bpy.data.images.new('V28_'+variant+'_ActualUV_Replay',width=int(W),height=int(H),alpha=True,float_buffer=True);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(pp['pixels']);image.pack()
else:image=bpy.data.images.load(str(O/'V28_ActualUV_OrbitPigment_2048_D.exr'),check_existing=False);image.colorspace_settings.name='Non-Color';image.pack()
mat.node_tree.nodes['V27_ACTUAL_UV_PIGMENT'].image=image
assert np.array_equal(prefix,np.array([[v.co[:] for v in k.data[:3957]] for k in skin.data.shape_keys.key_blocks]))
assert all(np.array_equal(p,np.array([v.co[:] for v in bpy.data.objects[n].data.vertices])) for n,p in hair.items())
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(dest));print('V28_REPLAY_SAVED',str(dest));print('BODY_PREFIX_ALL42_KEYS_EXACT; HAIR_EXACT')
