"""Read-only scope, face UV loop geometry, and rest mask samples."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).parent;S=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');expected='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(S)==expected;bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False)
ids=set()
def walk(lc,hidden=False):
 hidden=hidden or lc.exclude or lc.collection.hide_render
 if not hidden:ids.update(o.as_pointer() for o in lc.collection.objects)
 for c in lc.children:walk(c,hidden)
walk(bpy.context.view_layer.layer_collection);objects=[];actualmaterials={}
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render or o.as_pointer() not in ids:continue
 slots=[]
 for i,s in enumerate(o.material_slots):
  count=sum(p.material_index==i for p in o.data.polygons)
  if count and s.material:slots.append({'slot':i,'material':s.material.name,'polygon_count':count});actualmaterials.setdefault(s.material.name,[]).append({'owner':o.name,'slot':i,'polygons':count})
 objects.append({'name':o.name,'vertices':len(o.data.vertices),'materials_with_polygons':slots,'modifiers':[{'name':m.name,'type':m.type,'show_render':m.show_render,'node_group':m.node_group.name if m.type=='NODES' and m.node_group else None} for m in o.modifiers]})
o=bpy.data.objects['MIA_V27_SharedHeadBody'];m=o.data;xyz=np.array([list(o.matrix_world@v.co) for v in m.shape_keys.key_blocks[0].data]);mask=np.array([v.value for v in m.attributes['V27_HeadMaterialBlend'].data]);uv=m.uv_layers['UVMap'];loops=np.array([list(v.uv) for v in uv.data]);tri=[];facepoly=[]
for p in m.polygons:
 if p.material_index==0:
  facepoly.append(p.index);ll=list(p.loop_indices)
  for j in range(1,len(ll)-1):tri.append([ll[0],ll[j],ll[j+1]])
np.savez_compressed(P/'actual-face-uv-and-mask.npz',uv_corners=loops,face_loop_triangles=np.array(tri),face_polygon_indices=np.array(facepoly),basis_world=xyz,mask=mask,loop_vertex_indices=np.array([v.vertex_index for v in m.loops]))
b=mask[:3957];nz=np.flatnonzero(b>0);mid=np.flatnonzero((b>0)&(b<1));head=np.flatnonzero(b==1)
regions={}
for name,index in [('body_nonzero',nz),('body_transition',mid),('body_full_head',head)]:
 regions[name]={'count':len(index),'index_minmax':[int(index.min()),int(index.max())] if len(index) else None,'basis_world_bbox':[xyz[index].min(0).tolist(),xyz[index].max(0).tolist()] if len(index) else None,'unique_mask_values':np.unique(mask[index]).tolist() if len(index)<100 else None}
report={'native_sha256':expected,'render_scope':'Collection/view-layer exclusions +collection.hide_render +object.hide_render, not mere material datablock existence. Geometry-node-generated materials remain separately represented by modifier names.','render_visible_meshes':objects,'materials_actually_assigned_to_render_visible_polygons':actualmaterials,'head_neck_attribute':{'name':'V27_HeadMaterialBlend','domain':'POINT','type':'FLOAT','meaning':'Static stored point attribute used as MixShader Fac on head-neck material slots9/10. No current shader world-Z computation. Attribute follows skinned vertices rather than a world-space height cutoff. Historical rest-weight derivation requires provenance; not inferred from filename.','regions':regions},'read_only':True,'baseline_sha256_after':sha(S)};assert report['baseline_sha256_after']==expected
(P/'actual-visible-surface-scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('VISIBLE_SURFACE_SCOPE',len(objects),len(actualmaterials),regions,flush=True)
