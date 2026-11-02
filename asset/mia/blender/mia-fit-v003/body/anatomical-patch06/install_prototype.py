"""Create a private STATIC posed prototype; no native, rig or key replay."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;B=P.parent
NAME='MIA_v003_AnatomicalPatch06_STATIC_UNVERIFIED'
COLLECTION=NAME

def coords(data,field='co',width=3,dtype=np.float32):
    x=np.empty(len(data)*width,dtype);data.foreach_get(field,x);return x.reshape(-1,width)

def build(source=None):
    source=source or bpy.data.objects['MIA_V27_SharedHeadBody'];d=np.load(P/'prototype06.npz');report=json.loads((P/'construction.json').read_text())
    if NAME in bpy.data.objects:raise RuntimeError('Prototype already exists')
    mw=np.array(source.matrix_world);world=d['world'];local=(world-mw[:3,3])@np.linalg.inv(mw[:3,:3]).T
    sizes=d['polygon_sizes'];offset=np.r_[0,np.cumsum(sizes)];faces=[d['loop_vertices'][offset[i]:offset[i+1]].tolist() for i in range(len(sizes))]
    me=bpy.data.meshes.new(NAME+'_Mesh');me.from_pydata(local.tolist(),[],faces);me.update()
    ob=source.copy();ob.data=me;ob.name=NAME
    arm=[m for m in ob.modifiers if m.type=='ARMATURE'];assert len(arm)==1;ob.modifiers.remove(arm[0]);ob.animation_data_clear()
    col=bpy.data.collections.new(NAME);bpy.context.scene.collection.children.link(col);col.objects.link(ob);col.hide_render=True
    for mat in source.data.materials:me.materials.append(mat)
    for poly,mi in zip(me.polygons,d['polygon_materials']):poly.material_index=int(mi);poly.use_smooth=True
    kept=d['kept_original_faces'];newstart=len(kept)
    for j,oldfi in enumerate(kept):me.polygons[j].use_smooth=source.data.polygons[int(oldfi)].use_smooth
    for olduv in source.data.uv_layers:
        uv=me.uv_layers.new(name=olduv.name)
        for j,oldfi in enumerate(kept):
            a=source.data.polygons[int(oldfi)];b=me.polygons[j]
            for ia,ib in zip(a.loop_indices,b.loop_indices):uv.data[ib].uv=olduv.data[ia].uv
        # New corners are deliberately UNSEATED for this gray-only structural
        # proof. Do not imply working garment/UV migration from zeros.
    source.data.calc_loop_triangles();rawtri=np.array([t.vertices[:] for t in source.data.loop_triangles],np.int32)
    cache=np.load(B/'posed-target/control-topology.npz');assert np.array_equal(rawtri,cache['triangles'])
    oldW=np.load(B/'current-body-weights.npz');names=list(map(str,oldW['names']));weights=oldW['weights'].astype(float);assert set(names)=={g.name for g in source.vertex_groups}
    # Mesh replacement may rebuild the private object's group ordering. Always
    # resolve by semantic name; cached numeric group indices are not portable.
    for name in names:
        if ob.vertex_groups.get(name) is None:ob.vertex_groups.new(name=name)
    rows=[]
    for row in report['new_vertex_correspondence']:
        bar=np.array(row['barycentric']);tri=rawtri[row['source_raw_triangle']];rows.append(bar@weights[tri])
    allW=np.vstack([weights,np.array(rows)])
    rig=next(m.object for m in source.modifiers if m.type=='ARMATURE');bones={b.name for b in rig.data.bones if b.use_deform};bonecols=[i for i,name in enumerate(names) if name in bones]
    allW[len(weights):,bonecols]/=allW[len(weights):,bonecols].sum(1)[:,None]
    for gi,name in enumerate(names):
        g=ob.vertex_groups[name]
        for vi in np.flatnonzero(allW[:,gi]):g.add([int(vi)],float(allW[vi,gi]),'REPLACE')
    # Preserve numeric POINT shader attributes on every original ID. Appended
    # body points have no head-material blending.
    for a in source.data.attributes:
        if a.domain!='POINT' or a.name=='position' or a.data_type not in ['FLOAT','INT','BOOLEAN','FLOAT_VECTOR','FLOAT_COLOR']:continue
        dest=me.attributes.new(a.name,a.data_type,'POINT')
        field,width,dtype={'FLOAT':('value',1,np.float32),'INT':('value',1,np.int32),'BOOLEAN':('value',1,np.bool_),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT_COLOR':('color',4,np.float32)}[a.data_type]
        values=np.zeros((len(world),width),dtype);values[:len(source.data.vertices)]=coords(a.data,field,width,dtype);dest.data.foreach_set(field,values.ravel())
    # Keep original crease and seam policy by stable edge vertex pair.
    edge_policy={tuple(sorted(e.vertices[:])):i for i,e in enumerate(source.data.edges)}
    crease=source.data.attributes.get('crease_edge');newcrease=me.attributes.new('crease_edge','FLOAT','EDGE') if crease else None
    for e in me.edges:
        oi=edge_policy.get(tuple(sorted(e.vertices[:])))
        if oi is not None:
            e.use_seam=source.data.edges[oi].use_seam
            if crease:newcrease.data[e.index].value=crease.data[oi].value
    originalkeys=source.data.shape_keys.key_blocks
    bodykeyzero={k.name:bool(np.array_equal(coords(k.data)[:3957],coords(originalkeys['Basis'].data)[:3957])) for k in originalkeys}
    assert all(bodykeyzero.values())
    ob['status']='STATIC gray design; original47/UV/new inverse migration UNVERIFIED';ob['source_native']='4dc1';ob['prototype_sha256']=hashlib.sha256((P/'prototype06.npz').read_bytes()).hexdigest()
    bpy.context.view_layer.update()
    (P/'migration-readout.json').write_text(json.dumps(dict(original47_body_deltas_measured_zero=bodykeyzero,original47_archived_unchanged=True,private_prototype_has_keys=False,private_prototype_has_armature=False,new_uv_corners_unseated=True,
        bone_groups=len(bonecols),nonbone_groups=[name for name in names if name not in bones],new_bone_weight_sum_min=float(allW[len(weights):,bonecols].sum(1).min()),new_bone_weight_sum_max=float(allW[len(weights):,bonecols].sum(1).max()),
        source_raw_triangles_match_cache=True,source_raw_triangle_loop_ids=[[int(i) for i in source.data.loop_triangles[row['source_raw_triangle']].loops] for row in report['new_vertex_correspondence']],
        correspondence=report['new_vertex_correspondence'],status='STATIC only: per-corner UV and47 bindings/freshnewpointinverse pending; not rigged'),indent=2)+'\n')
    return ob
