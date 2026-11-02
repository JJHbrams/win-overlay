"""Audit manual design and ACTUAL surface support; never changes geometry."""
from pathlib import Path
import ast,json,math,hashlib
import numpy as np
P=Path(__file__).resolve().parent;B=P.parent
c=json.loads((P/'construction.json').read_text());s=json.loads((B/'source-binding/constraints.json').read_text())
env=dict(np=np,zstation=np.array(c['design_heights']),xstation=np.array(c['design_x']),ycurves=np.array(c['design_front_y']))
tree=ast.parse((P/'build_patch.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['pchip','front_y']]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'readonly-design-functions','exec'),env)
e=np.load(P/'evaluated06.npz');v=e['world'];t=e['triangles'];m=e['triangle_materials'];co=math.cos(math.radians(40));si=math.sin(math.radians(40));rows=[]
for b in s['section_support_bands']:
    z=b['world_z'];x=np.linspace(0,.145,4001);y=np.array([env['front_y'](xx,z) for xx in x]);support=co*x-si*(y+.018);i=support.argmax()
    signed=v[:,2]-z;sel=(m==1)&(signed[t].min(1)<0)&(signed[t].max(1)>0);hits=[]
    for tri in t[sel]:
        for ia,ib in [(0,1),(1,2),(2,0)]:
            u,w=tri[[ia,ib]];du,dw=signed[u],signed[w]
            if du*dw<0:
                p=v[u]+du/(du-dw)*(v[w]-v[u])
                if abs(p[0])<b['v06_outer_halfwidth']+.015 and p[1]<-.035:hits.append(p)
    hit=np.array(hits);val=co*np.abs(hit[:,0])-si*(hit[:,1]+.018);j=val.argmax()
    rows.append(dict(station=b['station'],v06_world_z=z,observed_support_m=b['oblique_support_m'],declared_uncertainty_m=b['oblique_support_uncertainty_m'],
        manual_design_support_m=float(support[i]),manual_design_residual_mm=float((support[i]-b['oblique_support_m'])*1000),manual_maximizer_xy=[float(x[i]),float(y[i])],
        manual_profile_minY=float(y.min()),v06_profile_y=b['v06_front_profile_y'],actual_approx_support_m=float(val[j]),actual_residual_mm=float((val[j]-b['oblique_support_m'])*1000),actual_maximizer_world=hit[j].tolist()))
report=dict(status='SOURCE BINDING FAIL: manual curves were not constrained by source bands during construction. This is a diagnostic first look only.',
    source_sha256=s['source_sha256'],prototype_sha256=hashlib.sha256((P/'prototype06.npz').read_bytes()).hexdigest(),
    convention='max cos40*absX - sin40*(Y+0.018); maximizer allowed to move. No fixed inferred lateral tangent point.',
    actual_selection_limit='Approximate spatial cup/body-front section: material1, absX<v06halfwidth+15mm,Y<-35mm. Not final reviewed semantic garment region.',
    rows=rows,provenance='Manual3D design hypotheses. Reading sourceJSON after mesh creation was insufficient; source-bound construction remains pending. No geometry altered by this audit.')
(P/'source-gate-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PATCH06_SOURCE_GATE_AUDIT_DONE',json.dumps(rows),flush=True)
