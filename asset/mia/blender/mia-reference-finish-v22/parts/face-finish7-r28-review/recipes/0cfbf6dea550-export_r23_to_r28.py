"""Complete exact R23-to-R28 replay for explicitly unapproved review WIP."""
from pathlib import Path
base=Path(__file__).with_name('export_r28.py');source=base.read_text()
source=source.replace("SOURCE=H/'candidate-r25/refinement-r27/Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'","SOURCE=H/'candidate-r23/Mia_FaceFinish7_BlinkR23_v22.blend'")
source=source[:source.index('outer=[249,236')]+"\nfor p,digest in hashes.items():assert sha(p)==digest\ndata['status']='WORKING CANDIDATE / ART UNAPPROVED'\n(OUT/'owner-key-replay-from-r23.json').write_text(json.dumps(data,indent=2))\nprint(json.dumps({'source':data['source'],'target':data['target'],'replay_sha256':sha(OUT/'owner-key-replay-from-r23.json'),'changed_skin_vertices':len(data['owners']['MIA_V14_SculptedSkin']['mesh_cache']['rows'])},indent=2))\n"
source=source.replace('R27->R28','R23->R28').replace('Do not treat this as a R23 baseline replay.','This is the complete R23 baseline replay; do not add R25/R26/R27/R28 intermediate deltas again.')
expanded=Path(__file__).with_name('expanded-r23-export.py');expanded.write_text(source);exec(compile(source,str(expanded),'exec'))
