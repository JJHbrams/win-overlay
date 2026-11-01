"""Reuse exact source camera/light renderer for actual brow pose proof."""
import sys, runpy, copy
from pathlib import Path
P=Path(__file__).resolve().parent
native=P/'Mia_SourceBrows_v31_C.blend'
renderer=P.parent/'render_native_review.py'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256','4fc5504b91c61aef4c48d5e54542fd9add38fd5c6a97b42b8d9b94efbe33ed7a','--tag','browsC-poses','--preset','source','--only','__configure_only_no_render__']
env=runpy.run_path(str(renderer),run_name='brow_pose_setup')
env['a'].only=''
master=env['master'];keys=master.data.shape_keys.key_blocks
front=copy.deepcopy(env['spec']);front['resolution']=[512,512]
for suffix,value in [('neutral',0.),('BRW_Angry',.5),('BRW_Angry',1.),('BRW_Fun',1.),('BRW_Joy',1.),('BRW_Sorrow',.5),('BRW_Sorrow',1.),('BRW_Surprised',1.),('EYE_Close',.5),('EYE_Close',1.)]:
 for k in keys:k.value=value if k.name.endswith('_'+suffix) else 0.
 env['render'](suffix+'-'+str(value),front,True,False)
for k in keys:k.value=0.
for row in env['pkg']['views'][1:]:
 for k in keys:k.value=.5 if k.name.endswith('_BRW_Angry') else 0.
 v=copy.deepcopy(row['candidate_camera']);v['resolution']=[512,512]
 env['render'](row['id']+'-AngryHalf',v,True,False)
print('BROW_POSE_IMAGES_DONE',len(env['records']))
