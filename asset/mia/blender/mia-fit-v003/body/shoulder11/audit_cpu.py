"""Read-only reuse of frozen09 actual-triangle audit, redirected into11 only."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
SOURCE=P.parent/'posterior-union09/audit_mesh.py'
code=SOURCE.read_text(encoding='utf-8')
old="a=np.load(E/'breast-step.npz');b=np.load(P/'posterior09.npz')"
assert code.count(old)==1
code=code.replace(old,"a=np.load(P.parent/'posterior-union09/posterior09.npz');b=np.load(P/'shoulder11-canonical.npz')")
code=code.replace("P/'posterior09.npz'","P/'shoulder11-canonical.npz'")
code=code.replace('1.420','1.465').replace('aboveZ1.420','aboveZ1.465')
needle="assert breast['exact'],breast"
insert="""assert breast['exact'],breast
lower=equal_surface('Entire09 lower protected surfaceZ<=1.36',lambda q:q[:,2]<=1.36)
protected_result=dict(breast=breast,lower=lower,upper_neck=neck)
(P/'protected-physical-triangles.json').write_text(json.dumps(protected_result,indent=2)+'\\n',encoding='utf-8',newline='\\n')
assert lower['exact'] and neck['exact'],('STOP protectedphysicalhold failed; no postmesh correction',protected_result)
"""
assert code.count(needle)==1;code=code.replace(needle,insert)
code=code.replace('breast_surface=breast,neck_surface=neck','breast_surface=breast,neck_surface=neck,lower_surface=lower')
code=code.replace('POSTERIOR09_CPU','SHOULDER11_CPU').replace('E_to09','09_to11').replace('09_toE','11_to09')
exec(compile(code,str(SOURCE)+'::own11baseline_adaptation','exec'),globals())
