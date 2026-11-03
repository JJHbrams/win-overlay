"""Freeze the actually inspected live coordinates for reproducible batch review.

Does not save a native or select/promote a model. Reuses the immutable atlas.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
source=ROOT/'.mia-cache/body-h/shape/assembly/winding-fixed'
out=ROOT/'.mia-cache/body-h/shape/assembly/live-D'
body=bpy.data.objects['MIA_Review12_H_LiveRepair'];assert body.mode=='OBJECT'
v=np.array([p.co[:] for p in body.data.vertices],np.float32)
ns=bpy.app.driver_namespace
assert np.array_equal(v,ns['MIA_Live_NeckOval_After'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
spec=importlib.util.spec_from_file_location('live_export_guard',ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
capacity=guard.inspect(100*1024**2);assert not capacity['violations'],capacity
assert not out.exists(),'Never overwrite a frozen live capture'
d=dict(np.load(source/'geometry.npz'));before=d['world'];d['world']=v
head=np.unique(d['triangles'][d['source_part']==1]);assert np.array_equal(v[head],before[head])
for key in ['waist','armR','armL']:
    ids=ns['MIA_Live_H_Rows'][key];assert np.array_equal(v[ids],before[ids])
out.mkdir(parents=True);(out/'atlas').mkdir()
np.savez_compressed(out/'geometry.npz',**d)
changed=np.flatnonzero(np.any(v!=before,axis=1))
np.savez_compressed(out/'live-vertex-delta.npz',vertex_ids=changed.astype(np.int32),before=before[changed],after=v[changed])
surface=dict(np.load(source/'atlas/surface.npz'));surface['world']=v
np.savez_compressed(out/'atlas/surface.npz',**surface)
meta=json.loads((source/'atlas/surface.json').read_text())
meta.update(scope='Actual official-MCP live-refined D static surface; source/art/deformation approval pending',
            payload_version='H-live-D',geometry_world_sha256=ah(v),surface_npz_path=str(out/'atlas/surface.npz'),
            surface_npz_sha256=sha(out/'atlas/surface.npz'),assembly_geometry_path=str(out/'geometry.npz'),
            atlas_path=str(source/'atlas/atlas.npz'),native_saved=False)
(out/'atlas/surface.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
assembly=json.loads((source/'assembly.json').read_text())
assembly['initial_construction_only']=assembly['collars']['neck']['geometric_section_tangents']
assembly['collars']['neck']['geometric_section_tangents']={
    'method':'Replaced by inspected live radial/upper fairing/oval-section edits; no original exactG1 claim',
    'current_source':'Official MCP evaluated editable coordinates exported from live Blender',
    'cut_endpoints_unchanged':True}
assembly.update(status='LIVE D frozen only for actual batch gray/source review; NOT ART or native promotion',
                assembly_geometry_sha256=sha(out/'geometry.npz'),world_sha256=ah(v),
                triangles_sha256=ah(d['triangles']),atlas_path=str(source/'atlas/atlas.npz'),
                collar_rows_path=str(ROOT/'.mia-cache/body-h/shape/assembly/collar-rows.npz'),
                source_payload=dict(path=str(source/'geometry.npz'),sha256=sha(source/'geometry.npz')))
(out/'assembly.json').write_text(json.dumps(assembly,indent=2)+'\n',encoding='utf8')
operations={}
for name in ['neck-operation','upper-fair-operation','cap-operation','neck-oval-operation']:
    path=ROOT/'.mia-cache/body-h/live'/(name+'.json')
    operations[name]=dict(path=str(path),sha256=sha(path))
record=dict(scope='Actually edited live state captured for deterministic review, not modeled in background',
            geometry=dict(path=str(out/'geometry.npz'),sha256=sha(out/'geometry.npz')),
            surface=dict(path=str(out/'atlas/surface.npz'),sha256=sha(out/'atlas/surface.npz')),
            atlas=dict(path=str(source/'atlas/atlas.npz'),sha256=sha(source/'atlas/atlas.npz')),
            world_sha256=ah(v),changed_vertices=len(changed),head_vertices_exact=len(head),
            Ewaist_arm_rows_exact=True,operations=operations,
            protected_native_sha256=sha(ROOT/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'),
            capacity=capacity,native_saved=False,art_accepted=False)
(out/'live-capture.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status='ACTUAL_LIVE_D_EXPORTED_NOT_ART',world_sha256=ah(v),changed_vertices=len(changed),output=str(out))))
