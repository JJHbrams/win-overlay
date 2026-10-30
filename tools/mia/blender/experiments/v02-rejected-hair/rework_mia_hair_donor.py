"""Build Mia's CC0 donor-topology hair stage without touching frozen anatomy.

Run with Blender 5.2 in background.  The input blend is only read; the stage
and all review frames are written below D:/ai/Mia3DWork/model-v02/hair-donor-stage.
"""
import bpy
import hashlib
import json
import math
import os
import struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree

INPUT = r"D:/ai/Mia3DWork/model-v02/anime-anatomy/Mia_AnimeAnatomy_v02_candidate_v13_body.blend"
OUT = r"D:/ai/Mia3DWork/model-v02/hair-donor-stage"
OUT_BLEND = os.path.join(OUT, "Mia_HairDonor_Rework_candidate_v05.blend")
EXPECTED_SHA = "d90744a9ec2370ae8d9564e482fbffd6b2485334f9571278d4482ce26ac943ca"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def digest_object(obj):
    me = obj.data
    h = hashlib.sha256()
    h.update(str((len(me.vertices), len(me.polygons), len(me.uv_layers))).encode())
    for v in me.vertices:
        h.update(struct.pack('<3f', *v.co[:]))
    for p in me.polygons:
        h.update(struct.pack('<%dI' % len(p.vertices), *p.vertices[:]))
    for uv in me.uv_layers:
        for l in uv.data:
            h.update(struct.pack('<2f', *l.uv[:]))
    for key in obj.data.shape_keys.key_blocks if obj.data.shape_keys else []:
        h.update(key.name.encode())
        for pt in key.data:
            h.update(struct.pack('<3f', *pt.co[:]))
    return h.hexdigest()


def coll(name, parent=None, hidden=False):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if not c.name in bpy.context.scene.collection.children:
        (parent or bpy.context.scene.collection).children.link(c)
    c.hide_render = hidden
    c.hide_viewport = hidden
    return c


def active_source_copy(obj, collection, name):
    """Force Blender to compose matrix_basis for a visible disposable source copy."""
    cp=obj.copy(); cp.data=obj.data; cp.name=name; collection.objects.link(cp)
    cp.hide_viewport=False; cp.hide_render=False
    bpy.context.view_layer.update()
    return cp


def components(obj):
    me, mw = obj.data, obj.matrix_world
    adj = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices[:]
        adj[a].append(b); adj[b].append(a)
    seen, groups = set(), []
    for begin in range(len(me.vertices)):
        if begin in seen: continue
        stack, group = [begin], []
        seen.add(begin)
        while stack:
            v = stack.pop(); group.append(v)
            for n in adj[v]:
                if n not in seen: seen.add(n); stack.append(n)
        groups.append(group)
    vi = {}
    for i, g in enumerate(groups):
        for v in g: vi[v] = i
    faces = [[] for _ in groups]
    for p in me.polygons:
        faces[vi[p.vertices[0]]].append(p.index)
    result = []
    for i, g in enumerate(groups):
        pts = [mw @ me.vertices[v].co for v in g]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        result.append(dict(id=i, verts=g, faces=faces[i], lo=lo, hi=hi,
                           center=(lo+hi)*.5, span=hi-lo))
    return result


def mesh_from_components(source, selected, name, collection, material_copies, transform=None, excluded_material_indices=()):
    """Exact whole polygons/components, preserving face material IDs and UV loops."""
    me = source.data
    chosen_faces = [p for c in selected for p in c['faces'] if source.data.polygons[p].material_index not in excluded_material_indices]
    used = sorted({v for pi in chosen_faces for v in me.polygons[pi].vertices})
    remap = {v: i for i, v in enumerate(used)}
    coords = []
    for v in used:
        p = source.matrix_world @ me.vertices[v].co
        coords.append(transform(p) if transform else p)
    faces = [[remap[v] for v in me.polygons[pi].vertices] for pi in chosen_faces]
    out = bpy.data.meshes.new(name + "_MESH")
    out.from_pydata(coords, [], faces); out.update()
    for m in material_copies: out.materials.append(m)
    for uvsrc in me.uv_layers:
        uvout = out.uv_layers.new(name=uvsrc.name)
        for oi, pi in enumerate(chosen_faces):
            sp, op = me.polygons[pi], out.polygons[oi]
            op.material_index = sp.material_index
            for sl, ol in zip(sp.loop_indices, op.loop_indices): uvout.data[ol].uv = uvsrc.data[sl].uv
    for oi, pi in enumerate(chosen_faces):
        out.polygons[oi].material_index = me.polygons[pi].material_index
        out.polygons[oi].use_smooth = me.polygons[pi].use_smooth
    ob = bpy.data.objects.new(name, out); collection.objects.link(ob)
    ob["donor_component_ids"] = [c['id'] for c in selected]
    ob["source_object"] = source.name
    ob["provenance"] = "Victoria Rubin VRoid beta4 CC0 donor; whole connected components"
    return ob


