"""Freeze core4 source cameras plus held C upper/lower review fixtures."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'render_four.py').read_text(encoding='utf-8')
needle="bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)"
extra="extra=json.loads((P.parent/'C/expanded-review/render-records.json').read_text());extra=[r for r in extra if r['view'] in ['upperoblique','loweropposite']];assert len(extra)==2\nfor r in extra:r['actual_all_light_flags_before_render']=r['actual_lights']\nold=old+extra\n"
s=s.replace(needle,extra+needle,1)
s=s.replace("target=Vector((0,-.035,1.275));dist=2", "target=Vector((0,-.035,1.285 if view in ['upperoblique','loweropposite'] else 1.275));dist=2")
s=s.replace('actual-four-D','actual-six-D').replace('len(records)==4','len(records)==6').replace('SCULPT07_D_ACTUAL_FOUR_DONE','SCULPT07_D_ACTUAL_SIX_DONE').replace('exact_four_cameras=True','exact_six_cameras=True')
(P/'render_core_six.py').write_text(s,encoding='utf-8')
s=(P/'compose_review.py').read_text(encoding='utf-8').replace("P/'actual-four-D'","P/'actual-six-D'");s=s.replace("read_text())\nfont=", "read_text());records=[r for r in records if r['view'] in ['front','profile','F2lowoblique','rearoblique']]\nfont=")
(P/'compose_review.py').write_text(s,encoding='utf-8');print('D_CORE_SIX_PREPARED')
