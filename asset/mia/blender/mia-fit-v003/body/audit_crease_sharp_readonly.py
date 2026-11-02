from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parent;d=json.loads((P/'current-body-audit.json').read_text());bpy.ops.wm.open_mainfile(filepath=d['native'],use_scripts=False);me=bpy.data.objects['MIA_V27_SharedHeadBody'].data;q=np.load(P/'inputs/mapping-frame1.npz')['q0_world'];edges=np.asarray([e.vertices[:] for e in me.edges]);report={}
for name in ['crease_edge','sharp_edge','sharp_face']:
 if name not in me.attributes:report[name]={'present':False};continue
 a=me.attributes[name];v=np.asarray([x.value for x in a.data]);nz=np.flatnonzero(v!=0);row=dict(present=True,domain=a.domain,count=len(v),nonzero=len(nz),max=float(v.max()))
 if a.domain=='EDGE':
  c=q[edges].mean(1);ii=nz[(c[nz,2]>1.14)&(c[nz,2]<1.42)&(abs(c[nz,0])<.22)&(c[nz,1]<.055)];row['thorax_axilla_nonzero']=[dict(edge=int(i),vertices=edges[i].tolist(),value=float(v[i]),center=c[i].tolist()) for i in ii]
 report[name]=row
(P/'posed-target/crease-sharp-readonly.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('CREASE_SHARP_READ_ONLY_DONE',json.dumps(report),flush=True)
