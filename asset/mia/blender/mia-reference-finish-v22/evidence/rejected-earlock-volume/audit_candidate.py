import bpy,json,hashlib,struct,numpy as np
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
O=Path(__file__).resolve().parent;M=json.loads((O/'manifest.json').read_text());S=Path(M['source']);D=Path(M['native']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p):sha(p) for p in [S,D]};name=M['changed_owner']
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));rows={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data;hh=hashlib.sha256()
  for v in m.vertices:
   hh.update(struct.pack('<3f',*v.co))
   for g in v.groups:hh.update(struct.pack('<If',g.group,g.weight))
  for p in m.polygons:hh.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));hh.update(struct.pack('<I?',p.material_index,p.use_smooth))
  for u in m.uv_layers:
   hh.update(u.name.encode())
   for x in u.data:hh.update(struct.pack('<2f',*x.uv))
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    hh.update(k.name.encode());hh.update(struct.pack('<f',k.value))
    for v in k.data:hh.update(struct.pack('<3f',*v.co))
  rows[o.name]={'data':hh.hexdigest(),'matrix':list(map(list,o.matrix_world)),'visibility':[o.hide_render,o.hide_viewport],'materials':[m.name if m else None for m in o.data.materials]}
 imgs={i.name:sha_bytes(bytes(i.packed_file.data)) for i in bpy.data.images if i.packed_file};return rows,imgs
sha_bytes=lambda b:hashlib.sha256(b).hexdigest();before,bi=snapshot(S);old=bpy.data.objects[name].data;ov=[(tuple(v.co),{g.group:g.weight for g in v.groups}) for v in old.vertices];of=[]
for p in old.polygons:of.append({'vertices':list(p.vertices),'uv':{u.name:{vid:list(u.data[l].uv) for vid,l in zip(p.vertices,p.loop_indices)} for u in old.uv_layers},'source':old.attributes['MIA_SOURCE_POLYGON'].data[p.index].value,'slot':p.material_index})
after,ai=snapshot(D);m=bpy.data.objects[name].data;vmap=[x.value for x in m.attributes['MIA_V22_OLD_VERTEX_ID'].data];fmap=[x.value for x in m.attributes['MIA_V22_OLD_FACE_ID'].data];region=[x.value for x in m.attributes['MIA_V22_TERMINAL_REGION'].data];vbad=[];fbad=[];uvbad=[]
for v,oldi in zip(m.vertices,vmap):
 if oldi>=0 and (tuple(v.co)!=ov[oldi][0] or {g.group:g.weight for g in v.groups}!=ov[oldi][1]):vbad.append(v.index)
for p,oldi in zip(m.polygons,fmap):
 if oldi<0:continue
 row=of[oldi];mapped=[vmap[v] for v in p.vertices]
 if set(mapped)!=set(row['vertices']) or m.attributes['MIA_SOURCE_POLYGON'].data[p.index].value!=row['source'] or p.material_index!=row['slot']:fbad.append(p.index)
 for u in m.uv_layers:
  for vid,l in zip(mapped,p.loop_indices):
   if list(u.data[l].uv)!=row['uv'][u.name][vid]:uvbad.append([p.index,u.name,vid])
missing=sorted(set(range(len(of)))-{x for x in fmap if x>=0});expected=json.loads((O/'proposed-selection.json').read_text())['delete_faces'];edgefaces=defaultdict(list);directions=defaultdict(list);patchpoly=[p for p in m.polygons if region[p.index]==1];pverts={v for p in patchpoly for v in p.vertices}
for p in m.polygons:
 for a,b in p.edge_keys:edgefaces[tuple(sorted((a,b)))].append(p.index)
for p in patchpoly:
 vv=list(p.vertices)
 for a,b in zip(vv,vv[1:]+vv[:1]):directions[tuple(sorted((a,b)))].append(a<b)
