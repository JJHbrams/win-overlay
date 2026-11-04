"""Save one compressed copy of the retained C production state, never a final.

Explicit live MCP phase only. It leaves the live filepath and source checkpoint
unchanged. Root must restore borrowed review state and check capacity first.
"""
from pathlib import Path
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parents[3]


def save(root=ROOT):
    import bpy
    root = Path(root).resolve()
    helper = runpy.run_path(str(root/'tools/mia/face_surface_live/v29_pigment_current.py'))
    small = helper['_helpers'](root)
    ns = bpy.app.driver_namespace
    assert 'MIA_HairReviewState' not in ns, 'Leave the borrowed review first'
    assert bpy.context.mode == 'OBJECT'
    assert ns['MIA_V29PigmentCurrent']['after'] == helper['_snapshot'](root)
    assert ns['MIA_RearRoot01'] and ns['MIA_HairLockLook01'] and ns['MIA_APProfile01']
    original_path = Path(bpy.data.filepath).resolve()
    assert helper['file_sha'](original_path) == helper['NATIVE_SHA']
    folder = root/'.mia-cache/production-resume-20261104'
    path = folder/'Mia_Resume_Static_WIP.blend'
    assert not path.exists(), 'One retained checkpoint, not repeated whole-native candidates'
    folder.mkdir(parents=True, exist_ok=True)
    objects = list(ns['MIA_CurvedRear03Base']['objects'])
    objects += [bpy.data.objects[helper['RAW']], bpy.data.objects[helper['BODY']]]
    inventory = {ob.name:dict(fingerprint=small['fingerprint'](ob),
        hide_render=bool(ob.hide_render), hidden=bool(ob.hide_get()),
        materials=[(s.link,s.material.name if s.material else None) for s in ob.material_slots]) for ob in objects}
    pigment = bpy.data.materials[helper['MATERIAL']]
    images = {n.image.name:dict(size=list(n.image.size),colorspace=n.image.colorspace_settings.name,
        packed=[__import__('hashlib').sha256(p.packed_file.data).hexdigest() for p in n.image.packed_files])
        for n in pigment.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    # Only the two reused maps are owned; other ancestor textures remain original.
    assert len([n for n in images if n.startswith('Recovered')]) == 2
    # A body-editing scene may hide every hair actor. The review copy must
    # expose the retained working replacement while preserving live visibility.
    visibility = {ob.name:(ob.hide_get(),ob.hide_render) for ob in bpy.context.scene.objects}
    sys.path.insert(0,str(root/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
    import review_fixture as fixture
    try:
        fixture.hair_visibility(bpy.context.scene,True)
        for ob in fixture.hair_actors(bpy.context.scene):
            if not ob.hide_render: ob.hide_set(False)
        assert bpy.data.objects[helper['RAW']].hide_render
        assert not bpy.data.objects[helper['TARGET']].hide_render
        for ob in objects:
            inventory[ob.name]['hide_render']=bool(ob.hide_render)
            inventory[ob.name]['hidden']=bool(ob.hide_get())
        bpy.ops.wm.save_as_mainfile(filepath=str(path),copy=True,compress=True,relative_remap=False)
    finally:
        for name,(hidden,render) in visibility.items():
            bpy.data.objects[name].hide_set(hidden);bpy.data.objects[name].hide_render=render
        bpy.context.view_layer.update()
    assert Path(bpy.data.filepath).resolve()==original_path
    assert helper['file_sha'](original_path)==helper['NATIVE_SHA']
    assert {ob.name:small['fingerprint'](ob) for ob in objects} == {
        name:r['fingerprint'] for name,r in inventory.items()}
    report=dict(status='SAVED_RETAINED_STATIC_WIP_COPY_NOT_FINAL',path=str(path),
        sha256=helper['file_sha'](path),bytes=path.stat().st_size,
        original_live_path=str(original_path),original_live_sha256=helper['NATIVE_SHA'],
        objects=inventory,pigment_images=images,
        included=['retained18locklook','retained6rearrootshape','APprofile695','boundedcrownpigment'],
        excluded='Rejected M1 transverse forecast; no new final maps, rig or ART approval',
        open_criteria='M1..M6 and FB remain OPEN; partial improvements only',
        fresh_reopen_verified=False,ART=False)
    (folder/'checkpoint.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return {k:v for k,v in report.items() if k not in ('objects','pigment_images')}


if globals().get('MIA_SAVE_RETAINED_RESUME_COPY') is True:
    print(json.dumps(save(globals().get('MIA_ROOT',ROOT))))
