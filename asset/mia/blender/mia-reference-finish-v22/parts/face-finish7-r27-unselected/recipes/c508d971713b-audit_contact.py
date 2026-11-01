"""Actual evaluated R23/R27 eyelid boundary equality at0,.5,1."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent;H=OUT.parent.parent
sources={'r23':H/'candidate-r23/Mia_FaceFinish7_BlinkR23_v22.blend','r27':OUT/'Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'};data={};hashes={}
for label,path in sources.items():
 hashes[label]=hashlib.sha256(path.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];keys=o.data.shape_keys.key_blocks
 for key in keys:key.value=0.
 values={};ids=None
 for value in [0.,.5,1.]:
  keys['Face.M_F00_000_00_Fcl_EYE_Close'].value=value;bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();p=np.array([tuple(v.co) for v in mesh.vertices])
  if ids is None:
   faces=[list(f.vertices) for f in mesh.polygons];count=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in faces for i in range(len(f)));ids=sorted({i for e,n in count.items() if n==1 for i in e if .01<abs(p[i,0])<.061 and p[i,1]>.035 and 1.525<p[i,2]<1.558})
  values[value]=p[ids].copy();ev.to_mesh_clear()
 data[label]={'ids':ids,'values':values};assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[label]
assert data['r23']['ids']==data['r27']['ids'];records=[]
for value in [0.,.5,1.]:
 a=data['r23']['values'][value];b=data['r27']['values'][value];maximum=float(np.linalg.norm(b-a,axis=1).max());assert maximum==0.,(value,maximum);records.append({'actual_Close':value,'max_evaluated_aperture_delta_m':maximum,'boundary_vertices':len(a)})
(OUT/'contact-audit.json').write_text(json.dumps({'sources':{k:{'path':str(v),'sha256':hashes[k]} for k,v in sources.items()},'records':records,'limits':'Aperture boundary equality preserves R23 contact behavior, including its disclosed subpixel full-closure residual; it is not a claim that all nearby interior motion is identical.'},indent=2));print(json.dumps(records,indent=2))
