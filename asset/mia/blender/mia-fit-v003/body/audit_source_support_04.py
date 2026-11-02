"""Whole curve support, and final evaluated horizontal plane intersections."""
from pathlib import Path
import json,math
import numpy as np
from field_math import periodic_theta
P=Path(__file__).resolve().parent;O=P/'posed-target';C=P/'source-binding';s=json.loads((C/'constraints.json').read_text());section=json.loads((C/'source-3D-sections-04.json').read_text());d=np.load(O/'evaluated-04.npz');world=d['world'];tri=d['triangles'];mi=d['triangle_materials'];yaw=math.radians(s['cameras']['F2']['yaw_degrees']);normal=np.array([-math.cos(yaw),-math.sin(yaw)]);rows=[]
for band in s['section_support_bands']:
    z=band['world_z'];r=next(q for q in section['sections'] if abs(q['z']-z)<1e-8);u=np.linspace(-math.pi,math.pi,2001,endpoint=False);curve=periodic_theta(np.array(section['angles']),np.asarray(r['points']),u);cv=curve[:,:2]-[0,-.018];support=cv@normal;imax=int(support.argmax());parts=world[tri];delta=parts[:,:,2]-z;active=(mi==1)&(delta.min(1)<0)&(delta.max(1)>0);points=[]
    for face in parts[active]:
        for i,j in [(0,1),(1,2),(2,0)]:
            a,b=face[i],face[j]
            if (a[2]-z)*(b[2]-z)<0:
                p=a+(b-a)*(z-a[2])/(b[2]-a[2])
                if abs(p[0])<.18 and p[1]<-.050:points.append(p)
    points=np.asarray(points);values=(points[:,:2]-[0,-.018])@normal;k=int(values.argmax());actual=float(values[k]);expected=band['oblique_support_m'];unc=band['oblique_support_uncertainty_m'];rows.append(dict(z=z,source_F2_y=band['source_F2_y'],source_support=expected,uncertainty=unc,whole_C2_curve_support=float(support[imax]),whole_curve_extremum=curve[imax].tolist(),final_actual_skin_support=actual,actual_extremum=points[k].tolist(),actual_support_residual_mm=(actual-expected)*1000,within_support_uncertainty=bool(abs(actual-expected)<=unc),final_front_cup_x_interval=[float(points[:,0].min()),float(points[:,0].max())],source_E2_front_width=band['source_front_width_m'],limits='Final actual skin section Y<−50mm and |X|<180mm excludes most arm context. Tangent bounds are view dependent; observed cloth outer skin inset/pose uncertainty remains. This is not a wholeART test.'))
(C/'actual-support-audit-04.json').write_text(json.dumps(dict(rows=rows,status='Observed-source support versus FULL curves and final evaluated intersections; actual visual/branch review still required.'),indent=2)+'\n',encoding='utf-8');print('SOURCE_WHOLE_CURVE_SUPPORT_AUDIT_DONE',json.dumps(rows),flush=True)
