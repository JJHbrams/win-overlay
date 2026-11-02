"""Conditionally allocated four frames, same A design with gate polarity fixed."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;wrapper=P/'render_four.py';source=wrapper.read_text(encoding='utf-8').replace("O=P/'review/A-front-oblique4'","O=P/'review/A-gate-corrected-front-oblique4'")
env={'__file__':str(wrapper),'__name__':'brow_gate_corrected_four'};exec(compile(source,str(wrapper),'exec'),env)
records=env['records']
for r in records:r['diagnostic_driver']=dict(path=str(Path(__file__)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),setup_wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),change='Output directory only; actual current helper differs from failedA only by the viewer-axis sign.')
(env['O']/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8');print('BROW_GATE_CORRECTED_FOUR_DONE',str(env['O']/'render-records.json'),flush=True)
