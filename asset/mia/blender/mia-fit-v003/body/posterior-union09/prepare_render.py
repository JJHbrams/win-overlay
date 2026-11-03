"""Copy/adapt frozen E/08 review code INTO09 only. No rendering or scene edits."""
from pathlib import Path
P=Path(__file__).resolve().parent;E=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E');OLD=P.parent/'posterior-continuity08'
code=(E/'install_design.py').read_text(encoding='utf-8');assert code.count("P/'sculpt07-E.npz'")==1
code=code.replace("P/'sculpt07-E.npz'","P/'posterior09.npz'").replace('MIA_v003_DesignSculpt07_E_UNSELECTED','MIA_v003_PosteriorUnion09_UNSELECTED').replace('Sculpt07_E_ORIGINAL_CONTEXT_SEAMS_UNVERIFIED','Posterior09_ORIGINAL_CONTEXT_SEAMS_UNVERIFIED')
(P/'install_design.py').write_text(code,encoding='utf-8',newline='\n')
code=(OLD/'render_actual8.py').read_text(encoding='utf-8').replace('08','09').replace('PosteriorContinuity09','PosteriorUnion09')
code=code.replace("assert audit09['status'].startswith('CPU_GEOMETRY_GUARDS_PASS')","assert audit09['finite'] and audit09['main_lower_passage_open'] and audit09['breast_surface']['exact'] and not audit09['new_nonadjacent_intersections']")
code=code.replace("audit09['candidate_sha256']","audit09['mesh_sha256']")
code=code.replace("INSTALL.__file__=str(E/'install_design.py')","INSTALL.__file__=str(OUT/'install_design.py')")
code=code.replace("install_code=(E/'install_design.py').read_text(encoding='utf-8').replace(\"(P/'preservation.json')\",\"(OUT/'preservation.json')\")","install_code=(OUT/'install_design.py').read_text(encoding='utf-8')")
code=code.replace("compile(install_code,str(E/'install_design.py')","compile(install_code,str(OUT/'install_design.py')")
code=code.replace("frozen_E_installer_sha256=sha(E/'install_design.py')","own09_installer_sha256=sha(OUT/'install_design.py')")
assert "audit09['main_lower_passage_open']" in code and "INSTALL.__file__=str(OUT/" in code
(P/'render_actual8.py').write_text(code,encoding='utf-8',newline='\n')
code=(OLD/'compose_review.py').read_text(encoding='utf-8').replace('08','09').replace('ONE POSTERIOR FORM','ONE POSTERIOR UNION').replace('broad masses/breast exact','E breast exact; broad surfaces bounded').replace("ART='FAIL: producer inspected all8; root independently inspected6critical includingNormal and agrees new puckers. Unselected; no new variant/native.'","ART='PENDING actual09 review; no adoption from CPU or renders'")
(P/'compose_review.py').write_text(code,encoding='utf-8',newline='\n')
print('POSTERIOR09_OWN_REVIEW_HELPERS_READY')
