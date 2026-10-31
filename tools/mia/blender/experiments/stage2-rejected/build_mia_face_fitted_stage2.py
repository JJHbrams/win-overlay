"""REJECTED facial fitting experiment. Not a Mia production baseline.

This is an evaluated facial study, not an art approval. The generated mixed
surface remains an immutable reference. Skin, scalp, eyes and hair have separate
owners; no garment or body source is sculpted together with the face.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mesh_signature(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in ob.data.polygons:
        h.update(struct.pack('<%dI' % len(p.vertices), *p.vertices))
    for uv in ob.data.uv_layers:
        for v in uv.data:
            h.update(struct.pack('<2f', *v.uv))
    return h.hexdigest()


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def emit(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    e = n.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    o = n.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(e.outputs[0], o.inputs['Surface'])
    return m


def alpha_material(original, name, color):
    m = emit(name, color)
    n, links = m.node_tree.nodes, m.node_tree.links
    e = next(x for x in n if x.type == 'EMISSION')
    out = next(x for x in n if x.type == 'OUTPUT_MATERIAL')
    image = next((x.image for x in original.node_tree.nodes if x.type == 'TEX_IMAGE' and x.image and 'BaseColor' in x.name), None)
    if image is None:
        image = next((x.image for x in original.node_tree.nodes if x.type == 'TEX_IMAGE' and x.image), None)
    if image:
        tex = n.new('ShaderNodeTexImage')
        tex.image = image
        tr = n.new('ShaderNodeBsdfTransparent')
        mix = n.new('ShaderNodeMixShader')
        links.new(tex.outputs['Alpha'], mix.inputs[0])
        links.new(tr.outputs[0], mix.inputs[1])
        links.new(e.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs['Surface'])
        m.surface_render_method = 'DITHERED'
        m.use_transparency_overlap = False
    return m


def split(src, ids, dest, name, mat=None, keys=True):
    used = sorted({v for i in ids for v in src.data.polygons[i].vertices})
    remap = {v: j for j, v in enumerate(used)}
    me = bpy.data.meshes.new(name + '_MESH')
    me.from_pydata([src.data.vertices[v].co[:] for v in used], [], [[remap[v] for v in src.data.polygons[i].vertices] for i in ids])
    for old in src.data.uv_layers:
        uv = me.uv_layers.new(name=old.name)
        for newi, oldi in enumerate(ids):
            for a, b in zip(me.polygons[newi].loop_indices, src.data.polygons[oldi].loop_indices):
                uv.data[a].uv = old.data[b].uv
    ob = bpy.data.objects.new(name, me)
    dest.objects.link(ob)
    ob.matrix_world = src.matrix_world.copy()
    if mat:
        me.materials.append(mat)
    else:
        for m in src.data.materials:
            me.materials.append(m)
        for a, b in zip(me.polygons, ids):
            a.material_index = src.data.polygons[b].material_index
    for p in me.polygons:
        p.use_smooth = True
    if keys and src.data.shape_keys:
        for sk in src.data.shape_keys.key_blocks:
            key = ob.shape_key_add(name=sk.name, from_mix=False)
            for j, i in enumerate(used):
                key.data[j].co = sk.data[i].co
    ob['source_vertices'] = used
    ob['source_polygons'] = ids
    return ob


CANONICAL_ROTATION = None


def canonical_copy(src, dest, name):
    # Material landmarks prove the source face points +Y, while Mia points -Y.
    # Explicitly evaluate an active copy before reading its transform.
    ob = src.copy()
    ob.data = src.data.copy()
    dest.objects.link(ob)
    ob.hide_viewport = ob.hide_render = False
    ob.hide_set(False)
    ob.parent = None
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    bpy.context.view_layer.update()
    world = ob.matrix_world.copy()
    global CANONICAL_ROTATION
    if CANONICAL_ROTATION is None:
        eye_ids=sorted({v for p in ob.data.polygons if p.material_index==1 for v in p.vertices})
        eye_y=sum((world@ob.data.vertices[i].co).y for i in eye_ids)/len(eye_ids)
        CANONICAL_ROTATION=Matrix.Rotation(math.pi,4,'Z') if eye_y>0 else Matrix.Identity(4)
        print('SOURCE_FRAME',list(world), 'eye_y',eye_y,'rotate_again',eye_y>0)
    transform = CANONICAL_ROTATION @ world
    mesh_points=[v.co.copy() for v in ob.data.vertices]
    key_points={k.name:[v.co.copy() for v in k.data] for k in ob.data.shape_keys.key_blocks} if ob.data.shape_keys else {}
    if ob.data.shape_keys:
        for key in ob.data.shape_keys.key_blocks:
            for v,q in zip(key.data,key_points[key.name]):
                v.co = transform @ q
    for v,q in zip(ob.data.vertices,mesh_points):
        v.co = transform @ q
    ob.matrix_world = Matrix.Identity(4)
    ob.name = name
    if ob.data.shape_keys:
        ob.data.shape_keys.animation_data_clear()
        for key in ob.data.shape_keys.key_blocks:
            key.value = 0
    return ob


class LandmarkWarp:
    def __init__(self, source, target):
        self.src = np.asarray(source)
        dst = np.asarray(target)
        # An affine term and smooth 3-D radial interpolation; exact landmarks are
        # measured on the topology template and the source skin, not hair bounds.
        r = np.linalg.norm(self.src[:, None] - self.src[None, :], axis=2)
        n = len(source)
        P = np.column_stack((np.ones(n), self.src))
        A = np.block([[r + np.eye(n) * 1e-8, P], [P.T, np.zeros((4, 4))]])
        self.coef = np.linalg.solve(A, np.vstack((dst - self.src, np.zeros((4, 3)))))

    def __call__(self, points):
        points = np.asarray(points)
        r = np.linalg.norm(points[:, None] - self.src[None, :], axis=2)
        P = np.column_stack((np.ones(len(points)), points))
        return points + np.column_stack((r, P)) @ self.coef


def source_colors(src):
    image = next(n.image for n in src.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
    w, h = image.size
    px = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    uv = src.data.uv_layers.active
    rgb, centers = [], []
    for p in src.data.polygons:
        t = sum((uv.data[i].uv for i in p.loop_indices), Vector((0, 0))) / p.loop_total
        rgb.append(px[min(h-1, max(0, int(t.y*h))), min(w-1, max(0, int(t.x*w))), :3])
        centers.append(tuple(src.matrix_world @ p.center))
    return np.array(rgb), np.array(centers)


def feature_points(face, slot):
    ids = sorted({i for p in face.data.polygons if p.material_index == slot for i in p.vertices})
    return np.array([face.data.vertices[i].co[:] for i in ids])


def build_warp(face, body, warm_points):
    skin = feature_points(face, 7)
    white = feature_points(face, 1)
    mouth = feature_points(face, 0)
    src, dst, labels = [], [], []

    def add(label, p, q):
        src.append(tuple(p)); dst.append(tuple(q)); labels.append(label)

    chin = skin[np.argmin(skin[:, 2])]
    nose_candidates = skin[(abs(skin[:, 0]) < .015) & (skin[:, 2] > 1.51) & (skin[:, 2] < 1.56)]
    nose = nose_candidates[np.argmin(nose_candidates[:, 1])]
    target_nose = warm_points[(abs(warm_points[:, 0]) < .025) & (warm_points[:, 2] > 1.46) & (warm_points[:, 2] < 1.49)]
    target_nose = target_nose[np.argmin(target_nose[:, 1])]
    target_chin = warm_points[(abs(warm_points[:, 0]) < .02) & (warm_points[:, 2] > 1.403) & (warm_points[:, 2] < 1.425) & (warm_points[:, 1] < -.07)]
    target_chin = target_chin[np.argmin(target_chin[:, 2])]
    add('chin', chin, (0, target_chin[1], target_chin[2]))
    add('nose_tip', nose, (0, target_nose[1], target_nose[2]))
    mouth_center = mouth.mean(axis=0)
    add('mouth_center', mouth_center, (0, -.111, 1.448))
    for side in (-1, 1):
        eye = white[white[:, 0] * side > 0].mean(axis=0)
        add('eye_center_' + str(side), eye, (side*.062, -.106, 1.516))
        for off, delta in [(-.030, -.028), (.030, .028)]:
            p = eye + np.array((off, .002, 0))
            add('orbital_' + str(side) + '_' + str(off), p, (side*.062+delta, -.102, 1.516 + .001*side*off/.03))
        add('jaw_' + str(side), (side*.071, -.034, 1.490), (side*.072, -.067, 1.445))
        add('cheek_' + str(side), (side*.096, -.030, 1.550), (side*.107, -.068, 1.502))
        add('temple_' + str(side), (side*.098, .005, 1.605), (side*.112, -.029, 1.574))
        add('ear_' + str(side), (side*.106, .005, 1.566), (side*.125, -.005, 1.513))
        add('rear_' + str(side), (side*.070, .075, 1.610), (side*.084, .074, 1.607))
    add('forehead', (0, -.060, 1.650), (0, -.105, 1.627))
    add('crown', (0, .010, 1.710), (0, .025, 1.710))
    add('occiput', (0, .113, 1.600), (0, .113, 1.596))
    for side in (-1, 1):
        add('neck_' + str(side), (side*.045, 0, 1.420), (side*.045, -.008, 1.365))
        add('neckbase_' + str(side), (side*.055, .005, 1.360), (side*.055, .005, 1.330))
        add('shoulder_anchor_' + str(side), (side*.22, 0, 1.300), (side*.22, 0, 1.300))
    warp = LandmarkWarp(src, dst)
    residual = np.linalg.norm(warp(src)-np.asarray(dst), axis=1)
    return warp, [{'name': n, 'template_world': p, 'design_target': q, 'residual_m': float(e)} for n, p, q, e in zip(labels, src, dst, residual)]


def aim(cam, target):
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat('-Z', 'Y').to_euler()


def render(scene, cam, out, name, yaw, override=None):
    target = Vector((0, -.025, 1.555))
    rad = math.radians(yaw)
    cam.location = target + Vector((.95*math.sin(rad), -.95*math.cos(rad), .02))
    aim(cam, target)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = .48
    old = scene.view_layers[0].material_override
    scene.view_layers[0].material_override = override
    scene.render.filepath = str(out/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = old
    return {'name': name, 'yaw': yaw, 'matrix': [list(v) for v in cam.matrix_world], 'ortho_scale': cam.data.ortho_scale}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--proofs', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    source, out = Path(a.input).resolve(), Path(a.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    source_hash = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.name = 'Mia_Stage2_FittedFace_REVIEW'
    scene['stage_status'] = 'FACIAL_FITTING_STUDY; ART_NOTAPPROVED; CHARACTER_INCOMPLETE'
    originals = {o.name: mesh_signature(o) for o in scene.objects if o.type == 'MESH'}
    dest = collection('MIA_STAGE2_FACIAL_COMPONENTS')
    archive = collection('MIA_STAGE2_FIT_WORKSPACE_HIDDEN')
    haircol = collection('MIA_STAGE2_HAIR_COMPONENTS')
    face = canonical_copy(bpy.data.objects['Face'], dest, 'MIA_FITTED_FACE_WORKING')
    body_source=bpy.data.objects.get('Mia_Body_Anatomy_Skin') or bpy.data.objects['Body']
    body = canonical_copy(body_source, archive, 'MIA_BODY_HEAD_SKIN_MASTER')
    if any(poly.material_index!=0 for poly in body.data.polygons):
        skin_ids=[poly.index for poly in body.data.polygons if poly.material_index==0]
        skin_body=split(body,skin_ids,archive,'MIA_BODY_HEAD_SKIN_MASTER_CLEAN',body.data.materials[0])
        body.hide_render=body.hide_viewport=True
        body=skin_body
    body['role'] = 'complete editable body/head skin master; no hidden-body deletion'
    src = bpy.data.objects['SINGLE_HEAD_MIXED_REVIEW']
    rgb, centers = source_colors(src)
    warm = (rgb[:, 0] > .48) & (rgb[:, 0]-rgb[:, 1] > .015) & (rgb[:, 0]-rgb[:, 2] > .045) & (centers[:, 1] < -.015)
    warm_points = centers[warm]
    warp, landmarks = build_warp(face, body, warm_points)
    spec = importlib.util.spec_from_file_location('mia_face_art', str(Path(__file__).resolve().parents[2]/'build_mia_face_art_v02.py'))
    art = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(art)
    # The template's existing closed-eye shapes supply proven surface flow. New
    # neutral is half-closed; new blink targets are retargeted through the warp.
    old_keys = face.data.shape_keys.key_blocks
    coords = {k.name: np.array([v.co[:] for v in k.data]) for k in old_keys}
    base = coords['Basis']
    close_name = next(n for n in coords if n.endswith('Fcl_EYE_Close'))
    # Reuse the previously exercised UV-barycentric upper-line construction,
    # then retarget its physical ribbon through the same facial warp.
    original_mats = list(face.data.materials)
    _,rim_paths=art.fit_rim_image(original_mats[2],str(out/'Mia_FittedFace_RimGuideUV.png'))
    prior=set(bpy.data.objects)
    rim_report=art.build_upper_rim(face,rim_paths)
    rim=next(o for o in bpy.data.objects if o not in prior and o.type=='MESH')
    rim.name='MIA_UPPER_LID_PHYSICAL_RIM'
    rim_coords={k.name:np.array([v.co[:] for v in k.data]) for k in rim.data.shape_keys.key_blocks}
    rim.data.shape_keys.animation_data_clear()
    art.pose(face,'neutral')
    for k in old_keys:k.value=0
    neutral = base + .48*(coords[close_name]-base)
    for v, q in zip(face.data.vertices, neutral):
        v.co = q
    for v, q in zip(old_keys[0].data, neutral):
        v.co = q
    for k in old_keys:
        k.value = 0
    art.BASE_SKIN = (.83, .75, .71, 1)
    art.UNDER_EYE_STRENGTH = .40
    pigment, contours = art.bake_skin(face, str(out/'Mia_FittedFace_SkinUV.png'))
    face.data.materials[7] = art.skin_material(pigment)
    face.data.materials[0] = alpha_material(original_mats[0], 'MIA_MOUTH_CAVITY_ALBEDO', (.055,.024,.030))
    face.data.materials[1] = alpha_material(original_mats[1], 'MIA_EYE_WHITE_ALBEDO', (.80,.81,.79))
    face.data.materials[2] = art.owned_ink(original_mats[2], 'MIA_EYELINE_ALBEDO', 'lash')
    face.data.materials[3] = art.owned_ink(original_mats[3], 'MIA_LASH_ALBEDO', 'lash')
    face.data.materials[4] = art.owned_ink(original_mats[4], 'MIA_BROW_ALBEDO', 'brow')
    face.data.materials[5] = art.owned_eye_tone(original_mats[5])
    face.data.materials[6] = art.owned_eye_tone(original_mats[6], highlight=True)
    # Construct new, explicitly retargeted controls instead of asserting original
    # key names imply successful expression transfer.
    face.shape_key_clear()
    fitted = warp(neutral)
    for v, q in zip(face.data.vertices, fitted):
        v.co = q
    face.shape_key_add(name='Basis')
    new_targets = {'MIA_Blink': coords[close_name], 'MIA_Blink_L': neutral.copy(), 'MIA_Blink_R': neutral.copy()}
    for side, label in [(-1, 'L'), (1, 'R')]:
        mask = neutral[:, 0]*side > 0
        new_targets['MIA_Blink_'+label][mask] = coords[close_name][mask]
    for name, ending in [('MIA_Mouth_Open', 'Fcl_MTH_A'), ('MIA_Annoyed', 'Fcl_EYE_Angry'), ('MIA_Smile', 'Fcl_MTH_Fun'), ('MIA_Brow_Up', 'Fcl_BRW_Surprised')]:
        found = next((key for key in coords if key.endswith(ending)), None)
        if found:
            new_targets[name] = neutral + coords[found]-base
    changed = {}
    brow_ids=sorted({i for poly in face.data.polygons if poly.material_index==4 for i in poly.vertices})
    for values in [neutral,*new_targets.values()]:
        values[brow_ids,2]-=.016
    fitted=warp(neutral)
    for v,q in zip(face.data.vertices,fitted):v.co=q
    for v,q in zip(face.data.shape_keys.key_blocks[0].data,fitted):v.co=q
    for name, values in new_targets.items():
        key = face.shape_key_add(name=name, from_mix=False)
        points = warp(values)
        for v, q in zip(key.data, points):
            v.co = q
        changed[name] = {'vertices': int(np.sum(np.linalg.norm(points-fitted, axis=1) > 1e-7)), 'max_delta_m': float(np.linalg.norm(points-fitted,axis=1).max())}
    # Eye travel uses the source's curved iris geometry; adjust depth along a
    # shallow convex contact surface, and prove its combinations in renders.
    irisids = sorted({i for poly in face.data.polygons if poly.material_index in (5,6) for i in poly.vertices})
    for label, dx, dz in [('Left', -.006, 0), ('Right', .006, 0), ('Up', 0, .004), ('Down', 0, -.004)]:
        key = face.shape_key_add(name='MIA_Gaze_'+label, from_mix=False)
        for v, q in zip(key.data, fitted):
            v.co = q
        for side in (-1,1):
            ids = [i for i in irisids if fitted[i,0]*side > 0]
            center = fitted[ids].mean(axis=0)
            for i in ids:
                q = fitted[i].copy(); x0=(q[0]-center[0])/.047;z0=(q[2]-center[2])/.036
                x1=(q[0]+dx-center[0])/.047;z1=(q[2]+dz-center[2])/.036
                depth0=-.028*math.sqrt(max(.02,1-x0*x0-z0*z0));depth1=-.028*math.sqrt(max(.02,1-x1*x1-z1*z1))
                q += (dx, depth1-depth0, dz)
                key.data[i].co=q
    # Complementary scalp/back-head comes from the original complete body/head
    # skin. The source data are retained; a named review mask limits visibility.
    for v in body.data.vertices:
        z=v.co.z
        if z>1.35:
            v.co=warp(np.array([v.co[:]]))[0]
    if body.data.shape_keys:
        body.shape_key_clear()
    body.data.materials[0]=art.skin_material()
    scope=body.vertex_groups.new(name='HEAD_NECK_REVIEW_SCOPE')
    ids=[v.index for v in body.data.vertices if v.co.z>1.323]
    scope.add(ids,1,'REPLACE')
    mask=body.modifiers.new('Head-neck inspection scope; complete body retained','MASK');mask.vertex_group=scope.name
    body.hide_viewport=body.hide_render=False
    # Preserve genuine source hair; reject facial paint by color and contact
    # depth. Ambiguous boundaries are explicitly a visual-review limitation.
    hairids=[]
    for i,(q,c) in enumerate(zip(centers,rgb)):
        x,y,z=q
        hair_color=(c.mean()<.46 and max(c)-min(c)<.16)
        facial_paint=(1.405<z<1.548 and abs(x)<.113 and y>-.128)
        if hair_color and not warm[i] and not facial_paint:
            hairids.append(i)
    hair=split(src,hairids,haircol,'MIA_PIXAL_HAIR_DESIGN_SEPARATE',keys=False)
    hair['role']='exact source UV/geometry hair design partition; production retopology pending'
    hair['classification_limit']='color/contact first pass; not a production hair boundary approval'
    src.hide_render=src.hide_viewport=True
    parts=[]
    names={0:'MIA_MOUTH_CAVITY',1:'MIA_EYE_WHITES',2:'MIA_EYELINE',3:'MIA_EYELASHES',4:'MIA_EYEBROWS',5:'MIA_IRISES',6:'MIA_EYE_HIGHLIGHTS',7:'MIA_FACIAL_SKIN',8:'MIA_EYE_EXTRA'}
    for slot,name in names.items():
        ids=[poly.index for poly in face.data.polygons if poly.material_index==slot]
        if ids:
            ob=split(face,ids,dest,name,face.data.materials[slot])
            ob['role']='fitted independent facial component'
            parts.append(ob)
    rb=rim_coords['Basis'];rn=rb+.48*(rim_coords[close_name]-rb)
    rim.shape_key_clear()
    for v,q in zip(rim.data.vertices,warp(rn)):v.co=q
    rim.shape_key_add(name='Basis')
    rim_target=rim_coords[close_name]
    correction=next((p-rb for name,p in rim_coords.items() if name.startswith('MIA_UpperRim_BlinkClearance')),np.zeros_like(rb))
    for name in face.data.shape_keys.key_blocks.keys():
        if name=='Basis':continue
        points=rn.copy()
        if name=='MIA_Blink':points=rim_target+correction
        elif name in ('MIA_Blink_L','MIA_Blink_R'):
            side=-1 if name.endswith('_L') else 1
            keep=rn[:,0]*side>0
            points[keep]=(rim_target+correction)[keep]
        elif name=='MIA_Annoyed':
            oldname=next((n for n in rim_coords if n.endswith('Fcl_EYE_Angry')),None)
            if oldname:points=rn+rim_coords[oldname]-rb
        key=rim.shape_key_add(name=name,from_mix=False)
        for v,q in zip(key.data,warp(points)):v.co=q
    rim['role']='UV-barycentrically bound upper-lid ink ribbon; retargeted morphs and tested clearance'
    parts.append(rim)
    face.hide_render=face.hide_viewport=True
    controls=bpy.data.objects.new('MIA_FACIAL_CONTROLS',None);dest.objects.link(controls)
    for key in face.data.shape_keys.key_blocks[1:]:
        controls[key.name]=0.0
        controls.id_properties_ui(key.name).update(min=0.,max=1.)
    for ob in parts:
        for key in ob.data.shape_keys.key_blocks[1:]:
            d=key.driver_add('value').driver;v=d.variables.new();v.name='value';v.type='SINGLE_PROP';v.targets[0].id=controls;v.targets[0].data_path='['+json.dumps(key.name)+']';d.expression='value'
    def set_pose(**values):
        for key in controls.keys():
            if key.startswith('MIA_'):
                controls[key]=float(values.get(key,0))
        controls.update_tag();bpy.context.view_layer.update()
    scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=32
    scene.render.resolution_x=600;scene.render.resolution_y=760;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='MIA_STAGE2_COMPARISON_CAMERA';scene.camera=cam
    native=out/'Mia_Stage2_FittedFace.blend'
    set_pose();bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(native),check_existing=False)
    camera_records=[]
    # Review actual assembled AND independent head. No expensive state grid is
    # launched unless the producer explicitly requests --proofs after review.
    for name,yaw in [('front',0),('side',90),('quarter_right',45),('quarter_left',-45)]:
        camera_records.append(render(scene,cam,out,'neutral_'+name,yaw))
    hair_objects=[hair,bpy.data.objects.get('SINGLE_HAIR_MIXED_REVIEW')]+[o for o in scene.objects if o.name.startswith('REUSED_MiaHair_')]
    saved=[(o,o.hide_render) for o in hair_objects if o]
    for ob,_ in saved:ob.hide_render=True
    for name,yaw in [('front',0),('side',90),('back',180),('quarter',45)]:
        camera_records.append(render(scene,cam,out,'bald_'+name,yaw))
    for ob,hidden in saved:ob.hide_render=hidden
    if a.proofs:
        for blink in (0,.5,1):
            for gaze in ['Center','Left','Right','Up','Down']:
                state={'MIA_Blink':blink}
                if gaze!='Center':state['MIA_Gaze_'+gaze]=1
                set_pose(**state)
                camera_records.append(render(scene,cam,out,'eye_%s_%s'%(blink,gaze),0))
        for state,values in [('mouth',{'MIA_Mouth_Open':1}),('annoyed',{'MIA_Annoyed':.6}),('smile',{'MIA_Smile':.65}),('left_blink',{'MIA_Blink_L':1})]:
            set_pose(**values)
            for name,yaw in [('front',0),('quarter',45)]:
                camera_records.append(render(scene,cam,out,state+'_'+name,yaw))
    set_pose()
    # Same new camera for the actual Stage1 reference, rather than comparing
    # different framing and claiming a likeness improvement from it.
    for ob in parts+[body,hair]:ob.hide_render=True
    src.hide_render=False
    for name,yaw in [('front',0),('side',90),('quarter',45)]:
        camera_records.append(render(scene,cam,out,'before_'+name,yaw))
    src.hide_render=True
    for ob in parts+[body,hair]:ob.hide_render=False
    render(scene,cam,out,'neutral_final_front',0)
    after={n:mesh_signature(bpy.data.objects[n]) for n in originals}
    assert originals==after,'Stage1 mesh geometry/UV changed'
    assert digest(source)==source_hash,'Stage1 native changed'
    report={'status':'FITTING_STUDY_UNREVIEWED; ART_NOTAPPROVED; FULL_CHARACTER_INCOMPLETE','input_sha256_before':source_hash,'input_sha256_after':digest(source),'original_geometry_uv_unchanged':originals==after,'landmarks':landmarks,'warp_method':'measured source chin/nose + authored orbital/jaw/cheek/crown targets; 3D radial fit; source topology reused, not generated whole-head bbox fit','new_expression_target_delta':changed,'neutral_template_close':.48,'upper_rim_source_binding':rim_report,'parts':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uv_layers':[x.name for x in o.data.uv_layers],'keys':list(o.data.shape_keys.key_blocks.keys())} for o in parts],'hair_source_faces':len(hairids),'hair_source_total':len(src.data.polygons),'skin_source_samples':len(warm_points),'cameras':camera_records,'proof_grid_rendered':a.proofs,'limitations':['Art/likeness has not been approved','Hair is source design geometry, semantic boundary requires inspection and later production retopology','Gaze contact approximation and expression combinations require actual inspection','body master and complementary head use a named inspection mask; body proportions are not approved here','Final facial weights/correctives/physics and event animations incomplete']}
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native),check_existing=False)
    print('FITTED_FACE_SAVED',native)


if __name__=='__main__':
    main()
