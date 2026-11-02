"""Create C plumbing from frozen B; no A/B mutations or native copying."""
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent/'B'
for name in ['build_volume.py','audit_volume.py','install_design.py','render_four.py','compose_review.py','plot_sections.py']:
    s=(B/name).read_text(encoding='utf-8')
    for a,b in [('Sculpt07_B_','Sculpt07_C_'),('SCULPT07_B_','SCULPT07_C_'),('Sculpt07_B_ORIGINAL_CONTEXT','Sculpt07_C_ORIGINAL_CONTEXT'),('MIA_v003_DesignSculpt07_B','MIA_v003_DesignSculpt07_C'),('sculpt07-B.npz','sculpt07-C.npz'),('actual-four-B','actual-four-C'),('NEW sculpt07-B','NEW sculpt07-C')]:s=s.replace(a,b)
    if name=='compose_review.py':s=s.replace("oldfolder=P.parent/'actual-four'","oldfolder=P.parent/'B/actual-four-B'").replace('Rejected07-A actual / same fixture','Rejected07-B actual / same fixture')
    (P/name).write_text(s,encoding='utf-8')
diag=P/'diagnostic';diag.mkdir(exist_ok=True);s=(B/'diagnostic/audit_meridian.py').read_text(encoding='utf-8').replace('sculpt07-B.npz','sculpt07-C.npz').replace('B_mesh_sha256','C_mesh_sha256').replace('B mesh:','C mesh:');(diag/'audit_meridian.py').write_text(s,encoding='utf-8')
print('C recipes namespaced')
