"""Read-only-native CPU mutations; exact in-memory restore, then fresh reopen."""
from pathlib import Path
import hashlib,json,sys,time
import bpy
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import scene_fingerprint as h
HELPER_SHA=hashlib.sha256((P/'scene_fingerprint.py').read_bytes()).hexdigest()
assert h.json_value({'z','a','m'})==['a','m','z']
N=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R2.blend')
SHA='eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();start=time.time()
base=h.snapshot_scene();assert h.canonical_json(base)==h.canonical_json(h.snapshot_scene())
legacy=json.loads(N.with_suffix('.integration.json').read_text())['final_owners'];core=['type','matrix_world','parent','parent_bone','hidden','vertices','loop_vertices','polygon_sizes','uv','materials','keys','weight_hash','modifiers','pose_basis'];legacy_errors=[]
for name,old in legacy.items():
    for field in core:
        if field in old and old[field]!=base['objects'][name][field]:legacy_errors.append([name,field])
assert not legacy_errors,legacy_errors
tests=[]
def fingerprint(ob):bpy.context.view_layer.update();return h.object_fingerprint(ob)
def test(label,ob,change,restore,expected):
    before=fingerprint(ob) if ob else h.scene_envelope()
    try:
        change();bpy.context.view_layer.update();after=fingerprint(ob) if ob else h.scene_envelope()
        changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k));assert set(expected).issubset(changed),(label,expected,changed)
    finally:restore();bpy.context.view_layer.update()
    actual=fingerprint(ob) if ob else h.scene_envelope();assert actual==before,(label,'restore failed')
    tests.append(dict(id=label,detected_fields=changed,exact_restore=True))
rig=bpy.data.objects['MIA_V06_RIG'];ctrl=bpy.data.objects['Mia_FacialControls_v002'];face=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];brow=bpy.data.objects['V31_SourceBrow_-1']
headpath='pose.bones["J_Bip_C_Head"].rotation_euler'
roll=next(f for f in rig.animation_data.drivers if f.data_path==headpath and f.array_index==2)
old=roll.driver.expression
test('head-roll-expression-at-neutral',rig,lambda:setattr(roll.driver,'expression',old+'+0.0'),lambda:setattr(roll.driver,'expression',old),['drivers'])
smile=next(f for f in face.data.shape_keys.animation_data.drivers if 'Fcl_MTH_Fun' in f.data_path);oldsmile=smile.driver.expression
test('smile-shapekey-expression-at-neutral',face,lambda:setattr(smile.driver,'expression',oldsmile+'+0.0'),lambda:setattr(smile.driver,'expression',oldsmile),['drivers'])
variable=roll.driver.variables[0];target=variable.targets[0];oldpath=target.data_path
test('driver-target-path',rig,lambda:setattr(target,'data_path','["HeadYaw"]' if oldpath!='["HeadYaw"]' else '["HeadRoll"]'),lambda:setattr(target,'data_path',oldpath),['drivers'])
for scope,block in [('object',ctrl),('mesh-data',skin.data),('shape-key-data',skin.data.shape_keys)]:
    key='R3_Guard_CPU_Probe';assert key not in block
    test('custom-property-'+scope,ctrl if scope=='object' else skin,lambda block=block:block.__setitem__(key,{'nested':[1.,2.],'note':'CPU only'}),lambda block=block:block.__delitem__(key),['custom_properties'])
# Existing same-name material graph edit must be seen without slot changes.
mat=brow.data.materials[0];em=next(n for n in mat.node_tree.nodes if n.type=='EMISSION');strength=em.inputs['Strength'];oldstrength=strength.default_value
test('same-name-material-socket',brow,lambda:setattr(strength,'default_value',oldstrength+.125),lambda:setattr(strength,'default_value',oldstrength),['material_signatures'])
# Embedded node trees have nonunique RNA names; a shared snapshot cache must
# still produce each material's exact independently-computed signature.
ma=mat.copy();mb=mat.copy()
try:
    assert ma.node_tree.name_full==mb.node_tree.name_full,'Copies must exercise identical embedded-tree RNA names'
    next(n for n in ma.node_tree.nodes if n.type=='EMISSION').inputs['Strength'].default_value=.3
    next(n for n in mb.node_tree.nodes if n.type=='EMISSION').inputs['Strength'].default_value=.8
    shared={};h.material_signature(ma,shared)
    assert h.material_signature(mb,shared)==h.material_signature(mb,{}),'Embedded tree cache collision'
    tests.append(dict(id='same-name-embedded-node-tree-cache',detected_fields=['material_signatures'],exact_restore=True))
finally:bpy.data.materials.remove(ma);bpy.data.materials.remove(mb)
# Recursive shared node-group definition/socket is covered as well.
group=bpy.data.node_groups.new('R3_Guard_CPU_Group','ShaderNodeTree');group.interface.new_socket(name='Probe',in_out='INPUT',socket_type='NodeSocketFloat');node=mat.node_tree.nodes.new('ShaderNodeGroup');node.node_tree=group
try:
    socket=group.interface.items_tree[0];value=socket.default_value
    test('recursive-nodegroup-interface',brow,lambda:setattr(socket,'default_value',value+.2),lambda:setattr(socket,'default_value',value),['material_signatures'])
