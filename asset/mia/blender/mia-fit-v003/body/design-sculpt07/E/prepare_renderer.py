"""E-owned core6 fixture copy; never runs frozen D writers."""
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'D'
s=(D/'render_core_six.py').read_text(encoding='utf-8')
for a,b in [('SCULPT07_D_','SCULPT07_E_'),('Sculpt07_D_','Sculpt07_E_'),('sculpt07-D.npz','sculpt07-E.npz'),('actual-six-D','actual-E')]:s=s.replace(a,b)
(P/'render_core_six.py').write_text(s,encoding='utf-8')
diag=P/'diagnostic';diag.mkdir(exist_ok=True);s=(D/'axilla-review/audit_actual_sections.py').read_text(encoding='utf-8').replace('sculpt07-D.npz','sculpt07-E.npz').replace('ACTUAL D','ACTUAL E');(diag/'audit_actual_sections.py').write_text(s,encoding='utf-8')
print('E_CORE6_RENDER_PREPARED')