def mesh_from_faces(source, face_ids, name, collection, material_copies, mesh=None, matrix=None):
    """Extract only requested source polygons; shared Body vertices never pull in skin."""
    me = mesh or source.data
    matrix = matrix or source.matrix_world
    used = sorted({v for pi in face_ids for v in me.polygons[pi].vertices})
    remap = {v:i for i,v in enumerate(used)}
    coords = [matrix @ me.vertices[v].co for v in used]
    out = bpy.data.meshes.new(name + '_MESH')
    out.from_pydata(coords, [], [[remap[v] for v in me.polygons[pi].vertices] for pi in face_ids]); out.update()
    for m in material_copies: out.materials.append(m)
    for uvs in me.uv_layers:
        uvout=out.uv_layers.new(name=uvs.name)
        for oi,pi in enumerate(face_ids):
            for sl,ol in zip(me.polygons[pi].loop_indices,out.polygons[oi].loop_indices): uvout.data[ol].uv=uvs.data[sl].uv
    for oi,pi in enumerate(face_ids):
        out.polygons[oi].material_index=0; out.polygons[oi].use_smooth=me.polygons[pi].use_smooth
    ob=bpy.data.objects.new(name,out); collection.objects.link(ob); return ob


def evaluated_hairback(source, slot):
    """Material-filtered evaluated geometry; shared Body vertices never copy skin."""
    deps=bpy.context.evaluated_depsgraph_get(); eo=source.evaluated_get(deps)
    em=eo.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
    ids=[p.index for p in em.polygons if p.material_index==slot]
    used={v for i in ids for v in em.polygons[i].vertices}
    assert len(ids)==394 and len(used)==225, (len(ids),len(used))
    # evaluated topology/material/UV stays index-compatible in this default pose
    delta=max(((source.matrix_world@a.co)-(eo.matrix_world@b.co)).length for a,b in zip(source.data.vertices,em.vertices))
    return eo,em,ids,{'raw_matrix':[list(r) for r in source.matrix_world], 'evaluated_matrix':[list(r) for r in eo.matrix_world], 'max_world_delta':delta}


