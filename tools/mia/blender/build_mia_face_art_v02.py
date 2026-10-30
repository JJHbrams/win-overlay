"""Apply an owned, non-destructive Mia face-art study to an anatomy checkpoint.

Blender 5.2: --background --python this.py -- --input a.blend --output b.blend
--render-dir proof --report proof/report.json. Original keys, UVs and source
images remain intact. The new skin image replaces sample-specific painted
brows/lips, while the actual eye-rim alpha is derived from its source texture.
"""

import argparse
import hashlib
import json
import math
import os
import struct
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree


FACE_NAME = "Mia_Face_AnimeTopology"
BODY_NAME = "Mia_Body_Anatomy_Skin"
ART_KEY = "MIA_FaceArt_OwnedBrowPlacement"
IMAGE_NAME = "Mia_FaceArt_UV_Pigment"
PROPORTION_KEY = "MIA_FaceArt_EyeProportion"
NEUTRAL_CLOSE = .45
UNDER_EYE_STRENGTH = .38


def cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--render-dir", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--resolution", type=int, default=768)
    p.add_argument("--neutral-close", type=float, default=NEUTRAL_CLOSE)
    p.add_argument("--under-eye-strength", type=float, default=UNDER_EYE_STRENGTH)
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if not 0 <= args.neutral_close <= 1 or not 0 <= args.under_eye_strength <= 1:
        p.error("Neutral closure and pigment strength must be between 0 and 1")
    return args


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(obj, keys=None):
    h = hashlib.sha256()
    mesh = obj.data
    for v in mesh.vertices:
        h.update(struct.pack("<3f", *v.co))
    for poly in mesh.polygons:
        h.update(struct.pack("<%dI" % len(poly.vertices), *poly.vertices))
    for layer in mesh.uv_layers:
        h.update(layer.name.encode())
        for item in layer.data:
            h.update(struct.pack("<2f", *item.uv))
    if mesh.shape_keys:
        for key in mesh.shape_keys.key_blocks:
            if keys is not None and key.name not in keys:
                continue
            h.update(key.name.encode())
            for point in key.data:
                h.update(struct.pack("<3f", *point.co))
    return h.hexdigest()


def image_hashes():
    result = {}
    for im in bpy.data.images:
        if im.name.startswith("F00_"):
            pixels = np.empty(len(im.pixels), dtype=np.float32)
            im.pixels.foreach_get(pixels)
            result[im.name] = hashlib.sha256(pixels.tobytes()).hexdigest()
    return result


def material_ids(face, slot):
    return sorted({i for p in face.data.polygons if p.material_index == slot for i in p.vertices})


def source_image(material):
    node = material.node_tree.nodes.get("Mtoon1BaseColorTexture.Image")
    if not node or not node.image:
        raise RuntimeError("No owned base-color image for " + material.name)
    return node.image


def pose(face, proof="neutral"):
    blocks = face.data.shape_keys.key_blocks
    for k in blocks:
        if any(part in k.name for part in ("Fcl_EYE_", "Fcl_MTH_", "Fcl_BRW_")):
            k.value = 0.0
    values = {
        "Fcl_EYE_Close": NEUTRAL_CLOSE,
        "Fcl_EYE_Sorrow": .10,
        "Fcl_BRW_Angry": .06,
        "Fcl_MTH_Angry": .18,
        "Fcl_MTH_Neutral": .12,
    }
    if proof == "blink":
        values["Fcl_EYE_Close"] = 1.0
        values["Fcl_EYE_Sorrow"] = 0.0
    if proof == "mouth_a":
        for k in blocks:
            if "Fcl_MTH_" in k.name:
                k.value = 0.0
        values = {k: v for k, v in values.items() if "MTH" not in k}
        values["Fcl_MTH_A"] = 1.0
    for name, value in values.items():
        matches = [k for k in blocks if k.name.endswith(name)]
        if len(matches) != 1:
            raise RuntimeError("Ambiguous source key " + name)
        matches[0].value = value
    bpy.context.view_layer.update()


