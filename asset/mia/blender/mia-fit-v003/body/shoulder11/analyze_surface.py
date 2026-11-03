"""Actual meshed roofs/sections/sourceprojection and fieldgradient risks; CPU."""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import field
B=P.parent/'posterior-union09';T=P.parent/'shoulder10';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sp=importlib.util.spec_from_file_location('shoulder11_geometry',P.parent/'posterior-continuity08/geometry.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
a=np.load(B/'posterior09.npz');b=np.load(P/'shoulder11-canonical.npz');v0=a['world'];f0=a['triangles'];v=b['world'];f=b['triangles'];params=json.loads((P/'parameters.json').read_text());F,R=field.make(params)
def ee(ff):return np.unique(np.sort(np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]),axis=1),axis=0)
e0=ee(f0);e=ee(f)
def projectedroof(q,edges,x):
    aa=q[edges[:,0]].astype(float);bb=q[edges[:,1]].astype(float);take=(np.minimum(aa[:,0],bb[:,0])<=x)&(np.maximum(aa[:,0],bb[:,0])>=x)&(abs(bb[:,0]-aa[:,0])>1e-12);ii=np.flatnonzero(take);t=(x-aa[ii,0])/(bb[ii,0]-aa[ii,0]);pp=aa[ii]+t[:,None]*(bb[ii]-aa[ii]);return pp[np.argmax(pp[:,2])]
source=json.loads((T/'build-report.json').read_text())['source_rail_residuals'];source_rows=[]
for row in source:
    p0=projectedroof(v0,e0,row['world_x']);p1=projectedroof(v,e,row['world_x']);source_rows.append(dict(side=row['side'],pixel=row['pixel'],world_x=row['world_x'],source_target_z=row['target_z'],baseline09_projectedroof=p0.tolist(),final11_projectedroof=p1.tolist(),
       before_excess_mm=float(1000*(p0[2]-row['target_z'])),after_excess_mm=float(1000*(p1[2]-row['target_z'])),actual_drop_mm=float(1000*(p1[2]-p0[2]))))
selected=[r for r in source_rows if .065<=abs(r['world_x'])<=.15]
roofs=[]
for y in [-.025,0,.025,.045]:
    samples=[];missing=[]
    for x in np.arange(.04,.18501,.0025):
        h0=g.line_hits(v0,f0,2,{0:float(x),1:y});h1=g.line_hits(v,f,2,{0:float(x),1:y})
        if h0 and h1:samples.append(dict(x=float(x),baseline09=h0[-1],final11=h1[-1],delta_z_mm=1000*(h1[-1]['world'][2]-h0[-1]['world'][2])))
        else:missing.append(dict(x=float(x),baseline_has_surface=bool(h0),final_has_surface=bool(h1)))
    row=dict(y=y,samples=samples,missing_vertical_columns=missing,section_limit='Missing X/Ycolumns are exterior retraction, not meshboundary holes. Do not connect a tangent across an absentcolumn.')
    for key in ['baseline09','final11']:
        points=np.array([s[key]['world'] for s in samples]);x=points[:,0];dx=np.diff(x);slope=np.diff(points[:,2])/dx;contiguous=np.isclose(dx,.0025,rtol=0,atol=1e-8);turn=np.degrees(abs(np.diff(np.arctan(slope))));turnok=contiguous[:-1]&contiguous[1:];outer=(x[:-1]>.14)&contiguous;up=np.flatnonzero(outer&(slope>0));k=int(np.argmax(np.where(turnok,turn,-1)))
        row[key+'_shape_diagnostics']=dict(actual_max_outer_slope=float(slope[outer].max()),positive_outer_segments=[[float(x[i]),float(x[i+1]),float(slope[i])] for i in up],
            max_adjacent_tangent_turn_degrees=float(turn[k]),peakturn_x_triplet=x[k:k+3].tolist(),peakturn_world=points[k:k+3].tolist())
    roofs.append(row)
