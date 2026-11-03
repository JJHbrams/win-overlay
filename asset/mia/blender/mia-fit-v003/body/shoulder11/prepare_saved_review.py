"""Reuse frozen10 saved-native proof/capture helpers; write only own11 helpers."""
from pathlib import Path
P=Path(__file__).resolve().parent;T=P.parent/'shoulder10'
code=(T/'verify_native.py').read_text(encoding='utf-8').replace("P/'shoulder10.npz'","P/'shoulder11-canonical.npz'").replace("report['sha256']","report['sha256']").replace('SHOULDER10_FRESH_REOPEN_PASS','SHOULDER11_FRESH_REOPEN_PASS')
(P/'verify_native.py').write_text(code,encoding='utf-8',newline='\n')
code=(T/'render_saved_pair.py').read_text(encoding='utf-8')
code=code.replace("assert read(P/'CPU-audit.json')['status'].startswith('CPU technical guards PASS')","assert all(x['exact'] for x in read(P/'protected-physical-triangles.json').values()) and not read(P/'CPU-audit.json')['new_nonadjacent_intersections']")
code=code.replace("('10',NATIVE10,P/'shoulder10.npz')","('11',NATIVE11,P/'shoulder11-canonical.npz')")
code=code.replace("gray_states['10']","gray_states['11']").replace('SHOULDER10_','SHOULDER11_')
assert 'NATIVE10' not in code and "('11',NATIVE11" in code
(P/'render_saved_pair.py').write_text(code,encoding='utf-8',newline='\n')
print('SHOULDER11_OWN_SAVED_REVIEW_HELPERS_READY')
