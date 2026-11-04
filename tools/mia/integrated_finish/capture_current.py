"""Actual current whole-height and hair views; no model/native mutation."""
from pathlib import Path
import json,runpy,sys,re
import bpy

ROOT=Path(__file__).resolve().parents[3]
stage=globals().get('MIA_CAPTURE_STAGE','baseline')
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',stage)
expected=globals().get('MIA_CAPTURE_BODY_SHA','695dbbd825ce444fd04f0e390ccd64d31265d7cb14b027a08bf2ced82b4a7215')
assert re.fullmatch(r'[a-f0-9]{64}',expected)
OUT=ROOT/'.mia-cache/body-h/live/integrated01'/stage
assert not OUT.exists()
h=runpy.run_path(str(ROOT/'tools/mia/face_surface_live/v29_pigment_current.py'))
before=h['_snapshot'](ROOT)
assert before[h['BODY']]['fingerprint']['coordinates']==expected
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
source=bpy.context.scene
camera=source.camera.copy();data=source.camera.data.copy();camera.data=data
source.collection.objects.link(camera)
old_camera=source.camera
settings=('resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','filepath')
saved={k:getattr(source.render,k) for k in settings};old_format=source.render.image_settings.file_format
visibility={o.name:(o.hide_get(),o.hide_render) for o in source.objects}
OUT.mkdir(parents=True)
record=dict(native=dict(path=bpy.data.filepath,sha256=fixture.sha(Path(bpy.data.filepath))),
 body_sha256=before[h['BODY']]['fingerprint']['coordinates'],
 scope='Actual current integrated baseline, nominal source-facing orientations; uniform source SRT required before proportion judgments',frames=[],ART=False)
try:
    fixture.hair_visibility(source,True)
    for ob in fixture.hair_actors(source):
        if not ob.hide_render:ob.hide_set(False)
    assert bpy.data.objects[h['RAW']].hide_render
    source.camera=camera;data.type='ORTHO';data.clip_start=.1;data.clip_end=10
    source.render.resolution_percentage=100;source.render.pixel_aspect_x=source.render.pixel_aspect_y=1
    source.render.image_settings.file_format='PNG'
    jobs=[('front',0,0),('profile',90,0),('back',180,0),('oblique',30,0),('opposite',-30,0),
          ('hair_back',180,0),('hair_rear_left',150,0),('hair_rear_right',210,0),('hair_high',150,25),('hair_low',210,-20)]
    for name,yaw,pitch in jobs:
        target,scale,res=(fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES)
        if name.startswith('hair_'):target,scale,res=( (0,0,1.365),.78,(800,800) )
        fixture.aim(source,yaw,pitch,target,scale,res)
        path=OUT/(name+'.png');source.render.filepath=str(path)
        actual=fixture.record(source)
        bpy.ops.render.render(write_still=True)
        record['frames'].append(dict(name=name,yaw=yaw,pitch=pitch,path=str(path),sha256=fixture.sha(path),fixture=actual))
        (OUT/'capture.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
finally:
    source.camera=old_camera
    for key,value in saved.items():setattr(source.render,key,value)
    source.render.image_settings.file_format=old_format
    for name,(hidden,render) in visibility.items():
        bpy.data.objects[name].hide_set(hidden);bpy.data.objects[name].hide_render=render
    bpy.data.objects.remove(camera,do_unlink=True);bpy.data.cameras.remove(data)
    bpy.context.view_layer.update()
assert h['_snapshot'](ROOT)==before
print(json.dumps(dict(actual_frames=len(record['frames']),output=str(OUT),model_held=True,ART=False)))
