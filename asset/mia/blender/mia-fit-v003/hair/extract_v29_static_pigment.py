"""Export only old static pigment nodes; reject geometry/normal/light ancestry."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;O=P/'v29-pigment';W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-face-finish-v29/surface-C/native/Mia_FaceFinish_v29_C.blend';assert hashlib.sha256(N.read_bytes()).hexdigest()=='d7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be'
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;ma=m.materials[0];n=ma.node_tree.nodes;target=n['믹스 (레거시).002'];generated=n['V22_GENERATED_UV_PIGMENT'];seen=set();stack=[target,generated]
while stack:
 node=stack.pop()
 if node in seen:continue
 seen.add(node)
 for inp in node.inputs:
  for link in inp.links:stack.append(link.from_node)
allowed={'MIX_RGB','VALTORGB','RGBTOBW','SEPARATE_COLOR','TEX_IMAGE','UVMAP'};assert all(x.type in allowed for x in seen),[(x.name,x.type) for x in seen];nodes=[];images={};uvnames=set()
for node in sorted(seen,key=lambda x:x.name):
 row=dict(name=node.name,bl_idname=node.bl_idname,type=node.type,inputs={})
 for i,socket in enumerate(node.inputs):
  if not hasattr(socket,'default_value'):continue
  value=socket.default_value
  try:value=list(value)
  except TypeError:pass
  row['inputs'][str(i)]=value
 for prop in ['blend_type','use_alpha','use_clamp','mode','uv_map','interpolation','extension']:
  if hasattr(node,prop):row[prop]=getattr(node,prop)
 if node.type=='UVMAP':uvnames.add(node.uv_map)
 if node.type=='VALTORGB':row['ramp']=dict(color_mode=node.color_ramp.color_mode,hue_interpolation=node.color_ramp.hue_interpolation,interpolation=node.color_ramp.interpolation,elements=[dict(position=e.position,color=list(e.color)) for e in node.color_ramp.elements])
 if node.type=='TEX_IMAGE':
  im=node.image;key=im.name
  if key not in images:
   assert im.packed_file,'Only retained packed source image accepted';blob=bytes(im.packed_file.data);ext='.png' if blob.startswith(b'\x89PNG') else '.jpg' if blob.startswith(b'\xff\xd8') else '.exr' if blob.startswith(b'v/1\x01') else None;assert ext is not None;file='StaticSource_'+str(len(images))+ext;(O/file).write_bytes(blob);images[key]=dict(file=file,sha256=hashlib.sha256(blob).hexdigest(),name=im.name,size=list(im.size),colorspace=im.colorspace_settings.name,alpha_mode=im.alpha_mode)
  row['image']=key
 nodes.append(row)
links=[dict(source=l.from_node.name,output=list(l.from_node.outputs).index(l.from_socket),target=l.to_node.name,input=list(l.to_node.inputs).index(l.to_socket)) for l in ma.node_tree.links if l.from_node in seen and l.to_node in seen]
d=np.load(O/'exact-correspondence.npz');raw=np.array([v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data]);lookup={int(v):i for i,v in enumerate(raw)};out={}
for name in uvnames:
 values=[]
 for source_id,vertices in zip(d['raw_source_ids'],d['raw_vertices']):
  p=m.polygons[lookup[int(source_id)]];mapping={int(v):m.uv_layers[name].data[j].uv[:] for v,j in zip(p.vertices,p.loop_indices)};values.append([mapping[int(v)] for v in vertices])
 out[name]=np.array(values,np.float32)
np.savez_compressed(O/'static-source-UVs.npz',**out);report=dict(nodes=nodes,links=links,images=images,static_base_output=dict(node=target.name,socket=0),generated_image_node=generated.name,UV_names=sorted(uvnames),UV_payload_sha256=hashlib.sha256((O/'static-source-UVs.npz').read_bytes()).hexdigest(),source='Retained v29 pure diffuse pigment ancestry BEFORE V22_GRAZING_EDGE_INK. Combine static base with retained generated overlay alpha; no Fresnel/object-normal/light/BSDF/geometry nodes allowed.',forbidden_old_geometry_normal_light_nodes_reused=False,current_Main_modified=False,native_saved=False)
(O/'static-pigment.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V29_STATIC_PIGMENT_EXTRACTED',len(nodes),len(images),sorted(uvnames),flush=True)
