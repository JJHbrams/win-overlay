from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'diagnose_buccal_f.py').read_text().replace("('D',ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend')","('F',ROOT/'shape-f/Mia_FaceFinish8_CentralBuccalF.blend')").replace('evaluated-buccal-diagnosis.json','evaluated-buccal-f-result.json')
exec(compile(code,str(ROOT/'diagnose_buccal_f.py'),'exec'))
