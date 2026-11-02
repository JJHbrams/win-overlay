"""Actual matched whole-fan profile/grazing proof on a specified packed native."""
import sys,json,runpy,argparse,copy,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
native=Path(a.native).resolve();sha=a.sha256;tag=a.tag;renderer=P/'render_native_review.py'
sys.argv=[str(renderer),'--','--native',str(native),'--sha256',sha,'--tag',tag,'--preset','source','--only','__configure_only_no_render__']
env=runpy.run_path(str(renderer),run_name='closed_macro_setup');env['a'].only=''
views=json.loads((P/'closed-lashes-v31/first-proof-B/records.json').read_text())
for label in ['B-profileClosed','B-grazingClosed','B-profileHalf','B-grazingHalf']:
 row=next(r for r in views if r['id']==label)
 for k in env['master'].data.shape_keys.key_blocks:k.value=row['active_master_keys'].get(k.name,0.)
 v=copy.deepcopy(env['spec']);v.update(row['camera'])
 env['render'](label.removeprefix('B-'),v,True,False)
assert hashlib.sha256(native.read_bytes()).hexdigest()==sha
print('CLOSED_MACRO_IMAGES_DONE',tag,len(env['records']))
