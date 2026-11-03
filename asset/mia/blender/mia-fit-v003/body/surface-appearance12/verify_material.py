"""Load final PNGs through actual Blender nodes, without render/native save."""
from pathlib import Path
import sys
import json
import bpy

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
import install_material

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
folder = Path(args[0]) if args else P/'maps-E-AA'
report_file = Path(args[1]) if len(args)>1 else folder/'material-route-proof.json'
bake = json.loads((folder/'bake-report.json').read_text(encoding='utf-8'))
expected = {Path(row['path']).stem: row for row in bake['files']}
materials = []
actual_materials = []
for variant in ['skin', 'underwear']:
    material = install_material.create_material(folder, variant=variant)
    actual_materials.append(material)
    initial = install_material.audit_material(material)
    assert initial['controls']['UnderwearMode'] == float(variant == 'underwear')
    assert len(initial['images']) == 5
    assert initial['UV_layer'] == 'MIA_Review12UV'
    for row in initial['images']:
        match = expected[Path(row['filepath']).stem]
        assert row['expected_file_sha256'] == match['sha256']
        assert row['color_space'] == match['color_space']
        assert row['UV_vector_linked']
    install_material.set_controls(material, variant='underwear' if variant=='skin' else 'skin',
                                  clavicle_strength=0, color_only=True)
    switched = install_material.audit_material(material)
    assert switched['controls']['UnderwearMode'] == float(variant == 'skin')
    assert switched['controls']['ClavicleStrength'] == 0
    assert switched['controls']['ColorOnly'] == 1
    assert switched['variant'] != initial['variant']
    packed = install_material.pack_material_images(material, relative_prefix='//MIA_Review12Maps/')
    assert packed == install_material.pack_material_images(material, relative_prefix='//MIA_Review12Maps/')
    packed_audit = install_material.audit_material(material)
    assert all(row['packed'] and row['packed_sha256']==row['expected_file_sha256'] for row in packed_audit['images'])
    materials.append(dict(initial=initial, toggled=switched, packed=packed,
                          portable_path_audit=packed_audit))
assert actual_materials[0].node_tree.as_pointer() != actual_materials[1].node_tree.as_pointer()
install_material.set_controls(actual_materials[0], variant='underwear', clavicle_strength=0)
install_material.set_controls(actual_materials[1], variant='skin', clavicle_strength=1)
independent = [install_material.audit_material(material)['controls'] for material in actual_materials]
assert [row['UnderwearMode'] for row in independent] == [1, 0]
assert [row['ClavicleStrength'] for row in independent] == [0, 1]
report = dict(status='PASS actual Blender material API with final target PNGs',
              blender_version=bpy.app.version_string,
              surface_sha256=bake['surface_input_sha256'], materials=materials,
              independent_material_controls=independent,
              independent_node_trees=True,
              render_called=False, source_native_loaded=False, geometry_changed=False,
              limits='Image routes/colorspaces/control toggles and original-byte packing verified; native assignment/save/fresh-reopen, neck seam and appearance still require integrator review.')
report_file.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
print('MIA12_FINAL_MAP_NODE_ROUTES_PASS', flush=True)