patchbad=[e for e,v in directions.items() if len(v)!=2 or v[0]==v[1]];m.calc_loop_triangles();vol=0;uvarea=[];geomarea=[];degenerate=0
for t in m.loop_triangles:
 if region[t.polygon_index]!=1:continue
 a,b,c=[m.vertices[i].co for i in t.vertices];area=(b-a).cross(c-a).length*.5;degenerate+=area<1e-12;vol+=a.dot(b.cross(c))/6;uv=[m.uv_layers['MIA_V17_PAINT_UV'].data[l].uv for l in t.loops];x,y,z=uv;ua=abs((y.x-x.x)*(z.y-x.y)-(y.y-x.y)*(z.x-x.x))*.5;uvarea.append(ua);geomarea.append(area)
ratio=np.array(uvarea)/np.maximum(geomarea,1e-15);density=np.sqrt(ratio)*4096*.01
r={'native_sha256':hashes[str(D)],'other_owner_differences':[n for n in before if n!=name and before[n]!=after[n]],'retained_vertices_changed':vbad,'retained_faces_changed':fbad,'retained_uv_changed':uvbad,'deleted_exact_declared430':missing==expected,'source_packed_images_exact':bi==ai,'packed_images':len(bi),'new_vertices':sum(x<0 for x in vmap),'new_faces':sum(x<0 for x in fmap),'new_patch_edges':len(directions),'new_patch_bad_edge_incidence_or_winding':len(patchbad),'new_patch_euler':len(pverts)-len(directions)+len(patchpoly),'new_patch_signed_volume_m3':float(vol),'new_patch_degenerate_triangles':int(degenerate),'global_open_edges':sum(len(fs)==1 for fs in edgefaces.values()),'global_nonmanifold_edges_gt2':sum(len(fs)>2 for fs in edgefaces.values()),'global_loose_edges':sum(not e for e in []) if False else sum(tuple(sorted(e.vertices)) not in edgefaces for e in m.edges),'new_weights_zero':sum(sum(g.weight for g in m.vertices[i].groups)==0 for i in pverts),'new_paintUV_effective_pixels_per_cm_percentiles':dict(zip(['min','p10','median','p90','max'],np.percentile(density,[0,10,50,90,100]).tolist())),'new_UV_zero_area_triangles':int((np.array(uvarea)<1e-12).sum()),'UV_limit':'Nearest source surface transfer can compress or fold UV. Density is local area ratio, not validation of paint continuity. Checker evidence required.','saved':False}
np.savez_compressed(O/'old-new-mapping.npz',new_vertex_to_old=np.array(vmap,np.int32),new_face_to_old=np.array(fmap,np.int32),new_face_region=np.array(region,np.int32));(O/'topology-provenance.json').write_text(json.dumps(r,indent=2));assert all(sha(Path(p))==v for p,v in hashes.items());print(json.dumps(r));assert not(r['other_owner_differences'] or vbad or fbad or uvbad or patchbad) and missing==expected and bi==ai
# New cap only actualUV checker, no native save.
mat=bpy.data.materials.new('DIAG_NEW_CAP_CHECKER');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');uv=n.new('ShaderNodeUVMap');uv.uv_map='MIA_V17_PAINT_UV';check=n.new('ShaderNodeTexChecker');check.inputs['Scale'].default_value=128;mat.node_tree.links.new(uv.outputs[0],check.inputs[0]);mat.node_tree.links.new(check.outputs[0],em.inputs[0]);mat.node_tree.links.new(em.outputs[0],out.inputs[0]);m.materials[M['new_material_slot']]=mat;s=bpy.context.scene
for view in ['Front','Profile','LeftOblique']:
 oldcam=bpy.data.objects['MIA_REVIEW_Head_'+view];cam=oldcam.copy();cam.data=oldcam.data.copy();s.collection.objects.link(cam);cam.location+=Vector((.0803828,-.0187201,1.4967201))-Vector((0,0,1.55));cam.data.ortho_scale=.095;s.camera=cam;s.render.filepath=str(O/('cap_checker_'+view+'.png'));bpy.ops.render.render(write_still=True)
print('AUDIT_DONE')