def add_brow_corrective(face):
    key = face.shape_key_add(name=ART_KEY, from_mix=False)
    basis=face.data.shape_keys.key_blocks[0]
    for i,p in enumerate(basis.data):key.data[i].co=p.co
    inverse = face.matrix_world.inverted().to_3x3()
    affected = []
    for index in material_ids(face, 4):
        point = face.matrix_world @ basis.data[index].co
        outward = max(-1.0, min(1.0, (abs(point.x) - .044) / .034))
        # Place the actual ink card, not the now-removed sample brow paint.
        # Compress its arch about the source card's middle before lowering it.
        delta = Vector((0, -.0003, -.029 + .0018 * outward + .48*(1.602-point.z)))
        key.data[index].co += inverse @ delta
        affected.append(index)
    key.value = 1.0
    # Source pigment below the broad gray eyelid patch was partly buried in the
    # skin. Fit the owned card to actual front skin clearance before thinning it.
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();evaluated=face.evaluated_get(deps)
    mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    world=[face.matrix_world@v.co for v in mesh.vertices]
    polys=[list(p.vertices) for p in mesh.polygons if p.material_index==7]
    tree=BVHTree.FromPolygons(world,polys)
    ink_clearance=[]
    for index in material_ids(face,2):
        point=world[index]
        hit=tree.ray_cast(Vector((point.x,-.4,point.z)),Vector((0,1,0)),.7)
        shift=-.0005
        if hit[0] is not None:
            shift=min(shift,hit[0].y-.0006-point.y)
        shift=max(-.012,shift)
        key.data[index].co+=inverse@Vector((0,shift,0))
        ink_clearance.append(shift)
    evaluated.to_mesh_clear()
    return {"name": key.name, "affected_brow_vertices": len(affected), "placement": "Lowered 29mm with a 52% vertical card scale and restrained outward slope", "eyeline_vertices_clearance_adjusted":len(ink_clearance),"eyeline_y_clearance_delta_range":[min(ink_clearance),max(ink_clearance)]}


def add_eye_proportion(face):
    """Widen the orbital opening and its owned parts together; keep source keys."""
    key=face.shape_key_add(name=PROPORTION_KEY,from_mix=False)
    basis=face.data.shape_keys.key_blocks[0]
    for i,p in enumerate(basis.data):key.data[i].co=p.co
    inverse=face.matrix_world.inverted().to_3x3()
    ownership={i:set() for i in range(len(face.data.vertices))}
    for p in face.data.polygons:
        for i in p.vertices:ownership[i].add(p.material_index)
    eye_ids=material_ids(face,1)
    centers={}
    for side in (-1,1):
        points=[face.matrix_world@basis.data[i].co for i in eye_ids if (face.matrix_world@basis.data[i].co).x*side>0]
        centers[side]=Vector(((min(p.x for p in points)+max(p.x for p in points))*.5,0,(min(p.z for p in points)+max(p.z for p in points))*.5))
    counts={"orbital_skin":0,"eye_parts":0,"iris":0}
    for i,v in enumerate(basis.data):
        p=face.matrix_world@v.co;side=-1 if p.x<0 else 1;c=centers[side]
        roles=ownership[i]
        delta=Vector()
        if roles & {1,2,3}:
            delta.x=.14*(p.x-c.x);delta.z=-.045*(p.z-c.z);counts["eye_parts"]+=1
        elif roles & {5,6,8}:
            delta.x=-.12*(p.x-c.x);delta.z=-.12*(p.z-c.z);counts["iris"]+=1
        elif 7 in roles:
            radius=math.sqrt(((p.x-c.x)/.056)**2+((p.z-c.z)/.047)**2)
            weight=1.0 if radius<.72 else max(0,1-(radius-.72)/.55)
            if p.y<-.025 and weight>0:
                delta.x=.14*(p.x-c.x)*weight;delta.z=-.045*(p.z-c.z)*weight;counts["orbital_skin"]+=1
        if delta.length:
            key.data[i].co+=inverse@delta
    key.value=1
    return {"name":key.name,"counts":counts,"eye_horizontal_scale":1.14,"iris_scale":.88,"orbital_skin_falloff":"full inside .72 ellipse, smooth to zero by1.27; front skin only"}


