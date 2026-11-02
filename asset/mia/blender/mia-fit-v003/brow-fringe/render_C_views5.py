"""Root-token-only C source views. Frozen B setup reused with explicit driver."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;base=P/'render_front4.py';text=base.read_text(encoding='utf-8')
text=text.replace("O=P/'actual-B-front4'","O=P/'actual-C-views5'")
text=text.replace('def shoot(label,hair_on):','''def shoot(label,hair_on,view='front'):
    current=next(r['camera'] for r in records0 if r['id']==view+'-hairON')
    camera.matrix_world=Matrix(current['matrix']);camera.data.ortho_scale=current['ortho_scale'];camera.data.shift_x,camera.data.shift_y=current['lens_shift']''')
text=text.replace('camera_record=copy.deepcopy(spec);','camera_record=copy.deepcopy(current);')
text=text.replace("'variant':'B' if runtime", "'variant':'C' if runtime").replace("sha(P/'fringe-B.npz')", "sha(P/'fringe-C.npz')")
text=text[:text.index("shoot('baseline-front-hairOFF'")]+'''
shoot('baseline-left_oblique-hairON',True,'left_oblique')
shoot('baseline-profile-hairON',True,'profile')
runtime=apply_candidate.apply('C')
shoot('candidate-front-hairON',True,'front')
shoot('candidate-left_oblique-hairON',True,'left_oblique')
shoot('candidate-profile-hairON',True,'profile')
assert sha(native)==expected;print('BROW_FRINGE_ACTUAL_C_VIEWS5_DONE',flush=True)
'''
env={'__file__':str(base),'__name__':'brow_fringe_C_views5'};exec(compile(text,str(base),'exec'),env)
driver={'path':str(Path(__file__)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base_renderer_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),
        'changes':'Same selected composition/fixture; actual per-view cameras; C payload; two baseline and three candidate views'}
for row in env['records']:row['runtime_driver']=driver
(env['O']/'records.json').write_text(json.dumps(env['records'],indent=2)+'\n',encoding='utf-8',newline='\n')
