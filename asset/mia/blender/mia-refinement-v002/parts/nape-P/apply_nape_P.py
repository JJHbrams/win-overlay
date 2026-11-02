"""Small guarded existing-layer reconstruction, compatible with MN and O."""
import bpy,bmesh,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def apply(folder=None):
 O=Path(folder) if folder else (P if (P/'repair.json').exists() else P/'nape-P');r=json.loads((O/'repair.json').read_text());ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;assert len(m.vertices)==r['base_vertices'] and len(m.polygons)==r['base_polys'];assert hashlib.sha256(np.array([v.vertex_index for v in m.loops],np.int32).tobytes()).hexdigest()==r['loop_vertices_sha256'];assert not m.has_custom_normals,'P requires auto normals before adding6 local patch corners'
 for x in r['region_guard']:assert np.array_equal(np.array(m.vertices[x['vertex']].co,np.float32),np.array(x['position'],np.float32))
 for name,digest in r['old_UV_hashes'].items():assert hashlib.sha256(np.array([v.uv[:] for v in m.uv_layers[name].data],np.float32).tobytes()).hexdigest()==digest
 oldCount=len(m.polygons);oldLoops=len(m.loops);oldIDs=np.array([v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data],np.int32);oldUV={u.name:np.array([v.uv[:] for v in u.data],np.float32) for u in m.uv_layers};bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();raw=bm.faces.layers.int.get('MIA_SOURCE_POLYGON');assert raw is not None;newTag=bm.faces.layers.int.new('MIA_V002_NapePatchID')
 for e in r['coordinate_edits']:bm.verts[e['vertex']].co=e['target']
 for i,f in enumerate(r['new_faces']):
  face=bm.faces.new([bm.verts[v] for v in f['vertices']]);face[raw]=f['raw_source_id'];face[newTag]=i+1;face.material_index=f['material_index'];face.smooth=True
  for loop,c in zip(face.loops,f['corners']):
   for name,uv in c['UV'].items():layer=bm.loops.layers.uv.get(name);assert layer is not None;loop[layer].uv=uv
 bm.to_mesh(m);bm.free();m.update();newIDs=np.array([v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data],np.int32);assert np.array_equal(newIDs[:oldCount],oldIDs),'Existing source faces reordered';assert all(np.array_equal(np.array([v.uv[:] for v in m.uv_layers[name].data],np.float32)[:oldLoops],uv) for name,uv in oldUV.items());corner=np.zeros((len(m.loops),3),np.float32)
 for f in r['new_faces']:
  index=int(np.flatnonzero(newIDs==f['raw_source_id'])[0]);poly=m.polygons[index];assert list(poly.vertices)==f['vertices']
  for li,c in zip(poly.loop_indices,f['corners']):corner[li]=c['custom_normal']
 m.normals_split_custom_set(corner.tolist());attr=m.attributes['MIA_V002_RimNormalWeight']
 for vi in r['force_geometric_normal_vertices']:attr.data[vi].value=1
 ob['mia_component']='hair';m.update();return {'variant':'nape-P','added_faces':len(r['new_faces']),'removed_faces':0,'existing_vertex_edits':len(r['coordinate_edits']),'new_custom_normal_corners':int(np.linalg.norm(corner,axis=1).astype(bool).sum()),'old_corners_auto_normals':True,'no_original_UV_changes':True,'resolved_free_layer_junctions':r['resolved_junctions'],'deferred_buried_fans':r['deferred_buried_fans'],'ART':'UNVERIFIED; no whole-nape PASS'}
