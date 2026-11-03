"""Actual Blender-node API check only; no render/native save/source load."""
from pathlib import Path
import sys
import json
import bpy

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import install_material

folder = P / '_smoke'
folder.mkdir(exist_ok=True)
for name in ['SkinBaseColor', 'UnderwearBaseColor', 'UnderwearCoverage', 'ClavicleInk', 'ClavicleShade']:
    image = bpy.data.images.new('API_test_' + name, 8, 8)
    image.generated_color = (.8, .7, .6, 1)
    image.filepath_raw = str(folder / (name + '.png'))
    image.file_format = 'PNG'
    image.save()
records = []
for variant in ['skin', 'underwear']:
    material = install_material.create_material(folder, variant=variant)
    record = install_material.audit_material(material)
    assert record['UV_layer'] == 'MIA_Review12UV'
    assert record['controls']['UnderwearMode'] == float(variant == 'underwear')
    install_material.set_controls(material, clavicle_strength=0, color_only=1)
    switched = install_material.audit_material(material)
    assert switched['controls']['ClavicleStrength'] == 0 and switched['controls']['ColorOnly'] == 1
    records.append(dict(initial=record, toggle=switched))
report = dict(status='PASS actual Blender node API only', materials=records, render_called=False,
              source_native_loaded=False, source_or_geometry_changed=False,
              limits='Synthetic8x8 image controls; actual target maps/native appearance remain unverified.')
(P / 'material-api-smoke.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
print('MIA12_MATERIAL_API_PASS', flush=True)
