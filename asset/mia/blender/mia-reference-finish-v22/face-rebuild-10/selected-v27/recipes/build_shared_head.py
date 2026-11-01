import bpy,bmesh,numpy as np,json,collections,hashlib
from pathlib import Path
O=Path(__file__).parent;OUT=O/'face-shared-final';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(O/'face-final-r3/Mia_Foundation_v27.blend'))
body=bpy.data.objects['MIA_V06_BODY_SKIN'];skin=bpy.data.objects['MIA_V27_ContinuousSkin'];master=bpy.data.objects['MIA_V27_Foundation_Face']
bodym=body.data;N=len(bodym.vertices);bp=np.array([v.co[:] for v in bodym.vertices]);names=[k.name for k in skin.data.shape_keys.key_blocks];world=np.array([[skin.matrix_world@v.co for v in k.data[:728]] for k in skin.data.shape_keys.key_blocks]);sf=[tuple(p.vertices) for p in list(skin.data.polygons)[:1342]]
mapping=json.loads((O/'shared-boundary-map.json').read_text());pairs=mapping['skin_welded_to_body_control'];assert len(pairs)==38
vmap={int(a):int(b) for a,b in pairs};assert len(set(vmap.values()))==38
for i in range(728):
 if i not in vmap:vmap[i]=N+sum(v>=N for v in vmap.values())
inv=body.matrix_world.inverted();local=np.array([[inv@__import__('mathutils').Vector(p) for p in c] for c in world]);coords=np.empty((len(names),N+690,3));coords[:,:N]=bp
for i,j in vmap.items():coords[:,j]=local[:,i]
faces=[tuple(p.vertices) for p in bodym.polygons]+[tuple(vmap[i] for i in f) for f in sf]
mesh=bpy.data.meshes.new('V27_SharedHeadBody_Control');mesh.from_pydata(coords[0],[],faces);mesh.materials.append(skin.material_slots[0].material)
for m in bodym.materials:mesh.materials.append(m)
for p in mesh.polygons:
 if p.index<len(bodym.polygons):p.material_index=bodym.polygons[p.index].material_index+1;p.use_smooth=bodym.polygons[p.index].use_smooth
 else:p.material_index=0;p.use_smooth=True
for old in bodym.uv_layers:
 uv=mesh.uv_layers.new(name=old.name)
 for i,d in enumerate(old.data):uv.data[i].uv=d.uv
 if old.name==skin.data.uv_layers.active.name:
  for p,sp in zip(list(mesh.polygons)[len(bodym.polygons):],list(skin.data.polygons)[:1342]):
   for li,sli in zip(p.loop_indices,sp.loop_indices):uv.data[li].uv=skin.data.uv_layers.active.data[sli].uv
# Preserve all nonstructural Body numeric/color attributes in the unchanged prefix.
for attr in bodym.attributes:
 if attr.name in {'position','.edge_verts','.corner_vert','.corner_edge','material_index'} or attr.name in mesh.attributes:continue
 try:
  dest=mesh.attributes.new(attr.name,attr.data_type,attr.domain)
  prop='vector' if attr.data_type in {'FLOAT_VECTOR','FLOAT2','INT32_2D'} else 'color' if 'COLOR' in attr.data_type else 'value'
  if attr.domain=='EDGE':
   oldedges={tuple(sorted(e.vertices)):e.index for e in bodym.edges}
   for e in mesh.edges:
    j=oldedges.get(tuple(sorted(e.vertices)))
    if j is not None:setattr(dest.data[e.index],prop,getattr(attr.data[j],prop))
  else:
   for i,d in enumerate(attr.data):setattr(dest.data[i],prop,getattr(d,prop))
 except Exception as e:print('ATTRIBUTE_COPY_NOTE',attr.name,str(e))
# Only actual eye/mouth boundaries remain creased. The head/face junction is shared and uncreased.
counts=collections.Counter(tuple(sorted((u,v))) for f in faces for u,v in zip(f,f[1:]+f[:1]));ce=mesh.attributes.get('crease_edge') or mesh.attributes.new('crease_edge','FLOAT','EDGE')
faceedges=set(tuple(sorted((vmap[u],vmap[v]))) for f in sf for u,v in zip(f,f[1:]+f[:1]))
for e in mesh.edges:
 pair=tuple(sorted(e.vertices))
 if pair in faceedges:ce.data[e.index].value=1. if counts[pair]==1 else 0.
ob=body.copy();ob.data=mesh;ob.name='MIA_V27_SharedHeadBody';bpy.context.scene.collection.objects.link(ob);ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
ob.vertex_groups.clear()
for original_group in body.vertex_groups:ob.vertex_groups.new(name=original_group.name)
weldgroup=ob.vertex_groups.new(name='V27_OriginalBodyWeldOnly');weldgroup.add(list(range(N)),1.,'REPLACE')
for modifier in ob.modifiers:
 if modifier.type=='WELD':modifier.vertex_group=weldgroup.name
for vg in skin.vertex_groups:
 if not ob.vertex_groups.get(vg.name):ob.vertex_groups.new(name=vg.name)
for i,v in enumerate(bodym.vertices):
 for g in v.groups:ob.vertex_groups[body.vertex_groups[g.group].name].add([i],g.weight,'REPLACE')
for i,j in vmap.items():
 if j<N:continue
 for g in skin.data.vertices[i].groups:ob.vertex_groups[skin.vertex_groups[g.group].name].add([j],g.weight,'REPLACE')
for name,c in zip(names,coords):
 k=ob.shape_key_add(name=name,from_mix=False)
 for v,p in zip(k.data,c):v.co=p
 k.value=0
 if name!='Basis':
  dr=k.driver_add('value').driver;dr.type='AVERAGE';v=dr.variables.new();v.name='face_key';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks['+json.dumps(name)+'].value'
for old in [body,skin]:old.hide_render=True;old.hide_viewport=True;old.hide_set(True)
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'))
unchanged=[i for i in range(N) if i not in vmap.values()]
(OUT/'shared-head-audit.json').write_text(json.dumps({'source':'face-final-r3','body_control_vertices':N,'face_control_vertices':728,'shared_boundary_vertices':38,'joined_control_vertices':len(mesh.vertices),'body_nonboundary_allkeys_exact':bool(np.array_equal(coords[:,unchanged],np.broadcast_to(bp[unchanged],coords[:,unchanged].shape))),'shared_mapping':pairs,'body_modifiers_retained':[(m.name,m.type) for m in ob.modifiers],'limits':'Actual lower-body evaluated equivalence, new SS2 eye contact, and shared seam renders pending. Source original Body remains archived unchanged.'},indent=2));print('SHARED_HEAD_SAVED')
