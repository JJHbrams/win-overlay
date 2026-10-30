"""Landmark-designed Mia head with connected skin around two eye apertures.

Authoring geometry, not image projection. The intact anatomy master remains
in the file. A separate render body uses an explicit overlapping neck interface;
this interface is static-modeling evidence, not rigging acceptance.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model_v02_eye_surface import material, mesh_object, eye_material

EYE_Z = 1.525
EYE_Y = -.046
EYE_RX = .030
EYE_RY = .035
N, BANDS = 128, 22
WIDTH = [(1.34, .042), (1.38, .042), (1.405, .037), (1.425, .043),
         (1.445, .064), (1.49, .095), (1.53, .102), (1.59, .103),
         (1.64, .080), (1.675, .025), (1.682, .001)]
FRONT = [(1.34, -.010), (1.38, -.016), (1.415, -.072), (1.435, -.077),
         (1.452, -.079), (1.48, -.077), (1.525, -.081), (1.56, -.083),
         (1.63, -.060), (1.675, .010), (1.682, .025)]
BACK = [(1.34, .065), (1.4, .070), (1.46, .090), (1.53, .120),
        (1.60, .124), (1.65, .100), (1.682, .030)]


def interpolate(table, z):
    def final(value):
        if table is WIDTH or table is BACK:
            t=max(0,min(1,(z-1.55)/.05))
            t=t*t*(3-2*t)
            r=math.sqrt(max(0,1-((z-1.577)/.105)**2))
            target=max(.0001,.105*r) if table is WIDTH else .025+.100*r
            return value*(1-t)+target*t
        return value
    if z <= table[0][0]:
        return table[0][1]
    for (a, va), (b, vb) in zip(table, table[1:]):
        if z <= b:
            t = (z - a) / (b - a)
            index = table.index((a, va))
            slope = (vb - va) / (b - a)
            before = slope if index == 0 else (va - table[index-1][1]) / (a - table[index-1][0])
            after = slope if index + 2 >= len(table) else (table[index+2][1] - vb) / (table[index+2][0] - b)
            ma = 0 if before * slope <= 0 else 2 * before * slope / (before + slope)
            mb = 0 if after * slope <= 0 else 2 * after * slope / (after + slope)
            return final((2*t**3-3*t*t+1)*va + (t**3-2*t*t+t)*(b-a)*ma + (-2*t**3+3*t*t)*vb + (t**3-t*t)*(b-a)*mb)
    return table[-1][1]


def face_y(x, z):
    width = interpolate(WIDTH, z)
    side = min(1, abs(x) / max(.001, width))
    front=interpolate(FRONT,z)
    t=max(0,min(1,(z-1.38)/.05))
    t=t*t*(3-2*t)
    side_center=.033*(1-t)+.025*t
    # Constant side meridian with a vertical tangent where the front meets
    # the rear cranium. The earlier finite-slope edge caused shading ridges.
    y=side_center-(side_center-front)*math.sqrt(max(0,1-side**4))
    y -= .013 * math.exp(-((x / .014) ** 2 + ((z - 1.482) / .016) ** 2))
    y -= .0035 * math.exp(-((x / .012) ** 2 + ((z - 1.511) / .025) ** 2))
    y -= .0018 * math.exp(-((x / .025) ** 4 + ((z - 1.455) / .0028) ** 2))
    y -= .0011 * math.exp(-((x / .024) ** 4 + ((z - 1.449) / .003) ** 2))
    y += .0013 * math.exp(-((x / .004) ** 2 + ((z - 1.465) / .006) ** 2))
    y += .0015 * math.exp(-((x / .010) ** 2 + ((z - 1.473) / .0025) ** 2))
    y -= .002 * max(0,1-abs(x)/.009)*math.exp(-((z-1.482)/.012)**2)
    y += .001 * math.exp(-((x/.023)**4+((z-1.443)/.0025)**2))
    if z > 1.56:
        t = max(0,min(1,(z-1.56)/.035))
        t = t*t*(3-2*t)
        radius = .100*math.sqrt(max(0,1-((z-1.577)/.105)**2))
        spherical = .025-radius*math.sqrt(max(0,1-side*side))
        y = y*(1-t)+spherical*t
    return y


def outer_point(cx, theta):
    dx, dz = math.cos(theta), math.sin(theta)
    sign = 1 if cx > 0 else -1
    def inside(r):
        x, z = cx + r * dx, EYE_Z + r * dz
        return 1.34 <= z <= 1.682 and x * sign >= -1e-10 and abs(x) <= interpolate(WIDTH, z)
    lo, hi = 0, .6
    for _ in range(50):
        mid = (lo + hi) / 2
        if inside(mid):
            lo = mid
        else:
            hi = mid
    return cx + lo * dx, EYE_Z + lo * dz


def make_head():
    skin = material("Mia_skin", (.64, .47, .42))
    coords, constraints = [], []
    # Uniformly sampled silhouette and frontal surface avoid long radial
    # polygons and the pinching they produced in the rejected first patch.
    outer = []
    for sign, indices in ((1, range(141)), (-1, range(140, -1, -1))):
        for j in indices:
            z = 1.34 + (1.682 - 1.34) * j / 140
            outer.append(len(coords))
            coords.append(Vector((sign * interpolate(WIDTH, z), z)))
    for i, a in enumerate(outer):
        constraints.append((a, outer[(i + 1) % len(outer)]))
    eye_loops = []
    for cx in (-.048, .048):
        loop = []
        for i in range(N):
            th = 2 * math.pi * i / N
            loop.append(len(coords))
            coords.append(Vector((cx + .028 * math.cos(th), EYE_Z - .0015*(1 if cx>0 else -1)*math.cos(th) + (.005 if math.sin(th) >= 0 else .011) * math.sin(th))))
        constraints.extend((loop[i], loop[(i + 1) % N]) for i in range(N))
        eye_loops.append(loop)
        for scale in (1.08, 1.20, 1.45, 1.8):
            for i in range(N):
                th = 2 * math.pi * i / N
                coords.append(Vector((cx + .028 * scale * math.cos(th), EYE_Z - .0015*(1 if cx>0 else -1)*math.cos(th) + (.005 if math.sin(th) >= 0 else .011) * scale * math.sin(th))))
    def in_eye(x, z):
        for cx in (-.048,.048):
            u=(x-cx)/.028
            zz=z-EYE_Z+.0015*(1 if cx>0 else -1)*u
            if u*u+(zz/(.005 if zz>=0 else .011))**2<.99999:
                return True
        return False
    for j in range(1, 139):
        z = 1.34 + (1.682 - 1.34) * j / 140
        width = interpolate(WIDTH, z)
        columns = max(3, round(width * 2 / .0028))
        for i in range(1, columns):
            x = -width + 2 * width * i / columns
            if not in_eye(x, z):
                coords.append(Vector((x, z)))
    cv, ce, cf, orig_v, _, _ = delaunay_2d_cdt(coords, constraints, [outer], 1, 1e-7, True)
    lookup = {}
    for out_i, input_ids in enumerate(orig_v):
        for input_i in input_ids:
            lookup[input_i] = out_i
    def skin_y(x, z):
        y = face_y(x, z)
        for cx in (-.048, .048):
            u=(x-cx)/.028
            slope=-.0015*(1 if cx>0 else -1)*u
            v=(z-EYE_Z-slope)/(.005 if z>=EYE_Z+slope else .011)
            radius=math.sqrt(u*u+v*v)
            if radius>=.999 and radius<4:
                rim_x=cx+.028*u/radius
                rim_z=EYE_Z-.0015*(1 if cx>0 else -1)*u/radius+(.005 if v>=0 else .011)*v/radius
                rq=max(0,1-((rim_x-cx)/EYE_RX)**2-((rim_z-EYE_Z)/.030)**2)
                rim_y=EYE_Y-EYE_RY*math.sqrt(rq)-.0009
                distance=math.sqrt((x-rim_x)**2+(z-rim_z)**2)
                t=max(0,min(1,distance/.012))
                t=t*t*(3-2*t)
                y=rim_y*(1-t)+y*t
            q = 1 - ((x-cx)/EYE_RX)**2 - ((z-EYE_Z)/.030)**2
            if q >= 0:
                y = min(y, EYE_Y - EYE_RY * math.sqrt(q) - .0010)
            if abs(u)<1:
                slope=-.0015*(1 if cx>0 else -1)*u
                edge=EYE_Z+slope+.005*math.sqrt(1-u*u)
                d=z-edge
                if 0<d<.010:
                    y-=.0012*math.sin(math.pi*d/.010)*(1-u*u)**2
                low=EYE_Z+slope-.011*math.sqrt(1-u*u)
                d=low-z
                if 0<d<.004:
                    y-=.00025*math.sin(math.pi*d/.004)*(1-u*u)**2
        return y
    vertices = [(p.x, skin_y(p.x, p.y), p.y) for p in cv]
    faces = []
    for face in cf:
        center = sum((cv[i] for i in face), Vector((0, 0))) / len(face)
        if not in_eye(center.x, center.y):
            faces.append(tuple(face))
    previous = [lookup[i] for i in outer]
    base_points = [Vector(vertices[i]) for i in previous]
    for j in range(1, 13):
        angle = j / 12 * math.pi / 2
        ring = []
        for p in base_points:
            x = p.x * math.cos(angle)
            y = p.y * (1 - math.sin(angle)) + interpolate(BACK, p.z) * math.sin(angle)
            ring.append(len(vertices))
            vertices.append((x, y, p.z))
        for i in range(len(ring)):
            q = (i + 1) % len(ring)
            faces.append((previous[i], previous[q], ring[q], ring[i]))
        previous = ring
    head = mesh_object("Mia_Head_ConnectedSkin", vertices, faces, skin)
    bm = bmesh.new()
    bm.from_mesh(head.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-8)
    for v in bm.verts:
        if v.co.z>1.55:
            t=max(0,min(1,(v.co.z-1.55)/.132))
            v.co.x*=1-.055*t*t
            v.co.z=1.55+(v.co.z-1.55)*.92
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(head.data)
    bm.free()
    for p in head.data.polygons:
        p.use_smooth = True
    head["role"] = "landmark_designed_render_head_with_neck_interface"
    head["topology"] = "Connected forehead/temples/cheeks around two apertures; complete cranium and neck"
    head["rig_status"] = "NOT_RIGGED; neck overlap must be validated in motion later"
    # Use original connected first-band positions for two seated lash ribbons.
    dark = material("Mia_lash_brow", (.025, .020, .022))
    for cx in (-.048, .048):
        vs, fs = [], []
        for i in range(N // 2 + 1):
            th = 2 * math.pi * i / N
            slope=-.0015*(1 if cx>0 else -1)*math.cos(th)
            x, z = cx + .028 * math.cos(th), EYE_Z+slope + .005 * math.sin(th)
            p = Vector((x, skin_y(x,z)-.00015, z))
            ox, oz = cx + .0290 * math.cos(th), EYE_Z+slope + .007 * math.sin(th)
            q = Vector((ox, skin_y(ox,oz)-.00015, oz))
            vs.extend((tuple(p), tuple(q)))
            if i:
                k = i * 2
                fs.append((k - 2, k - 1, k + 1, k))
        mesh_object("Mia_UpperLash_" + ("L" if cx > 0 else "R"), vs, fs, dark)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, location=(cx, EYE_Y, EYE_Z))
        eye = bpy.context.object
        eye.name = "Mia_Eye_" + ("L" if cx > 0 else "R")
        eye.scale = (EYE_RX, EYE_RY, .030)
        eye.data.materials.append(eye_material(EYE_RX, .030))
        for p in eye.data.polygons:
            p.use_smooth = True
    return head


def face_details(head):
    tree = BVHTree.FromPolygons([v.co for v in head.data.vertices], [list(p.vertices) for p in head.data.polygons])
    def point(x, z):
        hit, normal, _, _ = tree.ray_cast(Vector((x, -.4, z)), Vector((0, 1, 0)))
        if hit is None:
            raise RuntimeError("No facial skin under detail")
        hit.y -= .00018
        return tuple(hit)
    dark = bpy.data.materials["Mia_lash_brow"]
    for cx in (-.048, .048):
        v, f = [], []
        for i in range(33):
            u = i / 32 * 2 - 1
            x = cx + .027 * u
            z = EYE_Z + .017 + .001 * (1 - u * u) + .002*(1 if cx>0 else -1)*u
            thickness = .0013 * (1 - .65 * abs(u))
            v.extend((point(x, z), point(x, z + thickness)))
            if i:
                k = 2 * i
                f.append((k - 2, k - 1, k + 1, k))
        mesh_object("Mia_Brow_" + ("L" if cx > 0 else "R"), v, f, dark)
        v,f=[],[]
        for i in range(33):
            u=i/32*2-1
            x=cx+.025*u
            z=EYE_Z-.014-.0025*(1-u*u)
            v.extend((point(x,z),point(x,z+.0006*(1-.7*abs(u)))))
            if i:
                k=2*i
                f.append((k-2,k-1,k+1,k))
        mesh_object("Mia_UnderEye_"+("L" if cx>0 else "R"),v,f,material("Mia_under_eye_ash_"+str(cx),(.31,.24,.23)))
    v, f = [], []
    for i in range(41):
        u = i / 40 * 2 - 1
        x = .027 * u
        z = 1.452 + .001 * (1 - u * u)
        v.extend((point(x, z), point(x, z + .0007 * (1 - .6 * abs(u)))))
        if i:
            k = 2 * i
            f.append((k - 2, k - 1, k + 1, k))
    mesh_object("Mia_MouthSeam_on_skin", v, f, material("Mia_muted_mouth", (.22, .11, .11)))


def fit_neck(head, body, mask):
    mask.show_viewport = False
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    inverse = body.matrix_world.inverted()
    for v in head.data.vertices:
        if v.co.z >= 1.388:
            continue
        center = Vector((0,.033,v.co.z))
        direction = Vector((v.co.x, v.co.y-.033, 0)).normalized()
        origin = center+direction*.20
        local_o = inverse@origin
        local_d = (inverse.to_3x3()@(-direction)).normalized()
        hit, normal, _, _ = tree.ray_cast(local_o, local_d)
        if hit is None:
            continue
        target = body.matrix_world@hit-direction*.0007
        t = max(0,min(1,(v.co.z-1.34)/.048))
        t = t*t*(3-2*t)
        v.co = target.lerp(v.co,t)
    mask.show_viewport = True
    head.data.update()


def ears(original):
    # Preserve the CC0 ear surface from the untouched Basis. Root cuts are
    # embedded in the new head, rather than retaining a second facial shell.
    basis = original.data.shape_keys.key_blocks[0]
    skin = bpy.data.materials["Mia_skin"]
    objects=[]
    for sign in (-1,1):
        vertices, faces, mapping = [],[],{}
        for p in original.data.polygons:
            points=[original.matrix_world@basis.data[i].co for i in p.vertices]
            c=sum(points,Vector())/len(points)
            if c.x*sign>.112 and 1.465<c.z<1.582 and -.02<c.y<.095:
                face=[]
                for source_i,point in zip(p.vertices,points):
                    if source_i not in mapping:
                        q=point.copy()
                        q.x*=.79
                        q.z=1.525+(q.z-1.525)*.80
                        mapping[source_i]=len(vertices)
                        vertices.append(tuple(q))
                    face.append(mapping[source_i])
                faces.append(face)
        ear=mesh_object("Mia_Ear_"+("L" if sign>0 else "R"),vertices,faces,skin)
        bm=bmesh.new()
        bm.from_mesh(ear.data)
        bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(ear.data)
        bm.free()
        ear["source"]="CC0 full Basis ear; root overlap with authored head, not a second face"
        objects.append(ear)
    return objects


def fuse_ears(head,ears):
    def boundary(mesh):
        bm=bmesh.new()
        bm.from_mesh(mesh)
        count=sum(e.is_boundary for e in bm.edges)
        bm.free()
        return count
    expected=boundary(head.data)
    for ear in ears:
        modifier=head.modifiers.new("Anatomical_ear_root_union","BOOLEAN")
        modifier.operation="UNION"
        modifier.solver="EXACT"
        modifier.object=ear
        bpy.context.view_layer.objects.active=head
        head.select_set(True)
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        if boundary(head.data)!=expected:
            raise RuntimeError("Ear union changed intentional eye aperture boundaries")
        bpy.data.objects.remove(ear,do_unlink=True)
    bm=bmesh.new()
    bm.from_mesh(head.data)
    bmesh.ops.triangulate(bm,faces=[p for p in bm.faces if len(p.verts)>4])
    targets=[]
    for v in bm.verts:
        x,y,z=v.co
        weight=.14*math.exp(-(((abs(x)-.102)/.014)**2+((z-1.525)/.045)**2+((y-.025)/.065)**2))
        if weight>.001:
            targets.append((v,weight))
    for _ in range(24):
        updates=[]
        for v,weight in targets:
            neighbors=[e.other_vert(v) for e in v.link_edges]
            if neighbors:
                average=sum((p.co for p in neighbors),Vector())/len(neighbors)
                updates.append((v,v.co.lerp(average,weight)))
        for v,co in updates:
            v.co=co
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(head.data)
    bm.free()
    for p in head.data.polygons:
        p.use_smooth=True
    head["ear_roots"]="Exact local unions; intentional eye aperture boundary count unchanged"


def sculpt_integrated_ears(head):
    bm=bmesh.new()
    bm.from_mesh(head.data)
    selected=[]
    for p in bm.faces:
        c=p.calc_center_median()
        if abs(c.x)>.075 and -.012<c.y<.09 and 1.475<c.z<1.58:
            selected.extend(p.edges)
    bmesh.ops.subdivide_edges(bm,edges=list(set(selected)),cuts=2,use_grid_fill=True)
    for v in bm.verts:
        x,y,z=v.co
        if abs(x)<.075:
            continue
        u=(y-.035)/.024
        w=(z-1.525)/.034
        radius=math.sqrt(u*u+w*w)
        if radius>1.3:
            continue
        fade=max(0,1-(radius/1.3)**2)**2
        body=.012
        opening=max(0,min(1,(u+.80)/.50))
        opening=opening*opening*(3-2*opening)
        helix=.015*math.exp(-((radius-.73)/.20)**2)*opening
        concha=-.004*math.exp(-(radius/.33)**2)
        lobule=.004*math.exp(-((u-.10)/.5)**2-((w+.80)/.26)**2)
        antihelix=.003*math.exp(-((u+.05)/.18)**2-((w-.1)/.6)**2)
        v.co.x+=math.copysign((body+helix+concha+lobule+antihelix)*fade,x)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(head.data)
    bm.free()
    for p in head.data.polygons:
        p.use_smooth=True
    head["ear_roots"]="Continuous side-head surface sculpt; no appended cap, Boolean, root cut or separate ear shell"


def assign_owners(head):
    col=bpy.data.collections.new("Anatomy_Render")
    bpy.context.scene.collection.children.link(col)
    for ob in list(bpy.context.scene.objects):
        if ob.type=="MESH" and not ob.hide_render:
            for previous in list(ob.users_collection):
                previous.objects.unlink(ob)
            col.objects.link(ob)
            ob["owner"]="Anatomy"
    head["role"]="complete_connected_mia_render_anatomy"
    col["stage"]="ANATOMY; not an artistic acceptance flag"


def toon_skin(head):
    m=bpy.data.materials.new("Mia_illustrated_skin_geometry_shading")
    m.use_nodes=True
    nt=m.node_tree
    nt.nodes.clear()
    diffuse=nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs['Color'].default_value=(.8,.8,.8,1)
    rgb=nt.nodes.new("ShaderNodeShaderToRGB")
    nt.links.new(diffuse.outputs[0],rgb.inputs[0])
    ramp=nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation='CONSTANT'
    ramp.color_ramp.elements[0].position=.12
    ramp.color_ramp.elements[0].color=(.38,.25,.24,1)
    ramp.color_ramp.elements[1].position=.32
    ramp.color_ramp.elements[1].color=(.80,.65,.58,1)
    mid=ramp.color_ramp.elements.new(.21)
    mid.color=(.63,.45,.40,1)
    nt.links.new(rgb.outputs[0],ramp.inputs[0])
    fresnel=nt.nodes.new('ShaderNodeFresnel')
    fresnel.inputs['IOR'].default_value=1.45
    edge=nt.nodes.new('ShaderNodeValToRGB')
    edge.color_ramp.elements[0].position=.38
    edge.color_ramp.elements[0].color=(1,1,1,1)
    edge.color_ramp.elements[1].position=.68
    edge.color_ramp.elements[1].color=(.12,.09,.10,1)
    nt.links.new(fresnel.outputs[0],edge.inputs[0])
    mix=nt.nodes.new('ShaderNodeMixRGB')
    mix.blend_type='MULTIPLY'
    mix.inputs[0].default_value=1
    nt.links.new(ramp.outputs[0],mix.inputs[1])
    nt.links.new(edge.outputs[0],mix.inputs[2])
    emission=nt.nodes.new('ShaderNodeEmission')
    nt.links.new(mix.outputs[0],emission.inputs[0])
    output=nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(emission.outputs[0],output.inputs[0])
    head.data.materials.clear()
    head.data.materials.append(m)
    head["shading"]="Geometry-dependent cel shading and Fresnel edge tint; no projected portrait or image texture"


def bake_body_interface(body, mask):
    mask.show_viewport=False
    bpy.context.view_layer.update()
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    vertices=[body.matrix_world@v.co for v in mesh.vertices]
    faces=[list(p.vertices) for p in mesh.polygons]
    baked=bpy.data.meshes.new("Mia_body_render_exact_neck_interface")
    baked.from_pydata(vertices,[],faces)
    evaluated.to_mesh_clear()
    body.modifiers.clear()
    body.parent=None
    body.matrix_world.identity()
    body.data=baked
    bm=bmesh.new()
    bm.from_mesh(baked)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,
                          plane_co=(0,0,1.345),plane_no=(0,0,1),clear_outer=True,clear_inner=False)
    smooth_band(bm,1.12,1.33,8,.18)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(baked)
    bm.free()
    baked.materials.append(bpy.data.materials["Mia_body_skin"])
    for p in baked.polygons:
        p.use_smooth=True
    body["interface"]="Evaluated render copy only: exact 1.365m neck plane, full original master retained, authored neck overlaps below plane"


def smooth_band(bm,low,high,iterations,factor):
    selected=[]
    for v in bm.verts:
        if low<v.co.z<high and not v.is_boundary:
            t=(v.co.z-low)/(high-low)
            selected.append((v,math.sin(math.pi*t)**2*factor))
    for _ in range(iterations):
        updates=[]
        for v,weight in selected:
            neighbors=[e.other_vert(v) for e in v.link_edges]
            if neighbors:
                average=sum((p.co for p in neighbors),Vector())/len(neighbors)
                updates.append((v,v.co.lerp(average,weight)))
        for v,co in updates:
            v.co=co


def connect_anatomy(head,body):
    # Explicit replacement interface, on render copies only. Bridge a 20mm
    # neck interval with actual faces, rather than overlapping skin shells.
    bh=bmesh.new()
    bh.from_mesh(head.data)
    bmesh.ops.bisect_plane(bh,geom=list(bh.verts)+list(bh.edges)+list(bh.faces),dist=1e-6,
                          plane_co=(0,0,1.365),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
    bh.to_mesh(head.data)
    bh.free()
    vertices=[tuple(v.co) for v in head.data.vertices]
    faces=[list(p.vertices) for p in head.data.polygons]
    off=len(vertices)
    vertices.extend(tuple(v.co) for v in body.data.vertices)
    faces.extend([i+off for i in p.vertices] for p in body.data.polygons)
    combined=mesh_object("Mia_Anatomy_Render",vertices,faces,bpy.data.materials["Mia_skin"])
    bm=bmesh.new()
    bm.from_mesh(combined.data)
    neck_edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-1.345)<1e-5 or abs(v.co.z-1.365)<1e-5 for v in e.verts)]
    result=bmesh.ops.bridge_loops(bm,edges=neck_edges,use_pairs=True)
    if not result['faces']:
        raise RuntimeError("Neck loop bridge produced no actual faces")
    smooth_band(bm,1.28,1.44,45,.35)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    unexpected=[e for e in bm.edges if e.is_boundary and (sum(v.co.z for v in e.verts)/2)<1.48]
    if unexpected:
        raise RuntimeError("Unexpected lower anatomy boundary edges after neck join: %d"%len(unexpected))
    bm.to_mesh(combined.data)
    bm.free()
    for p in combined.data.polygons:
        p.use_smooth=True
    combined["neck_interface"]="Continuous mesh; head and body boundary loops connected by actual bridge faces; full source retained separately"
    combined["rig_status"]="static modeling only; deformation topology and rigging not accepted"
    bpy.data.objects.remove(head,do_unlink=True)
    bpy.data.objects.remove(body,do_unlink=True)
    return combined


def render_keys(dest):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    for ob in list(scene.objects):
        if ob.type == "LIGHT":
            bpy.data.objects.remove(ob, do_unlink=True)
    for name, pos, energy in (("Key", (1, -2, 3), 170), ("Fill", (-1.5, -1.5, 2), 65), ("Rim", (1, 2, 2.5), 110)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.size = energy, 2
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        ob.location = pos
        ob.rotation_euler = (Vector((0, 0, 1.4)) - ob.location).to_track_quat("-Z", "Y").to_euler()
    scene.view_settings.view_transform = "AgX"
    data = bpy.data.cameras.new("Model_review_camera")
    data.type, data.ortho_scale = "ORTHO", .40
    camera = bpy.data.objects.new("Model_review_camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    original = {o: list(o.data.materials) for o in scene.objects if o.type == "MESH" and not o.hide_render}
    for mode in ("saved", "clay"):
        if mode == "clay":
            clay = material("Head_review_clay", (.32, .32, .32))
            for ob in original:
                ob.data.materials.clear()
                ob.data.materials.append(clay)
        for yaw in (0, 45, 90, 180, 315):
            a = math.radians(yaw)
            target = Vector((0, .01, 1.52))
            camera.location = target + Vector((math.sin(a), -math.cos(a), .02))
            camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(dest / f"{mode}_{yaw:03d}.png")
            bpy.ops.render.render(write_still=True)
    for ob, mats in original.items():
        ob.data.materials.clear()
        for m in mats:
            ob.data.materials.append(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body-input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--toon",action="store_true",help="Optional geometry-dependent cel material; clay review remains separate")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = Path(args.body_input).resolve()
    dest = Path(args.output_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    original = bpy.data.objects["BodyHead_Master"]
    for ob in bpy.data.collections["Anatomy"].objects:
        ob.hide_render = True
    body = original.copy()
    body.data = original.data.copy()
    body.name = "Mia_Body_Render"
    body.hide_render = False
    bpy.context.scene.collection.objects.link(body)
    # Remove the rejected cranial deformation from the render body's neck;
    # body sculpt below the neck remains the separately reviewed torso field.
    if body.data.shape_keys:
        basis = body.data.shape_keys.key_blocks[0]
        sculpt = body.data.shape_keys.key_blocks[1]
        for i, p in enumerate(basis.data):
            z = (body.matrix_world @ p.co).z
            t = max(0, min(1, (z-1.25)/.05))
            t = t*t*(3-2*t)
            sculpt.data[i].co = sculpt.data[i].co.lerp(p.co, t)
    group = body.vertex_groups.new(name="RENDER_BODY_BELOW_HEAD_INTERFACE")
    for v in body.data.vertices:
        # Group is based on retained Basis coordinates: the complete authoring
        # master is not deleted. New neck overlaps the 1.365m render boundary.
        if (body.matrix_world @ v.co).z < 1.365:
            group.add([v.index], 1, "REPLACE")
    mask = body.modifiers.new("Explicit_replacement_head_interface", "MASK")
    mask.vertex_group = group.name
    body.data.materials.clear()
    body.data.materials.append(material("Mia_body_skin", (.64, .47, .42)))
    head = make_head()
    fit_neck(head,body,mask)
    bake_body_interface(body,mask)
    head=connect_anatomy(head,body)
    sculpt_integrated_ears(head)
    face_details(head)
    assign_owners(head)
    if args.toon:
        toon_skin(head)
    render_keys(dest)
    output = dest / "Mia_Landmark_Anatomy.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    report = {"source_sha_before": before, "source_sha_after": hashlib.sha256(source.read_bytes()).hexdigest(),
              "head_vertices": len(head.data.vertices), "head_faces": len(head.data.polygons),
              "status": "REQUIRES_ARTISTIC_REVIEW", "neck_interface": "Explicit render-body mask with overlapping modeled neck; complete master retained; unrigged"}
    (dest / "inventory.json").write_text(json.dumps(report, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
