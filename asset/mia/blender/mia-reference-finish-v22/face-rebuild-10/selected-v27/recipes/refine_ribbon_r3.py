import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;OUT=O/'face-final-r3';OUT.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(O/'face-final-r2/Mia_Foundation_v27.blend'));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_ContinuousSkin'];ks=master.data.shape_keys.key_blocks;ribs=[o for o in bpy.context.scene.objects if o.name.startswith('V27_') and 'Ribbon' in o.name and not o.hide_render];pairs=[]
for old in ribs:
 rows=len(old.data.vertices)//2;allcoords=[]
 for key in old.data.shape_keys.key_blocks:
  stations=[]
  for i in range(rows-1):
   stations.append((key.data[2*i].co.copy(),key.data[2*i+1].co.copy()));stations.append(((key.data[2*i].co+key.data[2*(i+1)].co)/2,(key.data[2*i+1].co+key.data[2*(i+1)+1].co)/2))
  stations.append((key.data[-2].co.copy(),key.data[-1].co.copy()));allcoords.append([a.lerp(b,t) for a,b in stations for t in [0,.25,.5,.75,1]])
 count=len(stations);faces=[(i*5+j,(i+1)*5+j,(i+1)*5+j+1,i*5+j+1) for i in range(count-1) for j in range(4)];me=bpy.data.meshes.new(old.data.name+'_DenseContact');me.from_pydata(allcoords[0],[],faces);me.materials.append(old.material_slots[0].material);ob=bpy.data.objects.new(old.name+'_Dense',me);bpy.context.scene.collection.objects.link(ob)
 for name,c in zip([k.name for k in ks],allcoords):
  key=ob.shape_key_add(name=name,from_mix=False)
  for v,co in zip(key.data,c):v.co=co
  key.value=0
  if name!='Basis':
   dr=key.driver_add('value').driver;dr.type='AVERAGE';var=dr.variables.new();var.name='face_key';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=master.data.shape_keys;var.targets[0].data_path='key_blocks['+json.dumps(name)+'].value'
 old.hide_render=True;old.hide_viewport=True;old.hide_set(True);pairs.append((old.name,ob))
records=[]
for ki,key in enumerate(ks):
 for k in ks:k.value=0
 if ki:key.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bv=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);maxd=0
 for old,ob in pairs:
  for v in ob.data.shape_keys.key_blocks[ki].data:
   q=v.co.copy();hit=bv.ray_cast(Vector((q.x,-.25,q.z)),Vector((0,1,0)))
   if hit[0] is not None:v.co.y=min(q.y,hit[0].y-.00022)
   maxd=max(maxd,(v.co-q).length)
  if ki==0:
   for v,c in zip(ob.data.vertices,ob.data.shape_keys.key_blocks[0].data):v.co=c.co
 ev.to_mesh_clear();records.append({'key':key.name,'max_reprojection_mm':maxd*1000})
for k in ks:k.value=0
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'));(OUT/'ribbon-density-audit.json').write_text(json.dumps({'width_samples':5,'length_sampling':'2x existing curve samples','front_surface_offset_mm':.22,'replacements':[(name,ob.name,len(ob.data.vertices)) for name,ob in pairs],'per_key':records,'limits':'Actual1000px neutral/half/full required; no global offset increase or width change.'},indent=2));print('DENSE_RIBBONS_SAVED')
