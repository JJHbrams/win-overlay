import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;V=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'E';bpy.ops.wm.open_mainfile(filepath=str(O/('Mia_EyeLash_v29_'+V+'.blend')));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;rows=[]
for value in [0,.5,1]:
 for k in keys:k.value=value if k.name.endswith('Fcl_EYE_Close') else 0
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();se=skin.evaluated_get(dg);sm=se.to_mesh();bv=BVHTree.FromPolygons([se.matrix_world@v.co for v in sm.vertices],[list(f.vertices) for f in sm.polygons]);r={'bilateral_Close':value,'owners':{}}
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or not ob.name.startswith('V29_') or 'Lashes_' not in ob.name:continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh();nt=4 if 'Upper' in ob.name else 3;dist=[];signed=[]
  for i in [ti*42+c for ti in range(nt) for c in range(6)]:
   q=ev.matrix_world@me.vertices[i].co;hit,n,idx,d=bv.find_nearest(q);dist.append(d);signed.append((q-hit).dot(n))
  r['owners'][ob.name]={'actual_nearest_root_surface_distance_mm':[min(dist)*1000,max(dist)*1000],'signed_nearest_normal_distance_mm':[min(signed)*1000,max(signed)*1000]};ev.to_mesh_clear()
 se.to_mesh_clear();rows.append(r)
(O/('lash-'+V+'-nearest-root-probe.json')).write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
