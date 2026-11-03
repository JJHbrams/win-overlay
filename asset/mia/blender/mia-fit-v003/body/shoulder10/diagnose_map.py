"""Read existing one-candidate section data; isolate the outer-fade slope term."""
from common import *
audit=read(P/'CPU-audit.json');rows=[]
for section in audit['actual_crossY_roofs']:
    samples=section['samples'];before=np.array([s['before']['world'] for s in samples]);after=np.array([s['after']['world'] for s in samples]);x=before[:,0]
    slope0=np.diff(before[:,2])/np.diff(x);slope1=np.diff(after[:,2])/np.diff(x)
    turns0=np.degrees(abs(np.diff(np.arctan(slope0))));turns1=np.degrees(abs(np.diff(np.arctan(slope1))))
    diagnostics=[]
    for i in np.flatnonzero((x[:-1]>.14)&(x[1:]<.19)):
        point=(before[i]+before[i+1])*.5;wx,bz,dw,db=factors(point[None,:]);jzz=1-.032*wx[0]*db[0]
        vertical_term=jzz*slope0[i];fade_term=-.032*dw[0]*bz[0]
        diagnostics.append(dict(x_interval=x[i:i+2].tolist(),before_world=before[i:i+2].tolist(),after_world=after[i:i+2].tolist(),
            baseline_slope=float(slope0[i]),candidate_actual_slope=float(slope1[i]),candidate_rise_mm=float(1000*(after[i+1,2]-after[i,2])),
            analytic_midpoint_vertical_term=float(vertical_term),analytic_midpoint_Xfade_term=float(fade_term),analytic_slope_sum=float(vertical_term+fade_term)))
    valid=(x[1:-1]>.04)&(x[1:-1]<.185);k=np.flatnonzero(valid)[np.argmax(turns1[valid])]
    rows.append(dict(y=section['y'],outercap_segments=diagnostics,
        actual_positive_outward_segments=[d for d in diagnostics if d['candidate_actual_slope']>0],
        largest_active_tangent_turn=dict(x_triplet=x[k:k+3].tolist(),before_z=before[k:k+3,2].tolist(),after_z=after[k:k+3,2].tolist(),before_degrees=float(turns0[k]),after_degrees=float(turns1[k]))))
report=dict(candidate_sha256=sha(P/'shoulder10.npz'),geometry_changed_by_this_script=False,diagnosis='Outer X fade restores a less-lowered cap while the medialroof is strongly lowered. Positive outward slope can result despite positive ambientJacobian and C2 displacement.',
    chain_rule='dZnew/dX=(1-A*Wx*Bprime)*dZold/dX - A*Wxprime*B. In outerfade Wxprime<0, adding a positive outward slope term.',
    actual_sections=rows,limits='FixedY roof sections are continuity diagnostics, not directsource-corresponding3D points. The front/back maximum-overY projected source comparison is separate. No furthergeometryvariant authorized.',
    interpretation='Actualfront/back Normal and gray show a raised thin cap lip/horizontal shoulderbar; actualprofile/oblique show cap-neck depression/step. Producer ART concern remains, independent review required.')
write(P/'map-cause.json',report)
for row in rows:
    print('MAP_CAUSE_Y',row['y'],'upturns',[(d['x_interval'],d['candidate_actual_slope'],d['analytic_midpoint_vertical_term'],d['analytic_midpoint_Xfade_term']) for d in row['actual_positive_outward_segments']], 'peakturn',row['largest_active_tangent_turn'])
