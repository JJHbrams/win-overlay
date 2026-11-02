"""One sequential GPU batch for exact integrated source/poses/closed comparisons."""
import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parent
native=P/'integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend'
sha='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a'
renderer=P/'render_final_v31.py'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256',sha,'--tag','v31-brows-lashes']
runpy.run_path(str(renderer),run_name='delivery_source_poses')
macro=P/'render_closed_macro.py'
for path,h,tag in [(P/'integrated/brows-C-outer-E/Mia_SourceLook_v31_Review_CleanHair.blend','9dd072af38d52130aa693c561545b2b70b98f22c3b69145fc2b7211cd1632505','v31-close-before'),(native,sha,'v31-close-after')]:
 sys.argv=[str(macro),'--','--native',str(path),'--sha256',h,'--tag',tag]
 runpy.run_path(str(macro),run_name='delivery_macro')
print('V31_DELIVERY_IMAGES_DONE')
