"""One actual runtime material ablation to distinguish ink edge from skin holes."""
import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;renderer=P.parent/'render_native_review.py';native=P/'Mia_SourceBrows_v31_C.blend'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256','4fc5504b91c61aef4c48d5e54542fd9add38fd5c6a97b42b8d9b94efbe33ed7a','--tag','browsC-edge-ablation','--preset','source','--only','__configure_only_no_render__']
env=runpy.run_path(str(renderer),run_name='brow_ablation_setup');env['a'].only=''
import bpy
node=bpy.data.materials['V31_SourceBrow_Ink_EdgeCoverage'].node_tree.nodes['V31_Brow_EdgeCoverage']
old=node.inputs['From Max'].default_value;assert abs(old-.15)<1e-6
node.inputs['From Max'].default_value=.000001
for k in env['master'].data.shape_keys.key_blocks:k.value=.5 if k.name.endswith('_BRW_Angry') else 0.
spec=env['spec'];spec['resolution']=[512,512]
env['render']('AngryHalf-edgeOFF',spec,True,False)
records=env['records'];records[-1]['runtime_material_ablation']={'material':'V31_SourceBrow_Ink_EdgeCoverage','input':'V31_Brow_EdgeCoverage/From Max','native_value':old,'runtime_value':.000001,'native_saved':False}
(env['out']/'render-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('BROW_EDGE_PROBE_DONE')
