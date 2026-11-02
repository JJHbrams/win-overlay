"""Actual identical geometry/shader pose with a bounded ortho depth interval."""
import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;renderer=P.parent/'render_native_review.py';native=P/'Mia_SourceBrows_v31_C.blend'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256','4fc5504b91c61aef4c48d5e54542fd9add38fd5c6a97b42b8d9b94efbe33ed7a','--tag','browsC-depth-range-probe','--preset','source','--only','__configure_only_no_render__']
env=runpy.run_path(str(renderer),run_name='brow_depth_setup');env['a'].only=''
cam=env['cam'];old=[cam.data.clip_start,cam.data.clip_end];cam.data.clip_start=.1;cam.data.clip_end=10
for k in env['master'].data.shape_keys.key_blocks:k.value=.5 if k.name.endswith('_BRW_Angry') else 0.
spec=env['spec'];spec['resolution']=[512,512]
env['render']('AngryHalf-clip10',spec,True,False)
records=env['records'];records[-1]['runtime_depth_ablation']={'before':old,'after':[cam.data.clip_start,cam.data.clip_end],'geometry_materials_unchanged':True,'native_saved':False}
(env['out']/'render-records.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('BROW_DEPTH_RANGE_PROBE_DONE',old)
