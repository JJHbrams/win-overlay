from pathlib import Path
base=Path(__file__).resolve().parent.parent/'candidate-r25/refinement-r27/audit_contact.py'
source=base.read_text().replace('H=OUT.parent.parent','H=OUT.parent').replace("'r27':OUT/'Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'","'r28':OUT/'Mia_FaceFinish7_MedialTransitionR28_v22.blend'").replace("data['r27']","data['r28']")
exec(compile(source,str(base),'exec'))
