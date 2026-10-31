"""World-space QA pose controls; never save the opened native."""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector


def evaluated_frame(rig, bone):
    bpy.context.view_layer.update()
    evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    posed=evaluated.pose.bones[bone.name]
    return evaluated.matrix_world @ posed.matrix, evaluated.matrix_world @ posed.head, evaluated.matrix_world @ posed.tail


def rotate_world(rig, bone, quaternion):
    before,head,tail=evaluated_frame(rig,bone)
    requested=Matrix.Translation(head) @ quaternion.to_matrix().to_4x4() @ Matrix.Translation(-head) @ before
    bone.matrix=rig.matrix_world.inverted() @ requested
    after,new_head,new_tail=evaluated_frame(rig,bone)
    actual=(after.to_quaternion() @ before.to_quaternion().inverted()).normalized()
    if actual.w<0:actual.negate()
    axis,angle=actual.to_axis_angle()
    error=actual.rotation_difference(quaternion).angle
    if error>math.pi:error=2*math.pi-error
    assert error<1e-4, ('world rotation mismatch',bone.name,error)
    assert (new_head-head).length<1e-5, ('head pivot moved',bone.name)
    return {'space':'WORLD','actual_delta_axis':list(axis),'actual_delta_angle_rad':angle,'quaternion_error_rad':error,'pivot_error_m':(new_head-head).length,'head_world_before':list(head),'tail_world_before':list(tail),'tail_world_after':list(new_tail)}


def yaw_world(rig,bone,radians):
    result=rotate_world(rig,bone,Quaternion(Vector((0,0,1)),radians))
    axis=Vector(result['actual_delta_axis'])
    assert abs(axis.z)>1-1e-5, ('yaw axis is not world Z',list(axis))
    signed=result['actual_delta_angle_rad']*(1 if axis.z>=0 else -1)
    assert abs(signed-radians)<1e-4, ('yaw angle mismatch',signed,radians)
    result.update(requested_world_axis=[0,0,1],requested_angle_rad=radians,actual_signed_yaw_rad=signed)
    return result


def arm_forward_world(rig,bone,minimum_m=.05):
    _,head,tail=evaluated_frame(rig,bone)
    baseline=(tail-head).normalized()
    front=Vector((0,-1,0))
    target=(baseline+front*.9).normalized()
    result=rotate_world(rig,bone,baseline.rotation_difference(target))
    movement=(Vector(result['tail_world_after'])-tail).dot(front)
    assert movement>=minimum_m, ('arm did not move forward',movement)
    result.update(front_world_axis=list(front),tail_forward_delta_m=movement,minimum_forward_delta_m=minimum_m,baseline_arm_direction=list(baseline),target_arm_direction=list(target))
    return result
