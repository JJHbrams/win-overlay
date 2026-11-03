"""E-owned copies of immutable procedural plumbing; no old recorder execution."""
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'D'
s=(D/'build_volume.py').read_text(encoding='utf-8').replace('SCULPT07_D_','SCULPT07_E_').replace('Sculpt07_D_','Sculpt07_E_').replace('sculpt07-D.npz','breast-step.npz').replace('build-report.json','breast-build-report.json');(P/'build_breast.py').write_text(s,encoding='utf-8')
for name in ['audit_volume.py','install_design.py','compose_review.py','plot_sections.py']:
    s=(D/name).read_text(encoding='utf-8').replace('SCULPT07_D_','SCULPT07_E_').replace('Sculpt07_D_','Sculpt07_E_').replace('MIA_v003_DesignSculpt07_D','MIA_v003_DesignSculpt07_E').replace('sculpt07-D.npz','sculpt07-E.npz').replace('actual-six-D','actual-E')
    if name=='compose_review.py':s=s.replace("oldfolder=P.parent/'C/actual-four-C'","oldfolder=P.parent/'D/actual-six-D'").replace('Held07-C actual / same fixture','Held07-D actual / same fixture').replace('NEW sculpt07-D','NEW sculpt07-E')
    (P/name).write_text(s,encoding='utf-8')
print('E_HELPERS_PREPARED')
