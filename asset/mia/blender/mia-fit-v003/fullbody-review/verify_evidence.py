"""Check integrated construction evidence integrity; never awards ART PASS."""
from pathlib import Path
import hashlib, json

P = Path(__file__).resolve().parent
body = P.parent/'body'
sha = lambda f: hashlib.sha256(Path(f).read_bytes()).hexdigest()
manifest = json.loads((body/'checkpoint-files.json').read_text(encoding='utf-8'))
errors = []
for item in manifest['files']:
    file = body/item['path']
    if not file.is_file() or file.stat().st_size != item['bytes'] or sha(file) != item['sha256']:
        errors.append('Integrated producer mismatch: '+item['path'])
records = json.loads((P/'actual-R4-neck/render-records.json').read_text(encoding='utf-8'))
assert {r['view'] for r in records} == {'front','oblique'}
native = P.parents[1]/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
for row in records:
    if sha(native) != row['native_sha256']:
        errors.append('Baseline native changed')
    if sha(body/'scaffold-fullbody/guide-data.json') != row['guide_data_sha256']:
        errors.append('Fullbody guide changed')
    if sha(body/'scaffold-fullbody/neck-supplement.json') != row['neck_data_sha256']:
        errors.append('Neck supplement changed')
    if sha(P/'actual-R4-neck'/Path(row['path']).name) != row['sha256']:
        errors.append('Actual guide image changed: '+row['view'])
    assert row['curves_rendered'] == 207 and row['original_objects_rendered'] == 0
    assert row['construction_meshes_rendered'] == 0 and row['native_saved'] is False
    assert row['camera']['projection'] == 'ORTHO'
    assert row['camera']['pixel_aspect'] == [1,1]
report = dict(integrated_producer_files_checked=len(manifest['files']),
              actual_guide_views_checked=len(records), errors=errors,
              evidence_integrity_pass=not errors,
              regional_guide_coverage='independent visual review PASS, guide only',
              target01_form='FAIL: persistent inferior shelf; not promoted',
              fitted_surface_art_approved=False, new_native_saved=False)
(P/'evidence-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
assert not errors
