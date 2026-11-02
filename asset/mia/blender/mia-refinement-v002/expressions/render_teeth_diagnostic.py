"""Actual render isolates material/culling on existing white-atlas tooth polygons."""
from pathlib import Path
import argparse, copy, hashlib, json, runpy, sys
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parent;old=P.parents[1]/'mia-visible-art-v30/render_native_review.py'
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native).resolve()
sys.argv=[str(old),'--','--native',str(native),'--sha256',a.sha256,'--tag','teeth-setup-'+a.tag,'--preset','source','--only','__no_setup_frames__']
env=runpy.run_path(str(old),run_name='teeth_diagnostic_setup');render=env['render'];out=P/'review'/a.tag;out.mkdir(parents=True,exist_ok=True);render.__globals__['out']=out;env['a'].only=''
master=env['master'];keys=master.data.shape_keys.key_blocks
for k in keys[1:]:k.value=1. if k.name.endswith('_MIA_ToothyGrin') else 0.
bpy.context.scene.frame_set(2);bpy.context.view_layer.update()
m=master.data;uv=m.uv_layers.active;selected=[]
for f in m.polygons:
 if f.material_index!=0:continue
 q=sum((uv.data[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices)
 if q.x<.46 and q.y>.52:selected.append(f.index)
mat=bpy.data.materials.new('DIAGNOSTIC_WhiteAtlasTeeth_Emission');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.8,.8,.8,1);o=n.new('ShaderNodeOutputMaterial');o.target='ALL';o.is_active_output=True;mat.node_tree.links.new(em.outputs[0],o.inputs['Surface'])
slot=len(m.materials);m.materials.append(mat)
for i in selected:m.polygons[i].material_index=slot
front=copy.deepcopy(env['spec']);front['resolution']=[512,512]
for cull in [True,False]:
 mat.use_backface_culling=cull;render('whiteEmission-cull'+str(cull),front,True,False)
records=dict(native=str(native),native_sha256=a.sha256,classified_faces=len(selected),only_runtime_material_assignment=True,
  diagnostic='White Emission is a diagnostic, not the proposed final material. Original surface/keys/UV are unchanged; no save.',
  actual_render_records=env['records'])
(out/'teeth-diagnostic.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
assert hashlib.sha256(native.read_bytes()).hexdigest()==a.sha256
print('TEETH_DIAGNOSTIC_DONE',len(selected),flush=True)
