"""Sequential final source and pose images, one GPU process."""
import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parent
native=P/'integrated/brows-C-outer-E/Mia_SourceLook_v31_Review.blend'
sha='c3557e9eaa2163ae0d6f712a8c51362c0a6abdab628bcabe3e9673511323813c'
renderer=P/'render_native_review.py'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256',sha,'--tag','v31-final-depthfixed','--preset','source']
runpy.run_path(str(renderer),run_name='final_source')
poses=P/'brow-v31/render_brow_poses.py'
sys.argv=[str(poses),'--','--native',str(native),'--sha256',sha,'--tag','v31-final-poses']
runpy.run_path(str(poses),run_name='final_poses')
