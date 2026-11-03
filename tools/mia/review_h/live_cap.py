"""One lateral cap-patch live edit; source field's old Z boundary is not anatomy."""
from pathlib import Path
import hashlib
import json
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/mia/review_h'))
import live_relax

body=bpy.data.objects['MIA_Review12_H_LiveRepair'];ns=bpy.app.driver_namespace
if body.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
v=np.array([p.co[:] for p in body.data.vertices],np.float32)
d=dict(np.load(Path(ns['MIA_Live_H_Payload'])/'geometry.npz'));f=d['triangles']
phase=globals().get('MIA_EDIT_PHASE','select')
if phase=='select':
    eligible=(abs(v[:,0])>.13)&(abs(v[:,0])<.24)&(v[:,2]>1.31)&(v[:,2]<1.405)
    eligible[(abs(v[:,0])<.16)&(v[:,2]<1.335)]=False
    eligible[(v[:,1]<-.035)&(v[:,2]<1.35)&(abs(v[:,0])<.16)]=False
    head=np.unique(f[d['source_part']==1]);eligible[head]=False
    eligible[ns['MIA_Live_H_Rows']['neck'].ravel()]=False
    weight,edges=live_relax.mask(v,f,eligible)
    ns['MIA_Live_Cap_Before']=v.copy();ns['MIA_Live_Cap_Weight']=weight;ns['MIA_Live_Cap_Edges']=edges
    for p in body.data.polygons:p.select=False
    for e in body.data.edges:e.select=False
    for p in body.data.vertices:p.select=bool(weight[p.index]>0)
    bpy.context.tool_settings.mesh_select_mode=(True,False,False)
    sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
    import review_fixture as fixture
    fixture.aim(bpy.context.scene,0,target=(0,0,1.36),scale=.58,resolution=(800,800))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type!='VIEW_3D':continue
            s=area.spaces.active;s.region_3d.view_location=(0,0,1.36);s.region_3d.view_distance=.58
            s.region_3d.view_rotation=bpy.context.scene.camera.rotation_euler.to_quaternion();s.region_3d.view_perspective='ORTHO'
            s.overlay.show_overlays=True
    bpy.ops.object.mode_set(mode='EDIT')
    print(json.dumps(dict(phase='CAP SELECT ONLY',selected_vertices=int((weight>0).sum()),geometry_changed=False,
                          excluded='Allhead,neckinterior,breastcoreandfrontroot,inferior/medialaxillarywalls,Ewaist/armjoins',
                          domain='Lateralcap13..24cm fromaxis,Z1.31..1.405; mediallowerwallX<.16/Z<1.335held;12mmgeodesicfade')))
else:
    assert phase=='apply' and np.array_equal(v,ns['MIA_Live_Cap_Before'])
    weight=ns['MIA_Live_Cap_Weight'];q=live_relax.relax(v,ns['MIA_Live_Cap_Edges'],weight,36)
    movement=np.linalg.norm(q-v,axis=1);assert movement.max()<.006
    assert np.array_equal(q[weight==0],v[weight==0])
    body.data.vertices.foreach_set('co',q.ravel());body.data.update();bpy.context.view_layer.update()
    ns['MIA_Live_Cap_After']=q.copy()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=False
    report=dict(operation='Live lateralcap patch fairing,one36-passmeshrelaxation',
                selected_vertices=int((weight>0).sum()),maximum_displacement_m=float(movement.max()),
                old_Z1_34_boundary='Implementationdomainexplicitlyexpandedonlywithincappatch;notareductionofsource/geometryverification',
                outside_coordinates_exact=int((weight==0).sum()),head_neck_breast_axillarywalls_Ejoins_exact=True,
                changed_below_old_Z1_34=int(((movement>0)&(v[:,2]<=1.34)).sum()),
                before_sha256=hashlib.sha256(v.tobytes()).hexdigest(),after_sha256=hashlib.sha256(q.tobytes()).hexdigest(),
                native_saved=False,adopted=False)
    (ROOT/'.mia-cache/body-h/live/cap-operation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))
