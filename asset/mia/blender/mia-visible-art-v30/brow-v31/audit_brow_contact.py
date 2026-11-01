"""Actual evaluated brow/skin endpoints and interpolations, not raw arrays."""
import bpy, sys, json, hashlib
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector

P=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:]
native=Path(args[0]).resolve(); out=Path(args[1]).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody']
keys=master.data.shape_keys.key_blocks
states=[('neutral',None,0.)]+[(k.name,k.name,1.) for k in keys[1:]]
states += [(tag+str(v),next(k.name for k in keys if k.name.endswith('_'+tag)),v) for tag in ['BRW_Angry','BRW_Sorrow','EYE_Close'] for v in [.25,.5,.75]]
rows=[]
for label,name,value in states:
 for k in keys:k.value=value if k.name==name else 0.
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dg);me=ev.to_mesh()
 bvh=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);ev.to_mesh_clear()
 values=[]
 for side in [-1,1]:
  ob=bpy.data.objects['V31_SourceBrow_'+str(side)];ev=ob.evaluated_get(dg);me=ev.to_mesh()
  pts=[ev.matrix_world@v.co for v in me.vertices]
  me.calc_loop_triangles()
  bary=[(i/8,j/8,1-(i+j)/8) for i in range(9) for j in range(9-i)]
  samples=pts+[sum((pts[i] for i in f.vertices),Vector())/len(f.vertices) for f in me.polygons]
  samples += [pts[t.vertices[0]]*w[0]+pts[t.vertices[1]]*w[1]+pts[t.vertices[2]]*w[2] for t in me.loop_triangles for w in bary]
  signed=[]
  for point in samples:
   hit,n,face,d=bvh.find_nearest(point);signed.append((point-hit).dot(n))
  values.append({'side':side,'sample_count':len(samples),'minimum_mm':min(signed)*1000,'maximum_mm':max(signed)*1000,'embedded_over_005mm':sum(v < -.00005 for v in signed),'floating_over_05mm':sum(v>.0005 for v in signed)})
  ev.to_mesh_clear()
 rows.append({'state':label,'control':name,'value':value,'owners':values})
for k in keys:k.value=0.
report={'native':str(native),'sha256':before,'native_unchanged':sha(native)==before,'method':'Actual evaluated skin BVH vs actual brow vertices, all polygon centres and45barycentric samples/evaluated triangle in every named endpoint and9quarter/mid expressions. Signed nearest distance, not ray-visibility proof.','states':rows,'limits':'Arbitrary expression combinations and source expression likeness remain unverified; actual visible pose renders also required.'}
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BROW_CONTACT',len(rows), min(q['minimum_mm'] for r in rows for q in r['owners']), max(q['maximum_mm'] for r in rows for q in r['owners']),sum(q['embedded_over_005mm'] for r in rows for q in r['owners']),flush=True)
