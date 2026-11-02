"""Read-only exact R2/D2 route inventory; no GPU, render or native save."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;F=P.parent;N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R2.blend');SHA='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def graph(mat):
 nt=mat.node_tree;out=nt.get_output_node('EEVEE');seen=set()
 def upstream(n):
  if n.name in seen:return
  seen.add(n.name)
  for i in n.inputs:
   for l in i.links:upstream(l.from_node)
 upstream(out)
 nodes=[]
 for n in nt.nodes:
  if n.name not in seen:continue
  d=dict(name=n.name,type=n.bl_idname,operation=getattr(n,'operation',None),blend_type=getattr(n,'blend_type',None),uv_map=getattr(n,'uv_map',None),image=n.image.name if n.type=='TEX_IMAGE' and n.image else None,interpolation=getattr(n,'interpolation',None),inputs=[dict(name=i.name,value=val(getattr(i,'default_value',None)),links=[dict(node=l.from_node.name,socket=l.from_socket.name) for l in i.links]) for i in n.inputs],outputs=[dict(name=o.name,value=val(getattr(o,'default_value',None))) for o in n.outputs])
  nodes.append(d)
 return dict(name=mat.name,output=dict(name=out.name,target=out.target,is_active_output=out.is_active_output,surface_links=[dict(node=l.from_node.name,socket=l.from_socket.name) for l in out.inputs['Surface'].links]),active_ancestry_nodes=nodes)
owners={};images={}
for name in ['MIA_V27_SharedHeadBody','V28G_InnerLid_-1','V28G_InnerLid_1']:
 ob=bpy.data.objects[name];mat=ob.material_slots[0].material;assert mat.name=='MIA_v002_'+name+'_RefinedD2';uv=ob.data.uv_layers['UVMap'];a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a)
 owners[name]=dict(slot=0,material=mat.name,active_uv=ob.data.uv_layers.active.name,UVMap_sha256=hashlib.sha256(a.tobytes()).hexdigest(),graph=graph(mat))
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image and n.name in [r['name'] for r in owners[name]['graph']['active_ancestry_nodes']]:
   im=n.image;images[im.name]=dict(size=list(im.size),colorspace=im.colorspace_settings.name,alpha_mode=im.alpha_mode,packed_sha256=hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None,node=n.name)
control=bpy.data.objects['MIA_V27_SharedHeadBody'].material_slots[0].material.node_tree.nodes['V30_ACTUAL_LID_FEATURE_DATA'].image
width,height=control.size;pixels=np.empty(width*height*4,np.float32);control.pixels.foreach_get(pixels);pixels=pixels.reshape(height,width,4)
x0,x1=int(.455*width),int(.545*width)+1;y0,y1=int(.30*height),int(.45*height)+1;alpha=pixels[y0:y1,x0:x1,3].copy();np.savez_compressed(P/'existing-nose-alpha-samples.npz',alpha_bottom_up=alpha,uv_bounds=np.array([x0/width,y0/height,x1/width,y1/height]))
maskstats=dict(uv_rectangle=[.455,.30,.545,.45],raster_size=list(alpha.shape[::-1]),alpha_range=[float(alpha.min()),float(alpha.max())],fractions_above={str(t):float((alpha>t).mean()) for t in [.0001,.1,.5,.9]},mask_source_sha256=images[control.name]['packed_sha256'])
report=dict(native=str(N),sha256=SHA,root_R3_basis='Root reports R3 retains D2 neutral maps/materials; this read-only probe independently traces exact frozen R2 current integrated D2. No R3 render is claimed.',owners=owners,images=images,old_nose_alpha=maskstats,native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==SHA,native_saved=False,GPU_used=False)
(P/'current-active-routes.json').write_text(json.dumps(report,indent=2)+'\n');print('NOSE_LIP_CURRENT_ROUTES_DONE',[(n,o['material']) for n,o in owners.items()],[(n,i['packed_sha256']) for n,i in images.items() if n.startswith('MIA_v002')],flush=True)
