"""Read-only exact v29-to-current Crown UV lineage and packed pigment export.

No source geometry/shading/normal map is replayed. Each target triangle is
matched by source-face ID AND exact raw vertex IDs before any texture sample.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;O=P/'v29-pigment';O.mkdir(exist_ok=True);W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-face-finish-v29/surface-C/native/Mia_FaceFinish_v29_C.blend';SHA='d7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;ma=m.materials[0];node=ma.node_tree.nodes['V22_GENERATED_UV_PIGMENT'];image=node.image;link=node.inputs['Vector'].links[0];uvnode=link.from_node;assert uvnode.type=='UVMAP';uvname=uvnode.uv_map;assert uvname in m.uv_layers
raw=np.array([v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data],int);lookup={int(r):i for i,r in enumerate(raw)};assert len(lookup)==len(raw)
target=np.load(P/'crown-strip-A/proxy-strip-result.npz');mapped=[];old_polys=[]
for source_id,vertices in zip(target['selected_raw_ids'],target['selected_vertices']):
 pi=lookup[int(source_id)];p=m.polygons[pi];assert set(p.vertices)==set(int(x) for x in vertices);uv={int(v):m.uv_layers[uvname].data[li].uv[:] for v,li in zip(p.vertices,p.loop_indices)};mapped.append([uv[int(v)] for v in vertices]);old_polys.append(pi)
assert len(mapped)==4999
path=O/'V29_ExistingGeneratedPigment.png';export='original packed bytes'
if image.packed_file:
 blob=bytes(image.packed_file.data);assert blob.startswith(b'\x89PNG\r\n\x1a\n');path.write_bytes(blob)
else:
 from PIL import Image
 pix=np.empty(image.size[0]*image.size[1]*4,np.float32);image.pixels.foreach_get(pix);pix=pix.reshape(image.size[1],image.size[0],4)[::-1];rgb=np.where(pix[:,:,:3]<=.0031308,pix[:,:,:3]*12.92,1.055*np.maximum(pix[:,:,:3],0)**(1/2.4)-.055);a=np.dstack([rgb,pix[:,:,3]]);Image.fromarray(np.uint8(np.clip(a*255+.5,0,255)),'RGBA').save(path);export='linear pixel buffer encoded sRGB, alpha unchanged'
np.savez_compressed(O/'exact-correspondence.npz',current_polygon_indices=target['selected_polygon_indices'],raw_source_ids=target['selected_raw_ids'],raw_vertices=target['selected_vertices'],old_polygon_indices=np.array(old_polys,np.int32),old_loop_uv=np.array(mapped,np.float32),new_loop_uv=target['loop_uv'])
report=dict(native=str(N),native_sha256=SHA,target_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',matched_real_triangles=len(mapped),matching='Source polygon ID plus exact raw vertex set; UV corners reordered by raw vertex identity',source_uv=uvname,source_image=image.name,source_image_size=list(image.size),source_image_colorspace=image.colorspace_settings.name,source_image_export=export,source_image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),correspondence_sha256=hashlib.sha256((O/'exact-correspondence.npz').read_bytes()).hexdigest(),source_texture_interpolation=node.interpolation,old_normal_maps_reused=False,old_geometry_reused=False,current_Main_modified=False,target_newUV_overlap_pairs=0,limits='Exact lineage proves texture-coordinate correspondence, not current artistic fit or old alpha coverage. Sample old image in the unique measured new atlas; keep current reliable guide paint and current actual geometric normals. Actual current-model pigment/production review required before selection.',native_saved=False)
(O/'extraction-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
