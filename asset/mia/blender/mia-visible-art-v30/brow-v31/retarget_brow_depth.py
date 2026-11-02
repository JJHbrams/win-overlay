"""Reseat only brow depth after the outer-orbit skin field; preserve source XZ."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-lash-v29')
from audit_mesh_helpers import snapshot
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
src,dest=Path(a.input).resolve(),Path(a.output).resolve();assert src!=dest and not dest.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();srcsha=sha(src)
bo,_,bm,bi=snapshot(src)
master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];names=[k.name for k in master.data.shape_keys.key_blocks]
owners=['V31_SourceBrow_-1','V31_SourceBrow_1'];old={n:np.array([[v.co[:] for v in k.data] for k in bpy.data.objects[n].data.shape_keys.key_blocks],dtype=np.float32) for n in owners};new={n:q.copy() for n,q in old.items()}
for ki,name in enumerate(names):
 for k in master.data.shape_keys.key_blocks:k.value=1. if k.name==name and ki else 0.
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 bvh=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);ev.to_mesh_clear()
 for n in owners:
  for vi,p in enumerate(old[n][ki]):
   hit,normal,face,d=bvh.ray_cast(Vector((float(p[0]),-1.,float(p[2]))),Vector((0,1,0)),2.)
   assert hit is not None and normal.y < -.15,(n,name,vi,'Skin front ray invalid')
   new[n][ki,vi,1]=hit.y+.00022/normal.y
for k in master.data.shape_keys.key_blocks:k.value=0.
for n in owners:
 ob=bpy.data.objects[n];ob.data.vertices.foreach_set('co',new[n][0].ravel())
 for k,q in zip(ob.data.shape_keys.key_blocks,new[n]):k.data.foreach_set('co',q.ravel())
 ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(dest));ao,_,am,ai=snapshot(dest)
checks={'all_nonbrow_input_mesh_records_exact':all(bo[n]==ao[n] for n in bo if n not in owners),'brows_only_coordinates_changed':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k!='coordinates') for n in owners),'all_source_XZ_bitexact':all(np.array_equal(old[n][:,:,[0,2]],new[n][:,:,[0,2]]) for n in owners),'all_input_material_graphs_exact':bm==am,'all_input_images_exact':bi==ai,'input_native_unchanged':sha(src)==srcsha}
assert all(checks.values()),checks
report={'input':str(src),'input_sha256':srcsha,'output':str(dest),'sha256':sha(dest),'checks':checks,'maximum_brow_Y_change_mm':max(float(abs(old[n]-new[n]).max())*1000 for n in owners),'scope':'Only2existing brow Y arrays/raw+all42; exact sourceXZ/UV/materials/morphnames/drivers/weights. Reseat on final actual outer-wrap skin; no face/body/eye edits.','pending':'Fresh evaluated contact and actual pose/source proof required.'}
dest.with_suffix('.brow-depth.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('BROW_RETARGET',report['sha256'],report['maximum_brow_Y_change_mm'],checks)
