from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'export_e_replay.py').read_text().replace("shape-e","shape-f2").replace('Mia_FaceFinish8_ConnectedCheekE.blend','Mia_FaceFinish8_ConnectedBuccalF2.blend').replace('for E.','for F2.')
exec(compile(code,str(__file__),'exec'))
