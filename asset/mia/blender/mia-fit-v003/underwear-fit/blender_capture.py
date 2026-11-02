"""Optional current-scene CPU capture. Never opens/saves/renders or edits owner."""
import bpy
import numpy as np
from mathutils import Matrix, Vector


def capture_surface(current_object, uv_layer='MIA_V002_UnderwearUV'):
    dg=bpy.context.evaluated_depsgraph_get();ev=current_object.evaluated_get(dg)
    me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
    try:
        me.calc_loop_triangles()
        if uv_layer not in me.uv_layers:raise ValueError('Required actual loop UV layer missing: '+uv_layer)
        uv=me.uv_layers[uv_layer]
        return {'world':np.asarray([list(ev.matrix_world@v.co) for v in me.vertices]),
                'triangles':np.asarray([t.vertices[:] for t in me.loop_triangles],dtype=np.int64),
                'triangle_uv':np.asarray([[uv.data[i].uv[:] for i in t.loops] for t in me.loop_triangles]),
                'triangle_materials':np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles]),
                'uv_layer':uv_layer,'owner':current_object.name,'frame':bpy.context.scene.frame_current,
                'uv_layers':[u.name for u in me.uv_layers]}
    finally:ev.to_mesh_clear()


def actual_camera_frame(record, validation_points=None):
    """Recover Blender's actual frame from recorded ORTHO settings on private IDs."""
    c=record.get('camera',record)
    if c['projection']!='ORTHO':raise ValueError('ORTHO only')
    scene=data=ob=None
    try:
        scene=bpy.data.scenes.new('_MIA_UV_CAPTURE_SCENE')
        scene.render.resolution_x,scene.render.resolution_y=c['resolution']
        scene.render.pixel_aspect_x,scene.render.pixel_aspect_y=c['pixel_aspect']
        data=bpy.data.cameras.new('_MIA_UV_CAPTURE_CAMERA');data.type='ORTHO';data.ortho_scale=c['ortho_scale']
        data.clip_start=c['clip_start'];data.clip_end=c['clip_end']
        ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.matrix_world=Matrix(c['matrix'])
        result=dict(c);result['view_frame_local']=[list(v) for v in data.view_frame(scene=scene)]
        if validation_points is not None:
            from bpy_extras.object_utils import world_to_camera_view
            from surface_seating import world_to_pixel
            w,h=c['resolution']
            official=[]
            for p in validation_points:
                q=world_to_camera_view(scene,ob,Vector(p))
                official.append([q.x*w-.5,(1-q.y)*h-.5])
            result['actual_blender_projection_max_error_px']=float(np.linalg.norm(
                world_to_pixel(result,validation_points)-np.asarray(official),axis=1).max())
        return result
    finally:
        if ob is not None:bpy.data.objects.remove(ob,do_unlink=True)
        if data is not None and data.users==0:bpy.data.cameras.remove(data)
        if scene is not None:bpy.data.scenes.remove(scene)
