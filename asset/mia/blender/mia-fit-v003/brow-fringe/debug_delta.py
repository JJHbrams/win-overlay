"""Bounded CPU key readback; not artwork evidence."""
import bpy,numpy as np,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import apply_candidate
main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
def coords():
    dg=bpy.context.evaluated_depsgraph_get();e=main.evaluated_get(dg);m=e.to_mesh();q=np.array([list(e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear();return q
q0=coords();r=apply_candidate.apply();q1=coords();main.data.update();main.update_tag(refresh={'DATA'});bpy.context.view_layer.update();q2=coords()
a=np.load(P/'fringe-A.npz');print('ACTUAL_DELTA '+json.dumps({'apply':r,'key_value':main.data.shape_keys.key_blocks[apply_candidate.KEY].value,'show_only':main.show_only_shape_key,'raw_max_payload_mm':float(np.linalg.norm(a['delta_local'],axis=1).max()*1000),'eval_before_tag_mm':float(np.linalg.norm(q1-q0,axis=1).max()*1000),'eval_after_tag_mm':float(np.linalg.norm(q2-q0,axis=1).max()*1000)}),flush=True)
