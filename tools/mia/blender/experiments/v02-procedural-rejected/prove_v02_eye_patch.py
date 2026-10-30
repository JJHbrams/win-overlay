#!/usr/bin/env python3
"""Create one topology-owned, seated eyelid proof for Mia v02."""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--render-dir',required=True)
    return p.parse_args(argv)


def mat(name,color,rough=.55):
    m=bpy.data.materials.new(name); m.diffuse_color=color; m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=color
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough
    return m


def curve_mesh(name,points,material,collection):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=3; c.bevel_depth=.0028; c.bevel_resolution=3
    s=c.splines.new('NURBS'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points): p.co=(*co,1)
    s.order_u=min(3,len(points)); s.use_endpoint_u=True
    o=bpy.data.objects.new(name,c); collection.objects.link(o); c.materials.append(material)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.convert(target='MESH'); o.select_set(False)
    return o


def main():
    a=args(); out=Path(a.output).resolve(); renders=Path(a.render_dir).resolve(); renders.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True); scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    col=bpy.data.collections.new('OneEye_Proof'); scene.collection.children.link(col)
    skin=mat('Skin',(0.58,.40,.38,1)); sclera=mat('Sclera',(.75,.80,.78,1)); iris=mat('Iris',(.20,.31,.33,1)); pupil=mat('Pupil',(.02,.025,.03,1)); lid=mat('LidSkin',(.46,.27,.28,1)); lash=mat('Lash',(.035,.025,.03,1))
    # Curved facial patch: dense UV-sphere surface keeps forehead/cheek behind the globe.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0,.10,0), scale=(.34,.19,.38)); head=bpy.context.object; head.name='FacePatch_CompleteForeheadCheek'; head.data.materials.append(skin); col.objects.link(head); bpy.context.collection.objects.unlink(head)
    # Actual ellipsoid globe, seated into the face surface.
    # The face patch front is y≈-0.09 at the eye line.  Keeping the globe
    # center at -0.03 embeds its front cap at the skin surface instead of
    # projecting a separate eyeball in front of the cheek.
    cx,cy,cz=.0,-.030,.025; rx,ry,rz=.095,.072,.060
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(cx,cy,cz), scale=(rx,ry,rz)); eye=bpy.context.object; eye.name='EyeGlobe_OneSide'; eye.data.materials.append(sclera); col.objects.link(eye); bpy.context.collection.objects.unlink(eye)
    # Iris/pupil are shallow ellipsoid caps embedded on globe front, not free planar decals.
    for name,scale,material,offset in [('Iris',.038,iris,-.071),('Pupil',.016,pupil,-.076)]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=(cx,cy+offset,cz), scale=(scale,.004,scale)); o=bpy.context.object; o.name=name+'_SurfaceCap'; o.data.materials.append(material); col.objects.link(o); bpy.context.collection.objects.unlink(o)
    # Same corner x positions for both lids; y is solved on the globe's front ellipsoid.
    def surface_y(x,z,clear=.0006):
        q=max(0,1-((x-cx)/rx)**2-((z-cz)/rz)**2)
        return cy-ry*math.sqrt(q)-clear
    xs=[-.080,-.060,-.035,0,.035,.060,.080]
    upper=[]; lower=[]
    for x in xs:
        t=abs(x)/.080
        upper_z=cz+.017-.020*(1-t*t) # lowered, flatter upper lid covers iris
        lower_z=cz-.018+.010*(1-t*t)
        upper.append((x,surface_y(x,upper_z),upper_z)); lower.append((x,surface_y(x,lower_z),lower_z))
    upper_obj=curve_mesh('UpperLid_Band_SharedCorners',upper,lid,col)
    lower_obj=curve_mesh('LowerLid_Band_SharedCorners',lower,lid,col)
    # Lash lies on the same seated upper path; no detached glasses arc.
    lash_pts=[(x,y-.0005,z+.0015) for x,y,z in upper]; lash_obj=curve_mesh('UpperLash_Seated',lash_pts,lash,col)
    for o in (upper_obj,lower_obj,lash_obj): o['surface_fit']='ellipsoid front equation, 0.0006m clearance'; o['shared_corner_x']=True
    # Simple lights/camera.
    for name,pos,energy in [('Key',(1,-2,2),500),('Fill',(-1,-1,1),180),('Rim',(1,1,2),250)]:
        d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=2; o=bpy.data.objects.new(name,d); o.location=pos; o.rotation_euler=(Vector((0,-.05,0))-o.location).to_track_quat('-Z','Y').to_euler(); col.objects.link(o)
    d=bpy.data.cameras.new('ProofCamera'); d.type='ORTHO'; d.ortho_scale=.52; cam=bpy.data.objects.new('ProofCamera',d); col.objects.link(cam); scene.camera=cam
    target=Vector((0,-.05,.02))
    for label,yaw in [('front',0),('three_quarter',45),('profile',90)]:
        r=math.radians(yaw); cam.location=target+Vector((math.sin(r)*1.5,-math.cos(r)*1.5,.08)); cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler(); scene.render.filepath=str(renders/(label+'.png')); bpy.ops.render.render(write_still=True)
    out.parent.mkdir(parents=True,exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print({'objects':len(col.objects),'globe_vertices':len(eye.data.vertices),'lid_mesh_vertices':len(upper_obj.data.vertices)+len(lower_obj.data.vertices),'output':str(out)})

if __name__=='__main__': main()