def ray_uv_diagnostic(obj, face_ids, samples):
    """World-space first-hit and barycentric UV diagnostics, without scene mutation."""
    me=obj.data; verts=[]; tris=[]; meta=[]
    for pi in face_ids:
        p=me.polygons[pi]; loops=list(p.loop_indices)
        for j in range(1,len(loops)-1):
            ls=(loops[0],loops[j],loops[j+1]); ids=[]
            for li in ls: ids.append(len(verts)); verts.append(obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            tris.append(ids); meta.append((pi,ls))
    tree=BVHTree.FromPolygons(verts,tris,all_triangles=True); uv=me.uv_layers.active
    out=[]
    for x,z in samples:
        hit=tree.ray_cast(Vector((x,-1.0,z)),Vector((0,1,0)),3)
        if hit[0] is None: out.append({'x':x,'z':z,'hit':None}); continue
        co,no,tri,dist=hit; pi,ls=meta[tri]; a,b,c=[verts[i] for i in tris[tri]]
        v0=b-a; v1=c-a; v2=co-a; d00=v0.dot(v0); d01=v0.dot(v1); d11=v1.dot(v1); d20=v2.dot(v0); d21=v2.dot(v1)
        den=d00*d11-d01*d01; vb=(d11*d20-d01*d21)/den; vc=(d00*d21-d01*d20)/den; va=1-vb-vc
        u=(0,0) if not uv else tuple(uv.data[ls[0]].uv*va+uv.data[ls[1]].uv*vb+uv.data[ls[2]].uv*vc)
        out.append({'x':x,'z':z,'world_y':co.y,'normal':list(no),'face':pi,'uv':u})
    return out


def image_alpha_at(material, uv):
    nodes=material.node_tree.nodes if material and material.use_nodes else []
    tex=next((n for n in nodes if n.type=='TEX_IMAGE' and n.image),None)
    if not tex or not uv: return None
    im=tex.image; w,h=im.size[:]; x=min(w-1,max(0,int((uv[0]%1)*w))); y=min(h-1,max(0,int((uv[1]%1)*h)))
    return im.pixels[(y*w+x)*4+3]


def owned_materials(source):
    ans = []
    for i, sm in enumerate(source.data.materials):
        m = sm.copy() if sm else bpy.data.materials.new("Hair")
        m.name = "MiaHair_Donor_Charcoal_MASK_%02d" % i
        image=next((n.image for n in sm.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None) if sm and sm.use_nodes else None
        nt=m.node_tree; nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); mix=nt.nodes.new('ShaderNodeMixShader')
        tr=nt.nodes.new('ShaderNodeBsdfTransparent'); em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value=1
        nt.links.new(tr.outputs[0],mix.inputs[1]); nt.links.new(em.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],out.inputs[0])
        if image:
            tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=image; bw=nt.nodes.new('ShaderNodeRGBToBW'); ramp=nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].color=(.025,.028,.033,1); ramp.color_ramp.elements[1].color=(.12,.125,.14,1)
            cut=nt.nodes.new('ShaderNodeMath'); cut.operation='GREATER_THAN'; cut.inputs[1].default_value=.5
            nt.links.new(tex.outputs['Color'],bw.inputs[0]); nt.links.new(bw.outputs[0],ramp.inputs[0]); nt.links.new(ramp.outputs[0],em.inputs['Color']); nt.links.new(tex.outputs['Alpha'],cut.inputs[0]); nt.links.new(cut.outputs[0],mix.inputs[0])
        else: em.inputs['Color'].default_value=(.055,.06,.07,1); mix.inputs[0].default_value=1
        m.use_backface_culling=False
        ans.append(m)
    return ans


