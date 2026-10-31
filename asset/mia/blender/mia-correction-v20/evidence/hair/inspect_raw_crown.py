import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3];stage=ROOT/'asset/mia/blender/mia-production-stage1/v11/Mia_Stage1_DesignReview.blend'
bpy.ops.wm.open_mainfile(filepath=str(stage));src=next(o for o in bpy.data.collections['SOURCE_SINGLE_RAW'].objects if o.type=='MESH');src.hide_viewport=False;src.hide_set(False);bpy.context.view_layer.update();vs=[];tr=Matrix.Translation((0,.025,1.556))@Matrix.Scale(.88,4)@Matrix.Translation((0,0,-1.516))
for v in src.data.vertices:
 q=tr@(src.matrix_world@v.co);q=Vector(((q.x+.0004777)*.82-.000394,(q.y+.0861166)*.82-.07108,1.559+(q.z-1.565739)*.82));vs.append(Vector((q.x*.90,(q.y+.07)*.90-.07,1.540+(q.z-1.550)*.90)))
bv=BVHTree.FromPolygons(vs,[list(p.vertices) for p in src.data.polygons]);hits=[]
for y,z in [(.060,1.628),(.060,1.634),(.063,1.628)]:
 hit,n,idx,d=bv.ray_cast(Vector((2,y,z)),Vector((-1,0,0)));hits.append({'y':y,'z':z,'hit':list(hit) if hit else None,'sourcepoly':idx})
uv=src.data.uv_layers.active;polys=[]
for p in src.data.polygons:
 q=sum((vs[i] for i in p.vertices),Vector())/len(p.vertices)
 if .035<q.x<.11 and .042<q.y<.085 and 1.610<q.z<1.652:polys.append({'sourcepoly':p.index,'vs':[list(vs[i]) for i in p.vertices],'uv':[list(uv.data[i].uv) for i in p.loop_indices]})
img=next(n.image for n in src.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image);import hashlib
r={'raw_ray_hits':hits,'region_faces':polys,'image_name':img.name,'image_packed_sha':hashlib.sha256(bytes(img.packed_file.data)).hexdigest() if img.packed_file else None};(OUT/'raw-crown-inspection.json').write_text(json.dumps(r));print('RAW_RAYS',hits,'PATCH_POLYS',len(polys),r['image_name'])
