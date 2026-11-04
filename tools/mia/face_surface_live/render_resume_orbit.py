"""Actual saved-WIP head/hair inspection orbit; no native write or ART gate.

Background Blender only, after fresh reopen verification. This 24-view neutral
preview does not replace the required final 32 angles x two body materials.
"""
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[3]


def render(root=ROOT):
    import bpy
    root=Path(root).resolve(); folder=root/'.mia-cache/production-resume-20261104'
    manifest=json.loads((folder/'checkpoint.json').read_text())
    fresh_path=folder/'fresh-reopen-final.json'
    if not fresh_path.exists(): fresh_path=folder/'fresh-reopen.json'
    fresh=json.loads(fresh_path.read_text())
    assert Path(bpy.data.filepath).resolve()==Path(manifest['path']).resolve()
    assert fresh['sha256']==manifest['sha256']
    sys.path.insert(0,str(root/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
    import review_fixture as fixture
    assert fixture.sha(Path(bpy.data.filepath))==manifest['sha256']
    # The live body-editing visibility is allowed to hide all hair. Render the
    # retained working replacement, never the hidden raw original as well.
    fixture.hair_visibility(bpy.context.scene,True)
    for ob in fixture.hair_actors(bpy.context.scene):
        if not ob.hide_render: ob.hide_set(False)
    assert bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].hide_render
    assert not bpy.data.objects['MIA_Hair_CurvedRear03Base_RemainingMain'].hide_render
    out=folder/'head-hair-orbit'; assert not out.exists(); out.mkdir()
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.render.image_settings.file_format='PNG'
    scene.camera.data.type='ORTHO';scene.camera.data.clip_start=.1;scene.camera.data.clip_end=10
    capture=dict(native=manifest['path'],native_sha256=manifest['sha256'],
        scope='Actual saved WIP neutral head/hair orbit, no pose/motion/FB final approval',
        actual_frame_count=24,frames=[],ART=False)
    for i in range(24):
        yaw=i*15
        fixture.aim(scene,yaw,0,(0,0,1.44),.64,(480,480))
        path=out/f'{i:02d}.png';scene.render.filepath=str(path)
        actual=fixture.record(scene)
        bpy.ops.render.render(write_still=True)
        capture['frames'].append(dict(yaw=yaw,path=str(path),sha256=fixture.sha(path),fixture=actual))
        (out/'capture.json').write_text(json.dumps(capture,indent=2)+'\n',encoding='utf8')
    assert fixture.sha(Path(bpy.data.filepath))==manifest['sha256']
    print(json.dumps(dict(actual_frames=24,output=str(out),native_saved=False,ART=False)))


if __name__=='__main__':render()
