"""Sequential final source and pose images, one GPU process."""
import sys,runpy,argparse
from pathlib import Path
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);native=Path(a.native).resolve();sha=a.sha256;tag=a.tag
renderer=P/'render_native_review.py'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256',sha,'--tag',tag+'-source4','--preset','source']
runpy.run_path(str(renderer),run_name='final_source')
poses=P/'brow-v31/render_brow_poses.py'
sys.argv=[str(poses),'--','--native',str(native),'--sha256',sha,'--tag',tag+'-poses']
runpy.run_path(str(poses),run_name='final_poses')