def build_upper_rim(face, uv_paths):
    """Trace the authored upper-lid pigment in unchanged UVs, with exact morphs."""
    mesh=face.data;mw=face.matrix_world;inverse=mw.inverted();blocks=list(mesh.shape_keys.key_blocks)
    basis=blocks[0]
    # Select the two largest connected upper-line components (76 vertices each).
    polys=[p for p in mesh.polygons if p.material_index==2]
    ids={v for p in polys for v in p.vertices};adj={v:set() for v in ids}
    for p in polys:
        vs=list(p.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):adj[a].add(b);adj[b].add(a)
    remaining=set(ids);components=[]
    while remaining:
        todo=[remaining.pop()];group=set(todo)
        while todo:
            v=todo.pop()
            for n in adj[v]&remaining:remaining.remove(n);group.add(n);todo.append(n)
        components.append(group)
    upper=set().union(*sorted(components,key=len,reverse=True)[:2])
    uv=mesh.uv_layers.active.data;triangles=[]
    for p in polys:
        if not all(i in upper for i in p.vertices):continue
        ls=list(p.loop_indices)
        for j in range(1,len(ls)-1):
            loops=(ls[0],ls[j],ls[j+1]);coords=[Vector(uv[i].uv) for i in loops]
            indices=[mesh.loops[i].vertex_index for i in loops]
            triangles.append((coords,indices))
    def lookup(point):
        x,y=point
        for coords,indices in triangles:
            (ax,ay),(bx,by),(cx,cy)=coords
            den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-10:continue
            w0=((by-cy)*(x-cx)+(cx-bx)*(y-cy))/den
            w1=((cy-ay)*(x-cx)+(ax-cx)*(y-cy))/den;w2=1-w0-w1
            if min(w0,w1,w2)>=-1e-5:return indices,(w0,w1,w2)
        return None
    paths=[]
    for path in uv_paths:
        mapped=[]
        for u,unused_v in path:
            crossings=[]
            for tri,indices in triangles:
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    if min(a.x,b.x)-1e-7<=u<=max(a.x,b.x)+1e-7 and abs(b.x-a.x)>1e-8:
                        t=(u-a.x)/(b.x-a.x)
                        crossings.append(a.y+(b.y-a.y)*t)
            if not crossings:continue
            # The image's dark lower mark lies outside parts of the upper card's
            # actual UV island. Trace its real lower border instead of drawing
            # onto texture pixels that the geometry never samples.
            low,high=min(crossings),max(crossings)
            point=(u,min(high-.0001,low+.003))
            data=lookup(point)
            if data is not None:mapped.append((point,data))
        if len(mapped)<10:raise RuntimeError('Upper-lid UV trace does not map to authored component')
        paths.append(mapped)
    deps=bpy.context.evaluated_depsgraph_get();evaluated=face.evaluated_get(deps)
    em=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    world=[mw@v.co for v in em.vertices]
    tree=BVHTree.FromPolygons(world,[list(p.vertices) for p in em.polygons if p.material_index==7])
    offsets=[]
    for path in paths:
        row=[]
        for point,(indices,weights) in path:
            co=sum((world[i]*w for i,w in zip(indices,weights)),Vector())
            hit=tree.ray_cast(Vector((co.x,-.4,co.z)),Vector((0,1,0)),.7)[0]
            delta=-.0008 if hit is None else min(-.0008,hit.y-.0008-co.y)
            row.append(max(-.014,delta))
        offsets.append(row)
    evaluated.to_mesh_clear()
    def coords(key):
        result=[]
        for side,path in enumerate(paths):
            for j,(uv_point,(indices,weights)) in enumerate(path):
                point=mw@sum((key.data[i].co*w for i,w in zip(indices,weights)),Vector())
                point.y+=offsets[side][j]
                t=j/(len(path)-1);half=.00062*(.35+.65*math.sin(math.pi*t)**.4)
                result.extend((inverse@(point+Vector((0,0,-half))),inverse@(point+Vector((0,0,half)))))
        return result
    basis_coords=coords(basis);faces=[];start=0
    for path in paths:
        for j in range(len(path)-1):
            a=start+j*2;faces.append((a,a+2,a+3,a+1))
        start+=len(path)*2
    inkmesh=bpy.data.meshes.new('MiaArt_UpperRim_MESH');inkmesh.from_pydata(basis_coords,[],faces);inkmesh.update()
    obj=bpy.data.objects.new('MiaArt_UpperRim',inkmesh);bpy.context.scene.collection.objects.link(obj)
    obj.parent=face.parent;obj.matrix_parent_inverse=face.matrix_parent_inverse.copy();obj.matrix_basis=face.matrix_basis.copy()
    obj['part_role']='FACE_ART_UPPER_RIM';obj['source_owner']=face.name
    obj['method']='Authored upper-line UV pigment traced barycentrically; exact source-key linear morph drivers'
    mat,nodes,links=new_nodes('Mia_FaceArt_UpperRim_Ink')
    emit=nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(.018,.016,.021,1)
    out=nodes.new('ShaderNodeOutputMaterial');links.new(emit.outputs[0],out.inputs['Surface']);inkmesh.materials.append(mat)
    for sourcekey in blocks:
        target=obj.shape_key_add(name=sourcekey.name,from_mix=False)
        points=coords(sourcekey)
        for i,point in enumerate(points):target.data[i].co=point
        if sourcekey!=basis:
            driver=target.driver_add('value').driver
            var=driver.variables.new();var.name='source_value';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=face.data.shape_keys
            var.targets[0].data_path='key_blocks['+json.dumps(sourcekey.name)+'].value';driver.expression='source_value'
    groups={};side_weights={"negative_X":set(),"positive_X":set()};bound_index=0
    for path in paths:
        for uv_point,(indices,barycentric) in path:
            weights={}
            for source_index,coefficient in zip(indices,barycentric):
                for entry in mesh.vertices[source_index].groups:
                    weights[entry.group]=weights.get(entry.group,0)+entry.weight*coefficient
            weights={i:max(0,w) for i,w in weights.items() if w>1e-7}
            total=sum(weights.values())
            assert total>1e-5,"Upper-rim UV binding has no source deformation weights"
            normalized={i:w/total for i,w in weights.items()}
            assert abs(sum(normalized.values())-1)<1e-6
            for group_index,value in normalized.items():
                if group_index not in groups:
                    groups[group_index]=obj.vertex_groups.new(name=face.vertex_groups[group_index].name)
                groups[group_index].add([bound_index,bound_index+1],value,'REPLACE')
            point=mw@sum((basis.data[i].co*w for i,w in zip(indices,barycentric)),Vector())
            side="negative_X" if point.x<0 else "positive_X"
            significant={face.vertex_groups[i].name for i,w in normalized.items() if w>.01}
            side_weights[side].update(significant)
            assert len(significant)==1,"Expected side-specific source EyeSet binding"
            assert max(normalized.values())>.999,"EyeSet binding was averaged across both eyes"
            bound_index+=2
    assert bound_index==len(basis_coords)
    assert all(len(names)==1 for names in side_weights.values()),"One physical eye has mixed EyeSet owners"
    assert side_weights["negative_X"]!=side_weights["positive_X"],"Both ribbons use the same EyeSet owner"
    for mod in face.modifiers:
        if mod.type=='ARMATURE':
            copy=obj.modifiers.new('MiaArt_shared_Armature','ARMATURE');copy.object=mod.object;copy.use_deform_preserve_volume=mod.use_deform_preserve_volume
    pose(face,'blink')
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();ef=face.evaluated_get(deps);fm=ef.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    fw=[mw@v.co for v in fm.vertices];skin=BVHTree.FromPolygons(fw,[list(p.vertices) for p in fm.polygons if p.material_index==7])
    eo=obj.evaluated_get(deps);om=eo.to_mesh(preserve_all_data_layers=True,depsgraph=deps)
    line_world=[eo.matrix_world@v.co for v in om.vertices]
    blink_delta=[]
    for point in line_world:
        hit=skin.ray_cast(Vector((point.x,-.4,point.z)),Vector((0,1,0)),.7)[0]
        blink_delta.append(0 if hit is None else max(-.025,min(0,hit.y-.0009-point.y)))
    ef.to_mesh_clear();eo.to_mesh_clear()
    blink=obj.shape_key_add(name='MIA_UpperRim_BlinkClearance',from_mix=False)
    for i,p in enumerate(obj.data.shape_keys.key_blocks[0].data):blink.data[i].co=p.co
    for i,delta in enumerate(blink_delta):blink.data[i].co+=inverse.to_3x3()@Vector((0,delta,0))
    driver=blink.driver_add('value').driver
    var=driver.variables.new();var.name='closed';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=face.data.shape_keys
    close=next(k.name for k in face.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'))
    var.targets[0].data_path='key_blocks['+json.dumps(close)+'].value';driver.expression='max(0,min(1,(closed-.56)/.44))'
    pose(face)
    return {'object':obj.name,'vertices':len(basis_coords),'faces':len(faces),'morphs':len(blocks)+1,'source_morph_drivers':len(blocks)-1,'part_role':obj['part_role'],'half_width_m':.00062,'source_uv_trace':[[(float(u),float(v)) for (u,v),data in path] for path in paths],'forward_clearance_delta_range':[min(min(row) for row in offsets),max(max(row) for row in offsets)],'blink_clearance_delta_range':[min(blink_delta),max(blink_delta)],'blink_clearance_driver':'clamp((Close-.56)/.44,0,1)','vertex_weight_binding':'exact source upper-line UV triangle barycentric weights; no cross-eye averaging','EyeSet_distribution':{side:sorted(names) for side,names in side_weights.items()},'per_point_source_EyeSet_asserted':True}


def new_nodes(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat, mat.node_tree.nodes, mat.node_tree.links


def fit_rim_image(original, path):
    """Fit one continuous thin stroke to the authored alpha/dark rim in each column."""
    source = source_image(original)
    w,h=source.size[:]
    rgba=np.empty(w*h*4,dtype=np.float32);source.pixels.foreach_get(rgba);rgba=rgba.reshape((h,w,4))
    lum=rgba[:,:,:3].mean(axis=2)
    v=(np.arange(h)+.5)/h
    expected=np.exp(-((v-.56)/.16)**2)
    score=rgba[:,:,3]*(1-np.clip(lum,0,1))**8*expected[:,None]
    score[(v<.35)|(v>.82),:]=0
    indices=np.argmax(score,axis=0).astype(float)
    valid=score.max(axis=0)>.17
    # Independent eye islands; never bridge a UV gap or the central nose interval.
    centers=indices.copy();uv_paths=[]
    for start,end in ((0,w//2),(w//2,w)):
        known=np.flatnonzero(valid[start:end])+start
        if len(known)<4:
            raise RuntimeError("Cannot fit source dark eye rim")
        first,last=known[0],known[-1]
        cols=np.arange(first,last+1)
        filled=np.interp(cols,known,indices[known])
        padded=np.pad(filled,(3,3),mode="edge")
        med=np.array([np.median(padded[j:j+7]) for j in range(len(filled))])
        centers[cols]=np.convolve(np.pad(med,(2,2),mode="edge"),np.array([1,2,3,2,1])/9,mode="valid")
        valid[first:last+1]=True
        sample_x=np.linspace(first+2,last-2,29)
        uv_paths.append([((float(x)+.5)/w,(float(np.interp(x,np.arange(w),centers))+.5)/h) for x in sample_x])
    distance=np.abs(np.arange(h)[:,None]-centers[None,:])
    alpha=np.clip((2.1-distance)/.8,0,1)*valid[None,:]
    pixels=np.empty_like(rgba);pixels[:,:,:3]=(.025,.023,.029);pixels[:,:,3]=alpha
    image=bpy.data.images.new("Mia_FaceArt_ThinRimUV",width=w,height=h,alpha=True)
    image.colorspace_settings.name="Non-Color";image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw=path;image.file_format="PNG";image.save();image.pack()
    with open(path+".uv.json","w") as stream:json.dump(uv_paths,stream)
    return image,uv_paths


def owned_ink(original, name, mode, fitted_rim=None):
    """Keep alpha/UV, tint ink; gray painted lid mass is not a black line."""
    mat, nodes, links = new_nodes(name)
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Original_owned_alpha_and_pigment"
    tex.image = fitted_rim if mode=="rim" else source_image(original)
    tex.interpolation = "Linear"
    rgb = nodes.new("ShaderNodeRGBToBW")
    links.new(tex.outputs["Color"], rgb.inputs["Color"])
    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    links.new(tex.outputs["Alpha"], mul.inputs[0])
    if mode == "rim":
        mul.inputs[1].default_value=1.0
    elif mode=="brow":
        threshold=nodes.new("ShaderNodeMath");threshold.operation="GREATER_THAN";threshold.inputs[1].default_value=.40
        links.new(tex.outputs["Alpha"],threshold.inputs[0]);links.new(threshold.outputs[0],mul.inputs[0]);mul.inputs[1].default_value=1
    else:
        mul.inputs[1].default_value = 0.0 if mode == "lash" else .82
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (.025, .023, .029, 1)
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(mul.outputs[0], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs[0], out.inputs["Surface"])
    mat.surface_render_method = "DITHERED"
    mat.use_transparency_overlap = False
    mat.use_backface_culling = original.use_backface_culling
    mat["source_image"] = tex.image.name
    mat["source_ownership"] = mode
    return mat


def lower_eye_contours(face, mesh):
    """Fit the visible Skin/White boundary, not the larger concealed white card."""
    result = []
    ids = material_ids(face, 1)
    all_points = np.array([tuple(face.matrix_world @ mesh.vertices[i].co) for i in ids])
    vertices = [face.matrix_world @ vertex.co for vertex in mesh.vertices]
    surface = [poly for poly in mesh.polygons if poly.material_index in (1, 7)]
    tree = BVHTree.FromPolygons(vertices, [list(poly.vertices) for poly in surface])
    for side in (-1, 1):
        points = all_points[all_points[:, 0] * side > 0]
        lo, hi = points[:, 0].min(), points[:, 0].max()
        samples = []
        for x in np.linspace(lo, hi, 25):
            for z in np.arange(points[:, 2].min() - .004, points[:, 2].max() + .004, .0002):
                hit = tree.ray_cast(Vector((float(x), -.5, float(z))), Vector((0, 1, 0)), 1.0)
                if hit[0] is not None and surface[hit[2]].material_index == 1:
                    samples.append((float(x), float(z)))
                    break
        if len(samples) < 5:
            raise RuntimeError("Could not resolve the visible lower eyelid boundary")
        center = (samples[0][0] + samples[-1][0]) * .5
        half_width = (samples[-1][0] - samples[0][0]) * .5
        poly = np.polyfit([(p[0]-center)/half_width for p in samples], [p[1] for p in samples], 2)
        result.append({"center_x": float(center), "half_width": float(half_width),
                       "lower_z_poly": [float(x) for x in poly],
                       "method": "front first-visible EyeWhite/Skin boundary, 0.2mm ray grid",
                       "visible_boundary_samples": samples})
    return result


def pigment(world, contours):
    """Paint in source surface coordinates, rasterized onto its unchanged UVs."""
    x, y, z = world
    color = np.empty((*x.shape, 4), dtype=np.float32)
    color[..., :] = (.83, .73, .70, 1.0)
    for contour in contours:
        u = (x - contour["center_x"]) / (contour["half_width"] * 1.02)
        poly = contour["lower_z_poly"]
        rim = poly[0] * u*u + poly[1] * u + poly[2]
        below = rim - z
        side = np.maximum(0, 1-u*u)
        vertical = np.clip(below / .006, 0, 1)
        strength = np.exp(-np.maximum(0,below)/.0022) * side * UNDER_EYE_STRENGTH
        strength *= (below > 0) & (below < .006) & (np.abs(u) < 1) & (y < -.025)
        color[..., :3] = color[..., :3]*(1-strength[..., None]) + np.array((.27, .208, .247))*strength[..., None]
        # One restrained lower-lid crease, distinct from a wide gray cheek patch.
        crease_distance = np.abs(below - .0007)
        crease = np.clip(1-crease_distance/.0003, 0, 1)*side*.13
        crease *= (np.abs(u)>.58) & (np.abs(u)<.90) & (y<-.025)
        color[..., :3] = color[..., :3]*(1-crease[..., None])+np.array((.17,.13,.16))*crease[...,None]
    # A dry, near-horizontal closed-lip line. Skin UV follows actual mouth shape keys.
    width = .0175
    q = np.abs((x+.00048)/width)
    line_z = 1.5002 - .0007*q*q
    ink = np.clip(1-np.abs(z-line_z)/.00062, 0, 1)
    ink *= np.clip((1-q)*5,0,1) * (q<1) * (y<-.08)
    color[..., :3] = color[..., :3]*(1-ink[...,None])+np.array((.048,.037,.044))*ink[...,None]
    return color


def bake_skin(face, path):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = face.evaluated_get(deps)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
    contours = lower_eye_contours(face, mesh)
    size = 1024
    pixels = np.empty((size,size,4), dtype=np.float32)
    pixels[:,:,:] = (.83,.73,.70,1)
    uv = mesh.uv_layers.active.data
    for poly in mesh.polygons:
        if poly.material_index != 7:
            continue
        loops = list(poly.loop_indices)
        for j in range(1,len(loops)-1):
            ls = (loops[0],loops[j],loops[j+1])
            coords = np.array([uv[i].uv[:] for i in ls])
            positions = np.array([tuple(face.matrix_world @ mesh.vertices[mesh.loops[i].vertex_index].co) for i in ls])
            low = np.maximum(0,np.floor(coords.min(axis=0)*size).astype(int))
            high = np.minimum(size-1,np.ceil(coords.max(axis=0)*size).astype(int))
            if np.any(high<low):
                continue
            ax,ay=coords[0];bx,by=coords[1];cx,cy=coords[2]
            den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy)
            if abs(den)<1e-10:
                continue
            xx,yy=np.meshgrid((np.arange(low[0],high[0]+1)+.5)/size,(np.arange(low[1],high[1]+1)+.5)/size)
            w0=((by-cy)*(xx-cx)+(cx-bx)*(yy-cy))/den
            w1=((cy-ay)*(xx-cx)+(ax-cx)*(yy-cy))/den
            w2=1-w0-w1
            mask=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7)
            world=positions[0,:,None,None]*w0+positions[1,:,None,None]*w1+positions[2,:,None,None]*w2
            tile=pixels[low[1]:high[1]+1,low[0]:high[0]+1]
            painted=pigment(world,contours)
            tile[mask]=painted[mask]
    evaluated.to_mesh_clear()
    image=bpy.data.images.new(IMAGE_NAME,width=size,height=size,alpha=True)
    image.colorspace_settings.name="Non-Color"
    image.pixels.foreach_set(pixels.ravel())
    image.filepath_raw=path
    image.file_format="PNG"
    image.save()
    image.pack()
    return image,contours


def skin_material(image=None, body_source=None):
    mat,nodes,links=new_nodes("Mia_FaceArt_CoolPaperBodySkin" if body_source else "Mia_FaceArt_CoolPaperSkin")
    if image:
        tex=nodes.new("ShaderNodeTexImage");tex.image=image;tex.interpolation="Linear"
        pigment_output=tex.outputs["Color"]
    else:
        color=nodes.new("ShaderNodeRGB");color.outputs[0].default_value=(.83,.73,.70,1)
        pigment_output=color.outputs[0]
    geometry=nodes.new("ShaderNodeNewGeometry")
    dot=nodes.new("ShaderNodeVectorMath");dot.operation="DOT_PRODUCT"
    dot.inputs[1].default_value=Vector((-.30,-.65,.70)).normalized()
    links.new(geometry.outputs["Normal"],dot.inputs[0])
    remap=nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value=-.4;remap.inputs["From Max"].default_value=.9
    links.new(dot.outputs["Value"],remap.inputs["Value"])
    ramp=nodes.new("ShaderNodeValToRGB");ramp.color_ramp.interpolation="EASE"
    ramp.color_ramp.elements[0].position=.30;ramp.color_ramp.elements[0].color=(.965,.95,.96,1)
    ramp.color_ramp.elements[1].position=.70;ramp.color_ramp.elements[1].color=(.99,.975,.975,1)
    links.new(remap.outputs["Result"],ramp.inputs["Fac"])
    multiply=nodes.new("ShaderNodeMixRGB");multiply.blend_type="MULTIPLY";multiply.inputs[0].default_value=1
    links.new(pigment_output,multiply.inputs[1]);links.new(ramp.outputs["Color"],multiply.inputs[2])
    emission=nodes.new("ShaderNodeEmission");links.new(multiply.outputs["Color"],emission.inputs["Color"])
    out=nodes.new("ShaderNodeOutputMaterial")
    if body_source:
        source=nodes.new("ShaderNodeTexImage");source.image=source_image(body_source)
        threshold=nodes.new("ShaderNodeMath");threshold.operation="GREATER_THAN";threshold.inputs[1].default_value=.5
        links.new(source.outputs["Alpha"],threshold.inputs[0])
        transparent=nodes.new("ShaderNodeBsdfTransparent");mix=nodes.new("ShaderNodeMixShader")
        links.new(threshold.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2])
        links.new(mix.outputs[0],out.inputs["Surface"]);mat.surface_render_method="DITHERED"
        mat.use_backface_culling=body_source.use_backface_culling
        mat["source_alpha_image"]=source.image.name
    else:links.new(emission.outputs[0],out.inputs["Surface"])
    mat["owned_pigment_image"]=image.name if image else "uniform matched complexion, original Body alpha preserved"
    mat["rendering_note"]="Unlit pigment with normal-dependent restrained cool tone; no specular skin highlight"
    return mat


def camera_setup(resolution):
    scene=bpy.context.scene
    camera=bpy.data.objects.get("MIA_REVIEW_CAMERA")
    if not camera:
        data=bpy.data.cameras.new("MIA_FACE_ART_CAMERA");camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera)
    camera.data.type="ORTHO";camera.data.ortho_scale=.285;scene.camera=camera
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=scene.render.resolution_y=resolution;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="Standard"
    return camera