sections=[]
for z in [1.36,1.365,1.38,1.40,1.42,1.44,1.465]:
    row=dict(z=z,states=[])
    for name,q,ff in [('09',v0,f0),('11FINAL',v,f)]:
        widths={};depths={}
        for y in [0,.025,.045]:
            hs=g.line_hits(q,ff,0,{1:y,2:z});widths[str(y)]=dict(hits=hs,outer_span_mm=1000*(hs[-1]['world'][0]-hs[0]['world'][0]) if hs else None)
        for x in [.04,.08,.12,.16]:
            hs=g.line_hits(q,ff,1,{0:x,2:z});depths[str(x)]=dict(hits=hs,outer_span_mm=1000*(hs[-1]['world'][1]-hs[0]['world'][1]) if hs else None)
        row['states'].append(dict(state=name,widths=widths,depths=depths))
    sections.append(row)
# The derivative risk is measured at actual FINAL meshpoints, not air guesses.
old=field.evaluate(R['original_final_union'],v.astype(float));hom=field.evaluate(R['homothetic_final_union'],v.astype(float));final=field.evaluate(F,v.astype(float));active=np.flatnonzero(abs(hom-old)>1e-12)
pts=v[active].astype(float);grad=[];h=.00001
for axis in range(3):
    d=np.eye(3)[axis]*h;grad.append((field.evaluate(F,pts+d)-field.evaluate(F,pts-d))/(2*h))
grad=np.array(grad).T;gate=params['shoulder11'];tt=np.clip((v[:,2].astype(float)-gate['gate_zero_z'])/(gate['gate_full_z']-gate['gate_zero_z']),0,1);wp=30*tt*tt*(1-tt)*(1-tt)/(gate['gate_full_z']-gate['gate_zero_z']);extra=wp*(hom-old);imax=int(np.argmax(extra))
report=dict(status='Actual11FINAL CPU shape measurements; ART UNVERIFIED',raw_NPZ_sha256=sha(P/'shoulder11.npz'),final_NPZ_sha256=sha(P/'shoulder11-canonical.npz'),
    source_front_projection=dict(method='Exact triangle-edge projectedupperenvelope maxoverY, not midplane correspondences.',before_core_median_excess_mm=float(np.median([r['before_excess_mm'] for r in selected])),after_core_median_excess_mm=float(np.median([r['after_excess_mm'] for r in selected])),samples=source_rows),
    actual_crossY_roofs=roofs,actual_fixedZ_sections=sections,
    field_derivative_risk=dict(actual_active_meshpoints=len(active),minimum_gradient_norm=float(np.linalg.norm(grad,axis=1).min()),maximum_gradient_norm=float(np.linalg.norm(grad,axis=1).max()),
        gate_derivative_bound=1.875/(gate['gate_full_z']-gate['gate_zero_z']),Sprime_times_Fhom_minus_Fold_max=float(extra.max()),that_final_meshpoint=dict(id=imax,world=v[imax].tolist(),old_field=float(old[imax]),hom_field=float(hom[imax])),
        final_field_minus_old_min=float((final-old).min()),actual_final_surface_abs_field_p95_max_mm=(np.percentile(abs(final),[95,100])*1000).tolist(),
        limitation='Field is approximate. Nonzero gradient/nesting does not prevent shelf/dent. GeometryNormal/highlow/sourceactuals remain decisive.'),
    one_native_meshing=True,numerical_canonicalization='Exactly4 known upperprotected Xroundoff restorations <=7.078e-8m; allotherrawcoords/triangles exact, see explicitproof.',GPU_used=False)
(P/'surface-analysis.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print('SHOULDER11_SOURCE',report['source_front_projection']['before_core_median_excess_mm'],report['source_front_projection']['after_core_median_excess_mm'],flush=True)
print('SHOULDER11_GRADIENT',json.dumps(report['field_derivative_risk']),flush=True)
for r in roofs:print('ACTUAL_ROOF',r['y'],r['final11_shape_diagnostics'],flush=True)
for r in sections:print('ACTUAL_FIXEDZ',r['z'],[(s['state'],s['widths']['0']['outer_span_mm'],s['depths']['0.08']['outer_span_mm']) for s in r['states']],flush=True)
