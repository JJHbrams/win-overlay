"""Keep the explicitly provisional modular WIP and make review visibility stable."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np
ns=bpy.app.driver_namespace;state=ns['MIA_CurvedRear03Base']
source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
assert hashlib.sha256(np.array([v.co[:] for v in source.data.vertices],np.float32).tobytes()).hexdigest()==state['source_raw_sha256']
assert 'source_fixture_flag_before_keep' not in state
state['source_fixture_flag_before_keep']=source.get('MIA12_source_hair_hide_render')
source['MIA12_source_hair_hide_render']=True
for ob in state['objects']:
    ob['MIA12_source_hair_hide_render']=False
    ob['MIA_working_part_status']='PROVISIONAL WORKING PART; whole source ART/rig unapproved'
state['provisional_keep']=True
ns['MIA_HairReviewState']['retained_replacement']=dict(source=source.name,namespace='MIA_CurvedRear03Base')
report=dict(selection='PROVISIONAL EDITABLE WORKING PART ONLY',
            original_Main_hidden_and_raw_exact=True,fixture_old_owner_excluded=True,
            new_actors=[o.name for o in state['objects']],
            source_fixture_flag_before_keep=state['source_fixture_flag_before_keep'],
            restore_script='tools/mia/face_surface_live/restore_supported_rear.py',
            actual_geometry_payload='.mia-cache/face-live/curved-rear03/actual-emergence/geometry.npz',
            payload_sha256='2b1a8508dfdcd7dc0d74958aaed4899f64486270a457b973fa9822ee98044de3',
            source_native_saved=False,ART=False)
p=(Path(__file__).resolve().parents[3]/'.mia-cache/face-live/curved-rear03/actual-emergence/working-part.json')
p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