def aim(camera,angle):
    radians=math.radians(angle)
    target=Vector((0,-.015,1.579))
    camera.location=target+Vector((.7*math.sin(radians),-.7*math.cos(radians),.005))
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()


def main():
    global NEUTRAL_CLOSE, UNDER_EYE_STRENGTH
    a=cli();source=os.path.abspath(a.input);output=os.path.abspath(a.output)
    NEUTRAL_CLOSE = a.neutral_close
    UNDER_EYE_STRENGTH = a.under_eye_strength
    if source==output:
        raise RuntimeError("Input overwrite is forbidden")
    os.makedirs(a.render_dir,exist_ok=True);os.makedirs(os.path.dirname(output),exist_ok=True)
    before_sha=sha(source);bpy.ops.wm.open_mainfile(filepath=source)
    face=bpy.data.objects[FACE_NAME];body=bpy.data.objects[BODY_NAME]
    names=[key.name for key in face.data.shape_keys.key_blocks]
    if len(names)!=42 or ART_KEY in names or bpy.data.images.get(IMAGE_NAME):
        raise RuntimeError("Expected unstyled 42-key source face")
    original_face=fingerprint(face,names);original_body=fingerprint(body);original_images=image_hashes()
    original_materials=[m.name for m in face.data.materials]
    pose(face)
    proportion=add_eye_proportion(face)
    corrective=add_brow_corrective(face)
    allowed={PROPORTION_KEY:set().union(*(set(material_ids(face,i)) for i in (1,2,3,5,6,7,8))),ART_KEY:set(material_ids(face,2))|set(material_ids(face,4))}
    ownership_report={}
    for key_name,indices in allowed.items():
        key=face.data.shape_keys.key_blocks[key_name];basis=face.data.shape_keys.key_blocks[0]
        changed={i for i,p in enumerate(key.data) if (p.co-basis.data[i].co).length>1e-7}
        assert changed<=indices,"Corrective escaped explicit material ownership"
        ownership_report[key_name]={"changed_vertices":len(changed),"outside_owned_vertices":0,"basis_coordinates_explicitly_initialized":True}
    source_materials=list(face.data.materials)
    rim_path=os.path.abspath(os.path.join(a.render_dir,"Mia_FaceArt_ThinRimUV.png"))
    rim_image,rim_uv_paths=fit_rim_image(source_materials[2],rim_path)
    face.data.materials[2]=owned_ink(source_materials[2],"Mia_FaceArt_ThinDarkEyeRim","rim",rim_image)
    face.data.materials[3]=owned_ink(source_materials[3],"Mia_FaceArt_RestrainedLash","lash")
    face.data.materials[4]=owned_ink(source_materials[4],"Mia_FaceArt_LowGraphiteBrow","brow")
    texture_path=os.path.abspath(os.path.join(a.render_dir,"Mia_FaceArt_UV_Pigment.png"))
    skin_image,contours=bake_skin(face,texture_path)
    face.data.materials[7]=skin_material(skin_image)
    original_body_materials=[m.name for m in body.data.materials]
    body.data.materials[0]=skin_material(body_source=body.data.materials[0])
    upper_rim=build_upper_rim(face,rim_uv_paths)
    # The new owned physical line replaces these source paint cards visually.
    face.data.materials[2]=owned_ink(source_materials[2],"Mia_FaceArt_SourceRim_Transparent","lash")
    camera=camera_setup(a.resolution)
    pose(face);aim(camera,0)
    selected_neutral={key.name:key.value for key in face.data.shape_keys.key_blocks}
    bpy.ops.wm.save_as_mainfile(filepath=output)
    proofs=[]
    armature=next(mod.object for mod in face.modifiers if mod.type=="ARMATURE" and mod.object)
    eye_bones=[armature.pose.bones[name] for name in ("J_Adj_L_FaceEye","J_Adj_R_FaceEye")]
    eye_rest={pb.name:(pb.matrix_basis.copy(),pb.rotation_mode) for pb in eye_bones}
    for proof in ("neutral","blink","mouth_a","gaze_left"):
        pose(face,"neutral" if proof=="gaze_left" else proof)
        if proof=="gaze_left":
            for pb in eye_bones:
                axis=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,1))
                pb.rotation_mode="QUATERNION";pb.rotation_quaternion=Quaternion(axis.normalized(),math.radians(12))
            bpy.context.view_layer.update()
        angles=(0,35,90) if proof=="neutral" else (0,35)
        for angle in angles:
            aim(camera,angle)
            path=os.path.abspath(os.path.join(a.render_dir,"face_"+proof+"_y%03d.png"%angle))
            bpy.context.scene.render.filepath=path;bpy.ops.render.render(write_still=True)
            proofs.append({"pose":proof,"yaw":angle,"path":path,"sha256":sha(path)})
        for pb in eye_bones:
            matrix,mode=eye_rest[pb.name];pb.matrix_basis=matrix;pb.rotation_mode=mode
        bpy.context.view_layer.update()
    pose(face);aim(camera,0)
    neutral={key.name:key.value for key in face.data.shape_keys.key_blocks}
    assert neutral==selected_neutral,"Proof loop did not restore selected neutral"
    eye_pose_restored=all(max(abs(pb.matrix_basis[i][j]-eye_rest[pb.name][0][i][j]) for i in range(4) for j in range(4))<1e-6 for pb in eye_bones)
    assert eye_pose_restored,"Proof loop did not restore eye-bone pose"
    assert all(key.value==0 for key in face.data.shape_keys.key_blocks if key.name.endswith("Fcl_MTH_A"))
    assert original_face==fingerprint(face,names),"Original facial topology/keys/UV changed"
    assert original_body==fingerprint(body),"Body changed"
    assert original_images==image_hashes(),"Source packed texture pixels changed"
    assert sha(source)==before_sha,"Source file changed"
    bpy.ops.wm.save_as_mainfile(filepath=output)
    report={
        "status":"FACE_ART_CANDIDATE_REQUIRES_REFERENCE_REVIEW",
        "input":source,"input_sha256_before":before_sha,"input_sha256_after":sha(source),
        "output":output,"output_sha256":sha(output),
        "builder_sha256":sha(__file__),
        "look_parameters":{"neutral_close":NEUTRAL_CLOSE,"under_eye_strength":UNDER_EYE_STRENGTH},
        "original_face_fingerprint":original_face,"face_fingerprint_after":fingerprint(face,names),
        "original_body_fingerprint":original_body,"body_fingerprint_after":fingerprint(body),
        "original_shape_key_count":len(names),"original_shape_key_names":names,
        "added_corrective":corrective,"eye_proportion_corrective":proportion,"upper_rim":upper_rim,"source_uv_and_key_coordinates_preserved":True,
        "corrective_ownership":ownership_report,"gaze_proof":{"bones":[pb.name for pb in eye_bones],"world_z_degrees":12,"pose_restored":eye_pose_restored},
        "source_images_unchanged":True,"original_materials":original_materials,
        "original_body_materials":original_body_materials,"matched_body_material":body.data.materials[0].name,
        "owned_materials":[face.data.materials[i].name for i in (2,3,4,7)],
        "pigment_texture":{"path":texture_path,"sha256":sha(texture_path),"packed":bool(skin_image.packed_file),"size":list(skin_image.size)},
        "thin_rim_texture":{"path":rim_path,"sha256":sha(rim_path),"packed":bool(rim_image.packed_file),"size":list(rim_image.size),"role":"Diagnostic alpha/UV calibration only; final visible upper line is the owned morph-driven ribbon"},
        "eye_lower_contours":contours,"neutral_values_restored":neutral,"proofs":proofs,
        "limitations":["Hair framing must be reviewed separately; this source is bald.","Painted closed-lip ink follows skin UV during mouth keys; open-mouth style/corner continuity still requires visual acceptance.","This changes owned materials, two facial correctives and a morph-driven upper-rim helper; final likeness, complete expression coverage and final rig remain separate acceptance gates."]}
    os.makedirs(os.path.dirname(os.path.abspath(a.report)),exist_ok=True)
    with open(a.report,"w",encoding="utf-8",newline="\n") as stream:
        json.dump(report,stream,indent=2);stream.write("\n")
    print("MIA_FACE_ART_COMPLETE="+a.report)


if __name__=="__main__":
    main()