def material_back(src, slot):
    sm=src.data.materials[slot]; m=sm.copy(); m.name='MiaHair_Donor_HairBack_Charcoal_BLEND'; nt=m.node_tree; image=next((n.image for n in sm.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
    nt.nodes.clear(); out=nt.nodes.new('ShaderNodeOutputMaterial'); mix=nt.nodes.new('ShaderNodeMixShader'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); em=nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value=1
    tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=image; bw=nt.nodes.new('ShaderNodeRGBToBW'); ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(.025,.028,.033,1); ramp.color_ramp.elements[1].color=(.12,.125,.14,1)
    nt.links.new(tex.outputs['Color'],bw.inputs[0]); nt.links.new(bw.outputs[0],ramp.inputs[0]); nt.links.new(ramp.outputs[0],em.inputs['Color']); nt.links.new(tex.outputs['Alpha'],mix.inputs[0]); nt.links.new(tr.outputs[0],mix.inputs[1]); nt.links.new(em.outputs[0],mix.inputs[2]); nt.links.new(mix.outputs[0],out.inputs[0])
    m.use_backface_culling=True
    return [m]


def procedural_bundle_material():
    m=bpy.data.materials.new('MiaHair_Procedural_Graphite_Opaque'); m.use_nodes=True; bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(.045,.05,.06,1); bs.inputs['Roughness'].default_value=.8; bs.inputs['Specular IOR Level'].default_value=.1; return m


def make_curve(name, points, radius, material, collection, taper=True):
    cu = bpy.data.curves.new(name + "_MESH", 'CURVE'); cu.dimensions = '3D'; cu.resolution_u = 3
    cu.bevel_depth = radius; cu.bevel_resolution = 3; cu.resolution_u = 12
    sp = cu.splines.new('NURBS'); sp.points.add(len(points)-1)
    for i, p in enumerate(points): sp.points[i].co = (*p, 1)
    sp.order_u = min(3, len(points)); sp.use_endpoint_u = True
    if taper:
        for i, p in enumerate(sp.points): p.radius = 1.05 - .65*i/max(1, len(points)-1)
    cu.materials.append(material)
    ob = bpy.data.objects.new(name, cu); collection.objects.link(ob)
    ob["provenance"] = "curved donor-style secondary bundle"; return ob


def render_setup():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 768
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    cam=bpy.data.objects.get('MIA_REVIEW_CAMERA'); assert cam, 'expected v13 studio camera'
    cam.data.type='ORTHO'; cam.data.ortho_scale=.72; sc.camera=cam
    return cam


def point_camera(cam, pos, target=(0,0,1.52)):
    cam.location = pos; cam.rotation_euler = (Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()


def render_views(prefix, frames, camera):
    for label, loc in frames.items():
        point_camera(camera, loc)
        bpy.context.scene.render.filepath = os.path.join(OUT, prefix + '_' + label + '.png')
        bpy.ops.render.render(write_still=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    assert sha(INPUT) == EXPECTED_SHA, 'frozen input SHA mismatch'
    bpy.ops.wm.open_mainfile(filepath=INPUT)
    assert not bpy.data.collections.get('MIA_HAIR_DONOR_STAGE'), 'stage already exists in input'
    face, body, donor = bpy.data.objects['Mia_Face_AnimeTopology'], bpy.data.objects['Mia_Body_Anatomy_Skin'], bpy.data.objects['Hair001']
    frozen_before = {'face':digest_object(face),'body':digest_object(body),'source_sha':sha(INPUT)}
    archive = coll('SOURCE_ARCHIVE', hidden=True); stage = coll('MIA_HAIR_DONOR_STAGE'); refs = coll('MIA_HAIR_DONOR_REFERENCE', stage, True)
    active = coll('SOURCE_ACTIVE_DISPOSABLE')
    source_body=bpy.data.objects.get('Body'); source_face=bpy.data.objects.get('Face')
    donor=active_source_copy(donor,active,'SOURCE_ACTIVE_Hair001_CC0')
    body_src=active_source_copy(source_body,active,'SOURCE_ACTIVE_Body_CC0') if source_body else None
    source_face_active=active_source_copy(source_face,active,'SOURCE_ACTIVE_Face_CC0') if source_face else None
    assert round(donor.matrix_world[0][0]) == -1 and round(body_src.matrix_world[0][0]) == -1, 'active source registration missing 180Z'
    # Archive copies are deliberately hidden and untouched. The complete donor is rendered first.
    raw = donor.copy(); raw.data = donor.data.copy(); raw.name = 'SOURCE_ARCHIVE_Hair001_COMPLETE_CC0'; archive.objects.link(raw)
    raw.hide_render = raw.hide_viewport = True
    donor.hide_render = donor.hide_viewport = False
    if body_src: body_src.hide_render = body_src.hide_viewport = True
    camera = render_setup()
    # Donor diagnostic uses the known illuminated Mia scene, never the archive-only black scene.
    donor.hide_render = donor.hide_viewport = True
    mats = owned_materials(donor); comps = components(donor)
    # Long, high-back components are the donor's signature right ponytail; retain as a rehomed rear layer.
    # Correct active-world measurement: the high side bundle is the long family
    # wholly outboard on +X, rather than the centered fringe/cap components.
    pony = [c for c in comps if c['lo'].x > .045 and c['span'].z > .20]
    # Components reaching far out on +X are the outer shell of the unmistakable
    # donor ponytail.  They are not retained in the front-facing foundation.
    pony = list({c['id']: c for c in pony}.values())
    foundation = [c for c in comps if c not in pony and len(c['faces']) >= 2]
    # Preserve authored crown/fringe whole topology.  Mild opening deformation avoids its blunt straight bang edge.
    def fringe_shape(p):
        q = p.copy()
        if q.y < -.025:
            fall=max(0.0,min(1.0,(1.70-q.z)/.25))
            q.z -= fall*(.015 + .012*math.sin((q.x+.035)*38))
            q.x += fall*.004*math.sin((q.z-1.4)*19)
        return q
    mainhair = mesh_from_components(donor, foundation, 'MiaHair_Donor_CrownFringe_Foundation', stage, mats, fringe_shape, excluded_material_indices=(2,))
    # Exact material-owned Body hair back extraction, without changing source body or any face ROI.
    back = None
    if body_src and 'F00_000_HairBack_00_HAIR' in [m.name if m else '' for m in body_src.data.materials]:
        slot = [m.name if m else '' for m in body_src.data.materials].index('F00_000_HairBack_00_HAIR')
        eo, em, wanted, eval_report=evaluated_hairback(body_src,slot)
        samples=[(0,1.54),(-.04,1.515),(.04,1.515)]
        srcface=source_face_active
        skin_ids=[]
        if srcface:
            skin_slots=[i for i,m in enumerate(srcface.data.materials) if m and '_SKIN' in m.name]
            skin_ids=[p.index for p in srcface.data.polygons if p.material_index in skin_slots]
        eval_report['body_uv_layers']=[u.name for u in body_src.data.uv_layers]
        eval_report['body_active_uv']=body_src.data.uv_layers.active.name if body_src.data.uv_layers.active else None
        eval_report['hairback_rays']=ray_uv_diagnostic(body_src,wanted,samples)
        hbmat=body_src.data.materials[slot]
        for hit in eval_report['hairback_rays']:
            hit['maintex_alpha']=image_alpha_at(hbmat,hit.get('uv')) if hit.get('hit',True) is not None else None
        eval_report['faceskin_rays']=ray_uv_diagnostic(srcface,skin_ids,samples) if skin_ids else []
        # First render the complete original avatar under the v13 studio lights.
        face.hide_render=True; body.hide_render=True; body_src.hide_render=False; donor.hide_render=False
        if srcface: srcface.hide_render=False
        render_views('05_v03_complete_source_avatar', {'front':(0,-.78,1.49),'back':(0,.78,1.49)}, camera)
        if srcface: srcface.hide_render=True
        face.hide_render=False; body.hide_render=False; body_src.hide_render=True; donor.hide_render=True
        back=mesh_from_faces(body_src,wanted,'MiaHair_Donor_BodyHairBack_Foundation',stage,material_back(body_src,slot),mesh=em,matrix=eo.matrix_world)
        assert len(back.data.polygons)==394 and len(back.data.vertices)==225
        back['provenance']='evaluated Body F00_000_HairBack_00_HAIR exact faces/UV'
        body_src.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    # Rehome tail components below the crown. It is scaled around high roots and spread over the rear/nape.
    rehomed=[]
    for rank, c in enumerate(pony):
        top=[donor.matrix_world @ donor.data.vertices[v].co for v in c['verts'] if (donor.matrix_world @ donor.data.vertices[v].co).z > c['hi'].z-.018]
        root=sum(top,Vector())/len(top); source_span=max(.01,c['hi'].z-c['lo'].z)
        target=Vector((-.15 + .30*(rank/max(1,len(pony)-1)), .145 + .018*math.sin(rank*1.7), 1.64-.012*(rank%3)))
        target_span=.36 + .08*(rank%3)/2
        def xf(p, root=root, target=target, rank=rank):
            d=p-root; scale=target_span/source_span
            q=target + Vector((d.x*scale, d.y*scale, d.z*scale)) + Vector((.009*math.sin((p.z-1.3)*15+rank), .0, 0))
            q.x=max(-.19,min(.19,q.x)); q.y=max(-.20,min(.22,q.y)); return q
        wave = mesh_from_components(donor,[c],'MiaHair_Donor_RehomedWave_%03d'%rank,stage,mats,xf,excluded_material_indices=(2,))
        rehomed.append(wave)
    # Compact rear half-up knot: a small core with curved, buried wraps.
    knotmat=procedural_bundle_material()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, location=(0,.145,1.62), scale=(.045,.030,.040))
    knot=bpy.context.object; knot.name='MiaHair_Compact_HalfUp_Knot_Core'; knot.data.materials.append(knotmat)
    for p in knot.data.polygons: p.use_smooth=True
    for c in list(knot.users_collection): c.objects.unlink(knot)
    stage.objects.link(knot); knot["provenance"]='compact half-up kernel, wrapped by donor-style curved bundles'
    for i in range(7):
        a=i*math.tau/7
        pts=[]
        for j in range(9):
            t=j/8; ang=a+t*math.tau*1.15
            pts.append((.038*math.cos(ang), .145+.024*math.sin(ang),1.62+.030*math.sin(ang*.7)))
        make_curve('MiaHair_Knot_Wrap_%02d'%i,pts,.004,knotmat,stage)
    # Exactly one anatomical +X left braid (character left viewed from front), three woven bundles.
    centers=[Vector((.10,0,1.60)),Vector((.112,-.025,1.55)),Vector((.125,-.09,1.48)),Vector((.135,-.12,1.35)),Vector((.14,-.15,1.22))]
    for lane in range(3):
        pts=[]
        for i in range(96):
            u=i/95*(len(centers)-1); a=min(len(centers)-2,int(u)); t=u-a
            c=centers[a].lerp(centers[a+1],t); tangent=(centers[a+1]-centers[a]).normalized()
            perp=Vector((-tangent.y,tangent.x,0)).normalized(); r=.012*(1-i/150)
            pts.append(c+perp*(r*math.cos(lane*math.tau/3+i*math.pi/2))+Vector((0,0,r*math.sin(lane*math.tau/3+i*math.pi/2))))
        ob=make_curve('MiaHair_LEFT_Braid_Bundle_%d'%lane,pts,.0065,knotmat,stage)
        ob['region']='one anatomical left braid'
    # A few long borrowed wave silhouettes prevent a cap/helmet and layer under the knot.
    for i,x in enumerate((-.145,-.10,-.055,.00,.055,.10,.145)):
        pts=[(x*.45,.125,1.68),(x,.17,1.57),(x*.92,.15,1.44),(x+(.018 if i%2 else -.018),.08,1.30)]
        make_curve('MiaHair_Rear_LooseWave_%02d'%i,pts,.006,knotmat,stage)
    donor_report=[]
    for c in comps:
        donor_report.append({'id':c['id'],'verts':len(c['verts']),'polys':len(c['faces']),
            'bounds_min':list(c['lo']),'bounds_max':list(c['hi']),
            'class':'high_right_ponytail_rehomed' if c in pony else 'crown_fringe_or_side_foundation'})
    # Evaluated visible hair envelope is deliberately bounded to Mia's compact silhouette.
    deps=bpy.context.evaluated_depsgraph_get(); pts=[]
    for ob in stage.objects:
        if ob.hide_render: continue
        eo=ob.evaluated_get(deps)
        if ob.type == 'MESH': pts += [eo.matrix_world @ v.co for v in eo.data.vertices]
        elif ob.type == 'CURVE': pts += [eo.matrix_world @ Vector(c) for c in ob.bound_box]
    lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    assert lo.x >= -.205 and hi.x <= .205 and lo.y >= -.225 and hi.y <= .235 and lo.z >= 1.15 and hi.z <= 1.81, ('hair envelope',lo[:],hi[:])
    # Must save candidate before final diagnostic renders.
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    render_views('08_v05_mia_rework', {'front':(0,-.78,1.49),'left':(.78,0,1.49),'right':(-.78,0,1.49),'back':(0,.78,1.49),
                                    'q_front_left':(.58,-.52,1.56),'q_back_right':(-.58,.52,1.56)}, camera)
    frozen_after={'face':digest_object(face),'body':digest_object(body),'source_sha':sha(INPUT)}
    assert frozen_before == frozen_after, 'frozen anatomy or input changed'
    report={'input':INPUT,'input_sha256':sha(INPUT),'frozen_before':frozen_before,'frozen_after':frozen_after,
      'source_object':'Hair001','source_components':len(comps),'foundation_component_ids':[c['id'] for c in foundation],
      'rehomed_ponytail_component_ids':[c['id'] for c in pony[:36]],'reused_ponytail_component_count':len(rehomed),
      'body_hairback_extracted':bool(back),'materials_created':[m.name for m in mats],
      'regions':['authored crown/fringe foundation','material-owned Body HairBack foundation','rehomed rear waves','compact half-up knot','exactly one +X left braid'],
      'evaluated_visible_bounds_min':list(lo),'evaluated_visible_bounds_max':list(hi),
      'component_analysis':donor_report}
    report['visible_required_regions']={o.name:not o.hide_render for o in stage.objects if 'Donor_RehomedWave' in o.name or 'Knot' in o.name or 'Braid' in o.name or 'Rear_Loose' in o.name}
    report['evaluated_hairback_groundtruth']=eval_report
    with open(os.path.join(OUT,'hair-donor-report-v05.json'),'w',encoding='utf8') as f: json.dump(report,f,indent=2)

if __name__ == '__main__': main()
