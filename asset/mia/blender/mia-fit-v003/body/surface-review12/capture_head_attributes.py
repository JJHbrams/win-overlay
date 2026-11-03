"""SavedR3b evaluatedhead shader attributes/cornerdata. CPU readonly capture."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;owner=bpy.data.objects['MIA_V27_SharedHeadBody'];bpy.context.scene.frame_set(1);dg=bpy.context.evaluated_depsgraph_get();ev=owner.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);me.calc_loop_triangles()
d=np.load(P/'donor.npz');world=np.asarray([ev.matrix_world@v.co for v in me.vertices],np.float32);assert np.array_equal(world,d['world'])
tri=np.array([t.vertices[:] for t in me.loop_triangles],np.int32);loops=np.array([t.loops[:] for t in me.loop_triangles],np.int32);assert np.array_equal(tri,d['triangles'])
out={};records=[];uvnames={u.name for u in me.uv_layers}
for a in me.attributes:
    if a.name.startswith('.') or a.name=='position' or a.name in uvnames or a.domain not in ['POINT','CORNER']:continue
    kind=a.data_type
    if kind in ['FLOAT_COLOR','BYTE_COLOR']:prop='color';dim=4;dtype=np.float32
    elif kind=='FLOAT_VECTOR':prop='vector';dim=3;dtype=np.float32
    elif kind=='FLOAT2':prop='vector';dim=2;dtype=np.float32
    elif kind=='FLOAT':prop='value';dim=1;dtype=np.float32
    elif kind in ['INT','BOOLEAN']:prop='value';dim=1;dtype=np.int32
    else:continue
    vals=np.empty(len(a.data)*dim,dtype=dtype);a.data.foreach_get(prop,vals);vals=vals.reshape(-1,dim)
    if a.domain=='CORNER':vals=vals[loops]
    key='attribute_'+str(len(records));out[key]=vals;records.append(dict(name=a.name,domain=a.domain,data_type=kind,property=prop,dimension=dim,npz_key=key))
usage=[];config={};seen=set()
def walk(tree,material):
    if tree is None or tree.as_pointer() in seen:return
    seen.add(tree.as_pointer())
    for n in tree.nodes:
        if n.type=='ATTRIBUTE':usage.append(dict(material=material,node=n.name,attribute=n.attribute_name,type=n.attribute_type))
        if n.type=='VERTEX_COLOR':usage.append(dict(material=material,node=n.name,attribute=n.layer_name,type='VERTEX_COLOR'))
        if n.type=='GROUP':walk(n.node_tree,material)
        if n.type=='MATH' or 'SkinBase' in n.name:
            config.setdefault(material,[]).append(dict(name=n.name,type=n.bl_idname,operation=getattr(n,'operation',None),inputs=[dict(name=s.name,value=list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value) for s in n.inputs if hasattr(s,'default_value')],outputs=[dict(name=s.name,value=list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value) for s in n.outputs if hasattr(s,'default_value')]))
for mat in owner.data.materials:
    if mat:walk(mat.node_tree,mat.name)
# Shader group-weight names become same-valued staticPOINT attributes if needed.
captured={r['name'] for r in records}|uvnames
for use in usage:
    name=use['attribute']
    if name in captured or not name or name not in owner.vertex_groups:continue
    gi=owner.vertex_groups[name].index;vals=np.array([sum(g.weight for g in v.groups if g.group==gi) for v in me.vertices],np.float32)[:,None];key='attribute_'+str(len(records));out[key]=vals
    records.append(dict(name=name,domain='POINT',data_type='FLOAT',property='value',dimension=1,npz_key=key,origin='Evaluatedshadervertexgroup'));captured.add(name)
np.savez_compressed(P/'head-attributes.npz',**out);report=dict(attributes=records,shader_attribute_usage=usage,shader_transfer_config=config,all_oldUV_layers=sorted(uvnames),
    original_evaluated_geometry_equal_donor=True,source_native_sha256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),GPU_used=False,native_saved=False)
(P/'head-attributes.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');ev.to_mesh_clear();print('REVIEW12_HEAD_ATTRIBUTES',json.dumps(dict(attributes=records,shader_attribute_usage=usage)),flush=True)
