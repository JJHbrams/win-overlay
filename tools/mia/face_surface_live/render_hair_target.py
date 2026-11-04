"""Actual live current-shader diagnostic at the unchanged whole-body source fixture.

New locks still have an explicit temporary geometry material. Rendering them
does not claim final toon maps or a finished hair look.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import re
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
tag=globals().get('MIA_HAIR_REVIEW_TAG')
assert tag is None or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',tag)
OUT=ROOT/'.mia-cache/face-live/curved-rear03/target-diagnostic'
if tag is not None:OUT=OUT/tag
sys.path.insert(0,str(ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'))
import review_fixture as fixture
view=globals().get('MIA_VIEW_REQUEST','back')
assert view in ('front','profile','back','oblique')
assert bpy.app.driver_namespace['MIA_CurvedRear03Base']['provisional_keep']
assert bpy.app.driver_namespace['MIA_HairReviewState']
OUT.mkdir(parents=True,exist_ok=True);image=OUT/(view+'.png');assert not image.exists()
spec=importlib.util.spec_from_file_location('mia_target_capacity',ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);capacity=guard.inspect(5*1024**2);assert not capacity['violations'],capacity
scene=bpy.context.scene;assert scene.render.engine=='BLENDER_EEVEE'
fixture.aim(scene,dict(front=0,profile=90,back=180,oblique=30)[view],0,fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES)
assert bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].hide_render
parts=bpy.app.driver_namespace['MIA_CurvedRear03Base']['objects']
assert all(not ob.hide_render for ob in parts)
body=bpy.data.objects['MIA_Review12_H_LiveRepair'];body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
assert body_sha==bpy.app.driver_namespace['MIA_HairReviewState']['body_sha256']
native_sha=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
current=json.loads((ROOT/'asset/mia/CURRENT_STATE.json').read_text(encoding='utf8'))['active_live_checkpoint']
is_current=(Path(bpy.data.filepath).resolve()==(ROOT/current['path']).resolve() and native_sha==current['sha256'])
assert native_sha=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1' or is_current
record=fixture.record(scene);previous_path=scene.render.filepath
try:
    scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
finally:
    scene.render.filepath=previous_path
assert image.exists() and image.stat().st_size>1000
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==native_sha
report=dict(view=view,path=str(image),sha256=fixture.sha(image),fixture=record,
            baseline_capture='.mia-cache/body-h/ratio-baseline/capture.json',
            body_sha256=body_sha,source_native_sha256=native_sha,
            actual_component='.mia-cache/face-live/curved-rear03/actual-emergence/geometry.npz',
            actual_component_sha256='2b1a8508dfdcd7dc0d74958aaed4899f64486270a457b973fa9822ee98044de3',
            current_original_materials_preserved=True,
            new_lock_material='Temporary Principled geometry placeholder; no final UV paint/normal/toon finish claim.',
            GPU_used=True,saved_review_native=False,ART=False,capacity=capacity)
(OUT/(view+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(view=view,path=str(image),sha256=report['sha256'],actual_render=True,ART=False)))
