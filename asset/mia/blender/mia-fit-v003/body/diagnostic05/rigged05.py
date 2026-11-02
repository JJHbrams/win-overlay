"""Rejected05 diagnostic on private original-key/rig copies; never save a scene."""
from pathlib import Path
import hashlib, math, json, sys
import bpy
import numpy as np
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parent.parent
O = Path(__file__).resolve().parent
NAME = 'MIA_v003_DIAGNOSTIC_Rejected05'
RIG = NAME + '_Rig'
KEY = 'Mia.v003.DIAGNOSTIC.Rejected05'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def coordinates(data):
    a = np.empty(len(data) * 3, np.float32)
    data.foreach_get('co', a)
    return a.reshape(-1, 3).astype(np.float64)

def read_surface(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = e.to_mesh()
    try:
        a = coordinates(me.vertices)
        mw = np.array(e.matrix_world)
        a = a @ mw[:3, :3].T + mw[:3, 3]
        return dict(world=a,
                    loops=np.array([q.vertex_index for q in me.loops], np.int32),
                    sizes=np.array([q.loop_total for q in me.polygons], np.int32),
                    materials=np.array([q.material_index for q in me.polygons], np.int32),
                    corner_normals=np.array([q.vector[:] for q in me.corner_normals]),
                    face_normals=np.array([q.normal[:] for q in me.polygons]))
    finally:
        e.to_mesh_clear()

def set_update(ob):
    ob.data.update()
    ob.update_tag(refresh={'DATA'})
    bpy.context.view_layer.update()

def control_world(ob):
    states = [(m, m.show_viewport) for m in ob.modifiers]
    seen_arm = False
    try:
        for m, _ in states:
            if seen_arm:
                m.show_viewport = False
            if m.type == 'ARMATURE':
                seen_arm = True
        bpy.context.view_layer.update()
        return read_surface(ob)['world']
    finally:
        for m, value in states:
            m.show_viewport = value
        bpy.context.view_layer.update()

def smooth(t):
    t = np.clip(t, 0, 1)
    return t*t*t*(10-15*t+6*t*t)

def build(source):
    if NAME in bpy.data.objects:
        raise RuntimeError('A private diagnostic already exists')
    mapping = np.load(P/'inputs/mapping-frame1.npz')
    target = np.load(P/'posed-target/target-05.npz')
    original_rig = next(m.object for m in source.modifiers if m.type == 'ARMATURE')
    col = bpy.data.collections.new(NAME)
    bpy.context.scene.collection.children.link(col)
    rig = original_rig.copy()
    rig.data = original_rig.data.copy()
    rig.name = RIG
    col.objects.link(rig)
    rig.hide_render = True
    ob = source.copy()
    ob.data = source.data.copy()
    ob.name = NAME
    assert ob.data.shape_keys is not source.data.shape_keys
    col.objects.link(ob)
    world = ob.matrix_world.copy()
    if ob.parent is original_rig:
        ob.parent = rig
        ob.matrix_world = world
    arm = next(m for m in ob.modifiers if m.type == 'ARMATURE')
    arm.object = rig
    assert not arm.use_deform_preserve_volume
    bpy.context.view_layer.update()
    # Copying retains the current authored animation/driver state. Arm channels
    # must be free before the isolated pose diagnostic; no original is touched.
    paths = [q.data_path for q in rig.animation_data.drivers] if rig.animation_data else []
    blocked = [q for q in paths if 'UpperArm' in q or 'LowerArm' in q]
    assert not blocked, blocked
    for side in ['L', 'R']:
        for part in ['UpperArm', 'LowerArm']:
            pb = rig.pose.bones['J_Bip_'+side+'_'+part]
            assert not any(c.influence != 0 and not c.mute for c in pb.constraints), pb.name
    q0 = control_world(ob)
    expected = mapping['q0_world']
    assert np.array_equal(q0, expected), ('Private rig q0 mismatch', np.max(np.abs(q0-expected)))
    raw_original = coordinates(ob.data.shape_keys.key_blocks['Basis'].data)
    # Match the exact float32 control coordinates consumed by frozen05, rather
    # than its higher precision construction cache.
    mw = np.array(ob.matrix_world)
    desired = target['target_local'].astype(np.float32).astype(np.float64) @ mw[:3,:3].T + mw[:3,3]
    field = np.einsum('nij,nj->ni', mapping['local_from_world'], desired-q0)
    field[np.linalg.norm(desired-q0,axis=1) == 0] = 0
    key = ob.shape_key_add(name=KEY, from_mix=False)
    key.value = 0.0
    key.data.foreach_set('co', (raw_original+field).astype(np.float32).ravel())
    key.value = 1.0
    set_update(ob)
    errors = []
    # Compensate finite float32 Armature/key arithmetic only; not a form fit.
    # Disjoint protected controls remain exact zero throughout.
    movable = np.linalg.norm(desired-q0,axis=1) > 0
    for _ in range(3):
        actual = control_world(ob)
        residual = desired-actual
        errors.append(float(np.linalg.norm(residual,axis=1).max()))
        adjustment = np.einsum('nij,nj->ni', mapping['local_from_world'], residual)
        adjustment[~movable] = 0
        co = coordinates(key.data)
        key.data.foreach_set('co', (co+adjustment).astype(np.float32).ravel())
        set_update(ob)
    actual = control_world(ob)
    control_error = np.linalg.norm(actual-desired,axis=1)
    assert float(control_error.max()) <= 2e-6, float(control_error.max())
    assert np.array_equal(coordinates(key.data)[3957:], raw_original[3957:])
    # The gate neutralizes only the chest/shoulder/axilla body zone. The original
    # group, original modifier, all rest data and all accepted face weights stay.
    sm = next(m for m in ob.modifiers if m.type == 'SMOOTH')
    group = ob.vertex_groups[sm.vertex_group]
    weights = np.array([next((x.weight for x in v.groups if x.group == group.index),0.) for v in ob.data.vertices])
    q = mapping['q0_world']
    mask = smooth((q[:,2]-1.08)/.05)*smooth((1.425-q[:,2])/.035)*smooth((.28-np.abs(q[:,0]))/.055)
    mask[3957:] = 0
    clonegroup = ob.vertex_groups.new(name=NAME+'_SmoothBodyGate')
    for i, value in enumerate(weights*(1-mask)):
        if value > 0:
            clonegroup.add([i], float(value), 'REPLACE')
    baseline_basis = {b.name:dict(location=b.location.copy(),rotation_mode=b.rotation_mode,
        rotation_euler=b.rotation_euler.copy(),rotation_quaternion=b.rotation_quaternion.copy(),
        rotation_axis_angle=list(b.rotation_axis_angle),scale=b.scale.copy()) for b in rig.pose.bones}
    meta = dict(target_sha256=digest(P/'posed-target/target-05.npz'), mapping_sha256=digest(P/'inputs/mapping-frame1.npz'),
                private_q0_bitexact=True, inverse_control_error_max_mm=float(control_error.max()*1000),
                inverse_iteration_max_mm=[v*1000 for v in errors],
                control_face690_exact=True, original_smooth_group=group.name, diagnostic_smooth_group=clonegroup.name,
                smooth_mask_nonzero=int(np.count_nonzero(mask)), smooth_mask_full=int(np.count_nonzero(mask==1)),
                smooth_mask_world_bounds=[q[mask>0].min(0).tolist(),q[mask>0].max(0).tolist()],
                smooth_face690_weights_exact=True, rig_arm_driver_paths=blocked,
                purpose='Rejected05 pose/operator diagnosis only. Not an anatomy candidate.')
    return dict(object=ob,rig=rig,collection=col,original_smooth_group=group.name,
                diagnostic_smooth_group=clonegroup.name,basis=baseline_basis,metadata=meta,
                smooth_mask=mask,desired_control_world=desired)

def reset_pose(ctx):
    # Restore authored channels, not matrix_basis decomposition (which can
    # introduce float32 quaternion/Euler roundoff even in a private copy).
    for name,state in ctx['basis'].items():
        b=ctx['rig'].pose.bones[name]
        b.rotation_mode=state['rotation_mode'];b.location=state['location']
        b.rotation_euler=state['rotation_euler'];b.rotation_quaternion=state['rotation_quaternion']
        b.rotation_axis_angle=state['rotation_axis_angle'];b.scale=state['scale']
    bpy.context.view_layer.update()

def arm_axes(rig):
    result = {}
    for side,sign in [('L',1),('R',-1)]:
        for part in ['UpperArm','LowerArm']:
            b = rig.pose.bones['J_Bip_'+side+'_'+part]
            head,tail = rig.matrix_world@b.head,rig.matrix_world@b.tail
            d = tail-head
            result[b.name] = dict(head=list(head),tail=list(tail),
                frontal_from_vertical_degrees=math.degrees(math.atan2(sign*d.x,-d.z)),
                depth_degrees=math.degrees(math.atan2(d.y,math.hypot(d.x,d.z))))
    return result

def pose_source_like(ctx):
    reset_pose(ctx)
    rig=ctx['rig']
    # Source skin axes are approximate. These bone targets are explicitly a
    # diagnostic hypothesis, not exact skin/bone landmark correspondence.
    for side,sign in [('L',1),('R',-1)]:
        for part,angle in [('UpperArm',14.),('LowerArm',19.)]:
            b=rig.pose.bones['J_Bip_'+side+'_'+part]
            axes=arm_axes(rig)[b.name]
            change=sign*(axes['frontal_from_vertical_degrees']-angle)
            head=rig.matrix_world@b.head
            transform=Matrix.Translation(head)@Matrix.Rotation(math.radians(change),4,'Y')@Matrix.Translation(-head)
            b.matrix=rig.matrix_world.inverted()@transform@rig.matrix_world@b.matrix
            bpy.context.view_layer.update()

def set_state(ctx,pose,smooth_on):
    if pose=='current': reset_pose(ctx)
    elif pose=='source-like': pose_source_like(ctx)
    else: raise ValueError(pose)
    sm=next(m for m in ctx['object'].modifiers if m.type=='SMOOTH')
    sm.vertex_group=ctx['original_smooth_group'] if smooth_on else ctx['diagnostic_smooth_group']
    bpy.context.view_layer.update()
    return dict(pose=pose,smooth_body_roi_on=smooth_on,arm_axes=arm_axes(ctx['rig']),
                smooth_modifier=dict(name=sm.name,factor=sm.factor,iterations=sm.iterations,vertex_group=sm.vertex_group),
                source_pose_limit='14/19 degree bone-axis hypothesis from approximate visible E2 skin14/19; skin/bone correspondence uncertain.')
