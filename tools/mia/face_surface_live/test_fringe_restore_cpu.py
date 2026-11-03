"""Actual Blender RNA apply/restore in an explicitly synthetic factory fixture.

Uses frozen real Main and retained M2 coordinate arrays, without opening a
native, using live MCP, rendering, or touching the actual running scene. This
checks deletion/cleanup and array restoration, not production rig/material ART.
"""
import hashlib
import json
from pathlib import Path
import shutil

import bpy
import numpy as np

assert bpy.app.background and not bpy.data.filepath
ROOT=Path(__file__).resolve().parents[3]
READY=ROOT/'.mia-cache/face-live/fringe-terminal01-ready'
OUT=READY/'cpu-restore-objectmode-baseline-off'
assert not OUT.exists()
OUT.mkdir()
for name in ('candidate.json','geometry.npz'):
    shutil.copyfile(READY/name,OUT/name)
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)


def mesh_object(name,q,f):
    me=bpy.data.meshes.new(name);me.from_pydata(q.tolist(),[],f.tolist());me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    return ob


def co_sha(ob):
    return hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices],np.float32).tobytes()).hexdigest()


a=np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz')
source=mesh_object('MIA_V17_PIXAL_DetailedHair',a['main_raw'],a['main_triangles'])
assert co_sha(source)=='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
source.hide_render=True;source.hide_set(True)
derived=source.copy();derived.data=source.data.copy();derived.name='MIA_Hair_CurvedRear03Base_RemainingMain'
bpy.context.scene.collection.objects.link(derived);derived.hide_render=False;derived.hide_set(False)
uv=derived.data.uv_layers.new(name='ExistingFixtureUV')
test_uv=np.tile(np.array([.12345,.6789],np.float32),(len(uv.data),1));uv.data.foreach_set('uv',test_uv.ravel())
rear=np.load(ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup/loop-mask.npz')['polygon_indices']
at=derived.data.attributes.new(name='FixtureExistingRearMask',type='BOOLEAN',domain='FACE')
mask=np.zeros(len(derived.data.polygons),np.int32);mask[rear]=1;at.data.foreach_set('value',mask)
g=bpy.data.node_groups.new('FixtureRearDelete','GeometryNodeTree')
g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
ni=g.nodes.new('NodeGroupInput');no=g.nodes.new('NodeGroupOutput');field=g.nodes.new('GeometryNodeInputNamedAttribute');field.data_type='BOOLEAN';field.inputs['Name'].default_value=at.name
delete=g.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE'
g.links.new(ni.outputs['Geometry'],delete.inputs['Geometry']);g.links.new(field.outputs['Attribute'],delete.inputs['Selection']);g.links.new(delete.outputs['Geometry'],no.inputs['Geometry'])
mod=derived.modifiers.new('FixtureRearDelete','NODES');mod.node_group=g
m2=[derived]
rear_data=np.load(ROOT/'.mia-cache/face-live/curved-rear03/actual-emergence/geometry.npz')
for key in rear_data.files:
    if not key.endswith('_world'):continue
    name=key[:-6]
    m2.append(mesh_object(name,rear_data[key],rear_data[name+'_triangles']))
for side in (-1,1):
    mesh_object(f'V31_SourceBrow_{side}',a[f'V31_SourceBrow_{side}_world'],np.empty((0,3),np.int32))
body=mesh_object('MIA_Review12_H_LiveRepair',np.array([[0,0,0],[1,0,0],[0,1,0]],np.float32),np.array([[0,1,2]],np.int32))
frame=bpy.data.objects.new('MIA_v003_BrowInk_HeadFrame',None);bpy.context.scene.collection.objects.link(frame);frame['Strength']=.6
overlay=mesh_object('MiaHair_BrowInkProjection_-1',np.array([[0,0,0],[.1,0,0],[0,.1,0]],np.float32),np.array([[0,1,2]],np.int32));overlay['mia_role']='brow_display';overlay['MIA12_source_hair_hide_render']=False
ns=bpy.app.driver_namespace
ns['MIA_HairReviewState']=dict(body_sha256=co_sha(body))
ns['MIA_CurvedRear03Base']=dict(objects=m2,source_raw_sha256=co_sha(source))
bpy.context.view_layer.update()


def snapshot():
    return dict(objects=sorted(bpy.data.objects.keys()),groups=sorted(bpy.data.node_groups.keys()),
        materials=sorted(bpy.data.materials.keys()),meshes=sorted(bpy.data.meshes.keys()),
        protected_arrays={ob.name:co_sha(ob) for ob in [source,*m2,body,bpy.data.objects['V31_SourceBrow_-1'],bpy.data.objects['V31_SourceBrow_1']]},
        derived_attributes=[(x.name,x.data_type,x.domain) for x in derived.data.attributes],
        derived_modifiers=[(m.name,m.type,m.node_group.name) for m in derived.modifiers],
        UV_sha256=hashlib.sha256(np.array([x.uv[:] for x in derived.data.uv_layers['ExistingFixtureUV'].data],np.float32).tobytes()).hexdigest(),
        overlay=(overlay.hide_get(),overlay.hide_render,overlay['MIA12_source_hair_hide_render']),strength=float(frame['Strength']))


before=snapshot()
script=Path(__file__).with_name('fringe_terminal_live.py').read_text()
literal="FOLDER=ROOT/'.mia-cache/face-live/fringe-terminal01-ready'"
assert script.count(literal)==1
# Redirect only output/payload directory, so synthetic receipts never occupy
# the actual live evidence paths. The installed geometry payload is identical.
script=script.replace(literal,f'FOLDER=Path({str(OUT)!r})')
env=dict(__name__='__mia_cpu_restore_test__')
for phase in ('select','apply','restore'):
    env['MIA_EDIT_PHASE']=phase
    exec(compile(script,'fringe_terminal_live.py','exec'),env)
    p=OUT/f'live-{phase}.json';record=json.loads(p.read_text())
    record.update(synthetic_factory_fixture=True,actual_live_install=False,live_MCP_used=False)
    p.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    if phase=='apply':
        assert frame['Strength']==0. and overlay.hide_render
        assert len(ns['MIA_FringeTerminal01']['objects'])==3
        assert record['remaining_Main_faces']==118636
after=snapshot()
assert before==after, {k:(before[k],after[k]) for k in before if before[k]!=after[k]}
assert 'MIA_FringeTerminal01' not in ns
report=dict(test='Actual Blender RNA on synthetic factory fixture; not current live scene or native',
    Blender_version=bpy.app.version_string,select_apply_restore_exact=True,
    protected_Main_sha256=co_sha(source),retained_M2_actors=len(m2),
    fixture_existing_UV_unchanged=True,existing_rear_mask_modifier_unchanged=True,
    all_created_objects_meshes_groups_materials_removed=True,graphic_visibility_and_strength_restored=True,
    payload_sha256=hashlib.sha256((READY/'geometry.npz').read_bytes()).hexdigest(),
    genuine_47_key_head_test=False,production_maps_normals_drivers_test=False,
    actual_live_scene_modified=False,GPU_used=False,native_opened=False,native_saved=False,ART=False)
(OUT/'CPU-restore-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
