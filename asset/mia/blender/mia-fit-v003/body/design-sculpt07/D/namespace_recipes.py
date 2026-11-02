"""D namespace only; fixed C producers and evidence remain unchanged."""
from pathlib import Path
P=Path(__file__).resolve().parent;C=P.parent/'C'
for name in ['build_volume.py','audit_volume.py','install_design.py','render_four.py','compose_review.py','plot_sections.py']:
    s=(C/name).read_text(encoding='utf-8')
    for a,b in [('Sculpt07_C_','Sculpt07_D_'),('SCULPT07_C_','SCULPT07_D_'),('MIA_v003_DesignSculpt07_C','MIA_v003_DesignSculpt07_D'),('sculpt07-C.npz','sculpt07-D.npz'),('actual-four-C','actual-four-D'),('NEW sculpt07-C','NEW sculpt07-D')]:s=s.replace(a,b)
    if name=='compose_review.py':s=s.replace("oldfolder=P.parent/'B/actual-four-B'","oldfolder=P.parent/'C/actual-four-C'").replace('Rejected07-B actual / same fixture','Held07-C actual / same fixture')
    (P/name).write_text(s,encoding='utf-8')
diag=P/'diagnostic';diag.mkdir(exist_ok=True);s=(C/'diagnostic/audit_meridian.py').read_text(encoding='utf-8').replace('sculpt07-C.npz','sculpt07-D.npz').replace('C_mesh_sha256','D_mesh_sha256').replace('C mesh:','D mesh:');(diag/'audit_meridian.py').write_text(s,encoding='utf-8');print('D recipes namespaced')
