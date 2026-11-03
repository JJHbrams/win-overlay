"""One fixed-light, fixed-camera before/after set from the actual private live object."""
from pathlib import Path
import importlib.util,json,sys
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[3];CACHE=ROOT/'.mia-cache/body-connected'
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
spec=importlib.util.spec_from_file_location('connected_storage_guard',ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
assert not guard.inspect(40*1024**2)['violations']
ob=bpy.data.objects['MIA_ConnectedBody_Design'];ns=bpy.app.driver_namespace
assert ob.mode=='OBJECT';p=dict(np.load(CACHE/'proposal.npz'))
out=CACHE/'actual-gray';assert not out.exists();out.mkdir()
scene=bpy.context.scene;pose=fixture.digest(fixture.pose(scene));records=[]
original_settings=dict(filepath=scene.render.filepath,resolution_x=scene.render.resolution_x,resolution_y=scene.render.resolution_y)
try:
    for label,yaw,pitch in [('front',0,0),('profile',90,0),('back',180,0),('oblique',30,0),('high',40,25),('low',-40,-25)]:
        fixture.aim(scene,yaw,pitch,(0,-.015,1.32),.74,(720,720))
        for state,co in [('before',ns['MIA_Connected_Baseline_Local']),('after',ns['MIA_Connected_Target_Local'])]:
            ob.data.vertices.foreach_set('co',co.ravel());ob.data.update();bpy.context.view_layer.update()
            assert fixture.digest(fixture.pose(scene))==pose
            path=out/(state+'-'+label+'.png');scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            records.append(dict(state=state,view=label,path=str(path),sha256=fixture.sha(path),fixture=fixture.record(scene)))
            (out/'capture.json').write_text(json.dumps(dict(scope='Actual original-cage DESIGN before/after; no ART approval',records=records,native_saved=False),indent=2)+'\n',encoding='utf8')
            print('CONNECTED_ACTUAL',state,label,flush=True)
finally:
    ob.data.vertices.foreach_set('co',ns['MIA_Connected_Target_Local'].ravel());ob.data.update();bpy.context.view_layer.update()
    for k,v in original_settings.items():setattr(scene.render,k,v)
print('CONNECTED_CAPTURE_COMPLETE_GPU_RELEASE',flush=True)
