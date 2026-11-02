"""Fresh-reopen actual saved guide points against source-constrained payloads."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np

P=Path(__file__).resolve().parent
meta=json.loads((P/'guide-scene.json').read_text(encoding='utf-8'))
native=P/Path(meta['path']).name
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
assert sha(native)==meta['sha256']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
rows=[]
for file,prefix in [('guide-data.json','V003_GUIDE_FULL4_'),('neck-supplement.json','V003_GUIDE_NECK_')]:
    data=json.loads((P.parent/'body/scaffold-fullbody'/file).read_text(encoding='utf-8'))
    for item in data['curves']:
        obj=bpy.data.objects[prefix+item['name']]
        assert obj.type=='CURVE' and obj.get('guide_only')
        expected=np.asarray(item['points'],dtype=np.float32)
        actual=np.asarray([p.co[:] for p in obj.data.splines[0].bezier_points],dtype=np.float32)
        assert np.array_equal(actual,expected),(obj.name,'saved section points changed')
        assert np.array_equal(np.asarray(obj.matrix_world),np.eye(4))
        assert bool(obj.data.splines[0].use_cyclic_u)==bool(item['closed'])
        rows.append(dict(name=obj.name,points=len(actual),points_bitexact=True))
assert len(rows)==207
assert sum(o.type=='MESH' for o in bpy.data.objects)==17
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert sha(native)==meta['sha256']
report=dict(saved_native_sha256=meta['sha256'],fresh_reopen_curves_checked=len(rows),
            all_source_payload_points_bitexact=True,rows=rows,
            production_model_modified=False,surface_art_approved=False)
(P/'guide-scene-fresh-points.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('STANDALONE_GUIDE_FRESH_POINTS_PASS',len(rows),flush=True)
