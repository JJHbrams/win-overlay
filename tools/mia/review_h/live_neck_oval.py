"""One live neck-section regularization; inspect prepared delta before apply.

An elliptical section is an artist's simple form hypothesis for this stylized
neck, not a claim that all human neck cross sections are exact ellipses.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
body=bpy.data.objects['MIA_Review12_H_LiveRepair'];ns=bpy.app.driver_namespace
if body.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
v=np.array([p.co[:] for p in body.data.vertices],np.float32)
rows=ns['MIA_Live_H_Rows']['neck'];phase=globals().get('MIA_EDIT_PHASE','select')


def area(xy):
    return float(.5*abs(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))))


if phase=='select':
    q=v.copy();row_reports=[]
    for k,ids in enumerate(rows,start=1):
        xy=v[ids,:2].astype(float);center=xy.mean(0);d=xy-center
        A=np.column_stack([d[:,0]**2,2*d[:,0]*d[:,1],d[:,1]**2])
        coefficients=np.linalg.lstsq(A,np.ones(len(xy)),rcond=None)[0]
        Q=np.array([[coefficients[0],coefficients[1]],[coefficients[1],coefficients[2]]])
        assert np.linalg.eigvalsh(Q).min()>0
        radius=np.linalg.norm(d,axis=1);direction=d/radius[:,None]
        target_radius=1./np.sqrt(np.einsum('ij,jk,ik->i',direction,Q,direction))
        target=center+target_radius[:,None]*direction
        target=center+(target-center)*np.sqrt(area(xy)/area(target))
        z=float(v[ids,2].mean());t=min((z-1.4)/.012,(1.465-z)/.012,1.);t=max(t,0.)
        weight=t*t*t*(10-15*t+6*t*t)
        changed=xy+weight*(target-xy)
        changed=center+(changed-center)*np.sqrt(area(xy)/area(changed))
        q[ids,:2]=changed
        row_reports.append(dict(row=k,weight=weight,area_before_m2=area(xy),area_after_m2=area(q[ids,:2]),
                                max_displacement_m=float(np.linalg.norm(changed-xy,axis=1).max())))
    movement=np.linalg.norm(q-v,axis=1);assert movement.max()<.006
    protected=np.ones(len(v),bool);protected[rows.ravel()]=False
    assert np.array_equal(q[protected],v[protected]) and np.array_equal(q[:,2],v[:,2])
    ns['MIA_Live_NeckOval_Before']=v.copy();ns['MIA_Live_NeckOval_After']=q.copy()
    ns['MIA_Live_NeckOval_Report']=dict(operation='Live area-preserving oval neck sections; endpoint12mmC2fade',
        proposed_max_displacement_m=float(movement.max()),selected_vertices=int(rows.size),
        all_outside_coordinates_exact=int(protected.sum()),all_Z_exact=True,rows=row_reports,native_saved=False,adopted=False)
    for p in body.data.polygons:p.select=False
    for e in body.data.edges:e.select=False
    selected=set(map(int,rows.ravel()))
    for p in body.data.vertices:p.select=p.index in selected
    bpy.context.tool_settings.mesh_select_mode=(True,False,False)
    for screen in bpy.data.screens:
        for ar in screen.areas:
            if ar.type=='VIEW_3D':ar.spaces.active.overlay.show_overlays=True
    bpy.ops.object.mode_set(mode='EDIT')
    print(json.dumps(dict(phase='OVAL SELECT ONLY',maximum_proposed_move_m=float(movement.max()),geometry_changed=False)))
else:
    assert phase=='apply'
    q=ns['MIA_Live_NeckOval_After']
    already_applied=np.array_equal(v,q)
    assert already_applied or np.array_equal(v,ns['MIA_Live_NeckOval_Before'])
    if not already_applied:
        body.data.vertices.foreach_set('co',q.ravel());body.data.update();bpy.context.view_layer.update()
    for screen in bpy.data.screens:
        for ar in screen.areas:
            if ar.type=='VIEW_3D':ar.spaces.active.overlay.show_overlays=False
    report=ns['MIA_Live_NeckOval_Report']
    report['actual_world_sha256']=hashlib.sha256(q.tobytes()).hexdigest()
    text=json.dumps(report,indent=2,default=lambda x: x.item() if isinstance(x,np.generic) else x)
    (ROOT/'.mia-cache/body-h/live/neck-oval-operation.json').write_text(text+'\n',encoding='utf8')
    print(json.dumps(dict(operation=report['operation'],maximum_move_m=report['proposed_max_displacement_m'],
                          outside_exact=report['all_outside_coordinates_exact'],all_Z_exact=True,native_saved=False,
                          receipt_only_recovery=already_applied,adopted=False)))