finally:mat.node_tree.nodes.remove(node);bpy.data.node_groups.remove(group)
attr=skin.data.attributes['V27_HeadMaterialBlend'];oldvalue=attr.data[0].value
test('existing-numeric-POINT-value',skin,lambda:setattr(attr.data[0],'value',oldvalue+.125),lambda:setattr(attr.data[0],'value',oldvalue),['point_attributes'])
attr=skin.data.attributes.new('R3_Guard_CPU_Color','FLOAT_COLOR','POINT')
try:
    color=attr.data[0].color[:]
    test('POINT-FLOAT_COLOR-content',skin,lambda:setattr(attr.data[0],'color',(0.1,0.2,0.3,0.4)),lambda:setattr(attr.data[0],'color',color),['point_attributes'])
finally:skin.data.attributes.remove(attr)
mod=brow.modifiers.new('R3_Guard_CPU_Support','SHRINKWRAP');mod.show_viewport=False;mod.show_render=False;mod.target=skin;mod.wrap_method='PROJECT';mod.wrap_mode='OUTSIDE';mod.use_project_y=True;mod.project_limit=.002;mod.offset=.0001
try:
    value=mod.offset;test('same-name-type-shrinkwrap-offset',brow,lambda:setattr(mod,'offset',.0002),lambda:setattr(mod,'offset',value),['modifier_settings'])
    target=mod.target;test('same-name-type-shrinkwrap-target',brow,lambda:setattr(mod,'target',face),lambda:setattr(mod,'target',target),['modifier_settings'])
finally:brow.modifiers.remove(mod)
camera=s.camera;clip=camera.data.clip_end
test('camera-clip-data',camera,lambda:setattr(camera.data,'clip_end',clip+1.),lambda:setattr(camera.data,'clip_end',clip),['camera_spec'])
lamp=next(o for o in s.objects if o.type=='LIGHT' and not o.hide_render);energy=lamp.data.energy
test('light-energy-data',lamp,lambda:setattr(lamp.data,'energy',energy+1.),lambda:setattr(lamp.data,'energy',energy),['light_spec'])
bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');strength=bg.inputs['Strength'];oldstrength=strength.default_value
test('world-envelope-graph',None,lambda:setattr(strength,'default_value',oldstrength+.1),lambda:setattr(strength,'default_value',oldstrength),['world'])
fps=s.render.fps;test('render-fps-envelope',None,lambda:setattr(s.render,'fps',fps+1),lambda:setattr(s.render,'fps',fps),['render'])

# The allowed rig driver exception is exact by owner/scope/path/index.
before={rig.name:fingerprint(rig)};allowed=dict(id='head-roll-r3',allowed_driver_changes=[dict(owner=rig.name,scope='object',data_path=headpath,array_index=2)])
roll.driver.expression=old+'+0.0';bpy.context.view_layer.update();after={rig.name:fingerprint(rig)}
h.assert_existing_driver_preservation(before,after,allowed);h.assert_scene_pose_owners_protected(before,after,allowed)
roll.driver.expression=old;bpy.context.view_layer.update()
rejects=[]
for description,stage in [('no-exception',dict(id='rejected')),('wrong-index',dict(id='rejected',allowed_driver_changes=[dict(owner=rig.name,scope='object',data_path=headpath,array_index=1)]))]:
    roll.driver.expression=old+'+0.0';bpy.context.view_layer.update();after={rig.name:fingerprint(rig)}
    try:h.assert_scene_pose_owners_protected(before,after,stage)
    except AssertionError:rejects.append(description)
    else:raise AssertionError('Undeclared rig edit passed '+description)
    finally:roll.driver.expression=old;bpy.context.view_layer.update()
# A declared driver cannot excuse rest-pose or camera/light mutations.
pose=rig.pose.bones['J_Bip_C_Head'];scale=pose.scale[:];pose.scale.x+=.01;bpy.context.view_layer.update()
try:h.assert_scene_pose_owners_protected(before,{rig.name:fingerprint(rig)},allowed)
except AssertionError:rejects.append('pose-change-even-with-driver-exception')
else:raise AssertionError('Pose edit escaped driver exception')
finally:pose.scale=scale;bpy.context.view_layer.update()
restored=h.snapshot_scene();assert restored==base,'Full-scene restore mismatch'
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);bpy.context.scene.frame_set(2);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();fresh=h.snapshot_scene();assert fresh==base,'Fresh R2 fingerprint changed'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
assert hashlib.sha256((P/'scene_fingerprint.py').read_bytes()).hexdigest()==HELPER_SHA,'Helper changed while testing'
report=dict(native=str(N),sha256=SHA,fingerprint_version=h.FINGERPRINT_VERSION,helper_sha256=hashlib.sha256((P/'scene_fingerprint.py').read_bytes()).hexdigest(),legacy_core_compatible=True,legacy_owners=len(legacy),deterministic_repeat=True,tests=tests,exact_driver_exception_accepted=True,negative_controls_rejected=rejects,all_mutations_restored=True,full_snapshot_sha256=h.json_digest(base),fresh_reopen_equal_same_helper_version=True,native_saved=False,gpu_used=False,native_unchanged=True,elapsed_seconds=time.time()-start)
(P/'CPU-mutation-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('R3_FINGERPRINT_MUTATION_GUARD_DONE',len(tests),'mutations',len(rejects),'negative controls',round(time.time()-start,2),'seconds',flush=True)
