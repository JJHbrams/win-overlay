"""Independent B25-state guard, reusing frozen A audit implementation."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;base=P/'audit_upper_A.py'
source=base.read_text(encoding='utf8')
old="A=W/'Mia_LashPose_v31_A.blend'";assert old in source
source=source.replace(old,"A=W/'Mia_LashPose_v31_B.blend'",1)
old="ASHA='d98e80ceb438b3b4fab1028f2f4b5b4a85152a6de1930a538321f6cd732b2a24'";assert old in source
source=source.replace(old,"ASHA='0dde1b1cf6da83ff6dea627890ab6d03342e0a968e762afe1d0986b3c89c188f'",1)
source=source.replace('upper-A-guard.json','upper-B-guard.json').replace('UPPER_A_GUARD','UPPER_B_GUARD')
source=source.replace("'A':hashlib.sha256(A.read_bytes())","'B':hashlib.sha256(A.read_bytes())")
exec(compile(source,str(base),'exec'),{'__name__':'__main__','__file__':str(__file__)})
path=P/'upper-B-guard.json';report=json.loads(path.read_text())
assert report['sha256']=='0dde1b1cf6da83ff6dea627890ab6d03342e0a968e762afe1d0986b3c89c188f'
assert report['summary']['states']==25
print('UPPER_B_AUDIT_DONE_REPORT_SHA256',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
