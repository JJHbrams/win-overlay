"""Actual live first-look of source-guided, distributed volumetric rear locks."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path(globals().get('MIA_CURVED_REAR_FOLDER',ROOT/'.mia-cache/face-live/curved-rear02'))
PREFIX=globals().get('MIA_CURVED_REAR_KEY','MIA_CurvedRear02')
ACTOR_PREFIX=globals().get('MIA_CURVED_REAR_ACTOR_PREFIX','MIA_Hair_CurvedRear02')
ns=bpy.app.driver_namespace
assert 'MIA_HairReviewState' in ns and PREFIX not in ns
assert bpy.context.mode=='OBJECT'
source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
raw=np.array([v.co[:] for v in source.data.vertices],np.float32)
assert hashlib.sha256(raw.tobytes()).hexdigest()=='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c'
cfg=json.loads((FOLDER/'candidate.json').read_text());file=FOLDER/'curves.npz'
assert hashlib.sha256(file.read_bytes()).hexdigest()==cfg['payload_sha256']
data=np.load(file);hidden=data['hidden_faces'];faces=np.array([p.vertices[:] for p in source.data.polygons],np.int32)
assert np.array_equal(faces[hidden],data['expected_hidden_triangles'])
keep_base=bool(globals().get('MIA_CURVED_REAR_KEEP_BASE',False))
if keep_base:
    traced=np.load(ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup/loop-mask.npz')
    hidden=traced['polygon_indices']
    assert np.array_equal(faces[hidden],traced['raw_vertices'])
state=dict(objects=[],meshes=[],groups=[],materials=[],source_visibility=(source.hide_get(),source.hide_render),source_raw_sha256=hashlib.sha256(raw.tobytes()).hexdigest())
ns[PREFIX]=state
derived=source.copy();derived.data=source.data.copy();derived.name=ACTOR_PREFIX+'_RemainingMain'
bpy.context.scene.collection.objects.link(derived);state['objects'].append(derived);state['meshes'].append(derived.data)
attr=derived.data.attributes.new(name=PREFIX+'_RemoveFace',type='BOOLEAN',domain='FACE');mask=np.zeros(len(faces),np.int32);mask[hidden]=1;attr.data.foreach_set('value',mask)
group=bpy.data.node_groups.new(PREFIX+'_DeclaredUnderlap','GeometryNodeTree');state['groups'].append(group)
group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
ni=group.nodes.new('NodeGroupInput');no=group.nodes.new('NodeGroupOutput');field=group.nodes.new('GeometryNodeInputNamedAttribute');field.data_type='BOOLEAN';field.inputs['Name'].default_value=attr.name
delete=group.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE';group.links.new(ni.outputs['Geometry'],delete.inputs['Geometry']);group.links.new(field.outputs['Attribute'],delete.inputs['Selection']);group.links.new(delete.outputs['Geometry'],no.inputs['Geometry'])
mod=derived.modifiers.new(PREFIX+'_Underlap','NODES');mod.node_group=group
material=bpy.data.materials.new(ACTOR_PREFIX+'_GeometryOnly');material.use_nodes=True;state['materials'].append(material)
material.diffuse_color=source.data.materials[0].diffuse_color
bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value=(.18,.15,.14,1);bs.inputs['Roughness'].default_value=.8
counts=[]
for row in cfg['locks']:
    name=row['name'];q=data[name+'_world'];f=data[name+'_triangles'];uv=data[name+'_UV']
    me=bpy.data.meshes.new(ACTOR_PREFIX+'_'+name);me.from_pydata(q.tolist(),[],f.tolist());me.update()
    ob=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(ob)
    state['objects'].append(ob);state['meshes'].append(me)
    me.materials.append(material)
    for p in me.polygons:p.use_smooth=True
    layer=me.uv_layers.new(name='LockParamUV');layer.data.foreach_set('uv',uv.reshape(-1,2).ravel())
    ob['mia_component']='hair';ob['MIA_role']='UNACCEPTED separate '+row['layer']+' source-guided rear lock'
    ob['MIA_source_uv_controls']=json.dumps(row['source_uv']);ob['MIA_buried_root_inferred']=True
    ob['MIA_rig_status']='Static shape probe only; no secondary-motion or skinning acceptance'
    counts.append(dict(name=ob.name,vertices=len(q),triangles=len(f)))
source.hide_set(True);source.hide_render=True;derived.hide_set(False);derived.hide_render=False
derived['mia_component']='hair'
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=False
bpy.context.view_layer.update()
body=bpy.data.objects['MIA_Review12_H_LiveRepair'];body_sha=hashlib.sha256(np.array([v.co[:] for v in body.data.vertices],np.float32).tobytes()).hexdigest()
assert body_sha==ns['MIA_HairReviewState']['body_sha256']
assert hashlib.sha256(np.array([v.co[:] for v in source.data.vertices],np.float32).tobytes()).hexdigest()==state['source_raw_sha256']
report=dict(candidate=cfg['candidate'],actual_live_install=True,locks=counts,declared_underlap_faces=len(hidden),
            continuous_original_posterior_base_retained=keep_base,
            body_sha256=body_sha,original_Main_raw_exact=True,target_shader_finished=False,ART=False,native_saved=False)
(FOLDER/('continuous-base-live-install.json' if keep_base else 'live-install.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
