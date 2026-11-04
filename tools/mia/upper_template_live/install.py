"""Install the unselected template03 mesh into the existing live body actor.

Root invokes through official MCP only, after leaving its hair review. No other
actor, native, texture bake or rig is changed. Restore retains the old mesh.
"""
from pathlib import Path
import hashlib
import importlib.util
import json

import bpy
import numpy as np

# Load this revision directly: live Blender retains normal import caches between
# failed trial calls, so an ordinary import could silently reuse the old helper.
_spec = importlib.util.spec_from_file_location('mia_upper_template03_diagnostics', Path(__file__).with_name('diagnostic_weights.py'))
diagnostics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diagnostics)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/shape/assembly/template03'
KEY = 'MIA_UpperTemplate03'
BODY = 'MIA_Review12_H_LiveRepair'
BASE_SHA = '69d4d4f0ea907da2474bc74f4b55312971d137f0911bdf9089fc02509a6bf25a'


def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def coordinates(mesh):
    a = np.empty((len(mesh.vertices), 3), np.float32)
    mesh.vertices.foreach_get('co', a.ravel()); return a


def actor_properties(body):
    return {ob.name: dict(data_pointer=int(ob.data.as_pointer()) if ob.data else None,
                         matrix=[list(row) for row in ob.matrix_world],
                         hidden=bool(ob.hide_get()), render_hidden=bool(ob.hide_render),
                         materials=[int(slot.material.as_pointer()) if slot.material else None for slot in ob.material_slots] if ob.type == 'MESH' else None)
            for ob in bpy.context.scene.objects if ob != body}


def normal_angles(a, b):
    a = a.astype(float); b = b.astype(float)
    a /= np.maximum(np.linalg.norm(a, axis=-1)[..., None], 1e-30)
    b /= np.maximum(np.linalg.norm(b, axis=-1)[..., None], 1e-30)
    return np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), np.sum(a*b, axis=-1)))


def main():
    namespace = bpy.app.driver_namespace
    assert KEY not in namespace, 'Do not stack a trial'
    assert 'MIA_HairReviewState' not in namespace, 'Root must exit borrowed hair review first'
    receipt = OUT/'live-install.json'; assert not receipt.exists(), 'Immutable install receipt exists'
    report = json.loads((OUT/'build.json').read_text())
    technical = json.loads((OUT/'verification.json').read_text())
    assert not technical['errors'] and technical['candidate_sha256'] == report['candidate_sha256']
    path = OUT/'geometry.npz'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report['geometry_npz_sha256']
    d = dict(np.load(path)); body = bpy.data.objects[BODY]
    assert body.mode == 'OBJECT' and np.allclose(np.asarray(body.matrix_world), np.eye(4), atol=1e-7)
    old = body.data
    assert digest(coordinates(old)) == BASE_SHA
    assert not old.shape_keys and not body.modifiers, 'Only known static body may be swapped'
    group_metadata = diagnostics.require_known(body)
    old_deform = diagnostics.entries(old)
    if len(old_deform):
        assert old_deform['group'].min() >= 0 and old_deform['group'].max() < len(group_metadata['groups'])
    old_deform_sha = diagnostics.digest(old_deform)
    retained_deform = diagnostics.remap_retained(old_deform, d['baseline_vertex'], len(old.vertices))
    original_slots = [(slot.link, slot.material) for slot in body.material_slots]
    other_actors = actor_properties(body)
    old_uv_state = dict(active=old.uv_layers.active.name if old.uv_layers.active else None,
                        render=[u.name for u in old.uv_layers if u.active_render])
    meta_path = ROOT/'asset/mia/blender/mia-fit-v003/body/surface-review12'
    names = json.loads((meta_path/'donor.json').read_text())['uv_layers']
    assert set(old.uv_layers.keys()) <= set(names+['MIA_Review12UV']), 'Uninventoried UV layer'
    before_uv = {}
    for layer in old.uv_layers:
        values = np.empty((len(old.loops), 2), np.float32); layer.data.foreach_get('uv', values.ravel())
        before_uv[layer.name] = values.reshape(-1, 3, 2)
    head = d['source_part'] == 1; baseline_face = d['baseline_face'][head]
    assert (baseline_face >= 0).all()
    old_head_normals = np.asarray([n.vector[:] for n in old.corner_normals], np.float32).reshape(-1, 3, 3)[baseline_face]
    mesh = bpy.data.meshes.new('MIA_UpperTemplate03_STATIC_Unselected')
    gray = bpy.data.materials.new('MIA_UpperTemplate03_ProvisionalGray'); gray.use_nodes = True
    shader = next(n for n in gray.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (.23, .23, .23, 1)
    shader.inputs['Roughness'].default_value = .85; shader.inputs['Metallic'].default_value = 0
    installed = False
    try:
        mesh.from_pydata(d['world'].tolist(), [], d['triangles'].tolist()); mesh.update()
        for _, material in original_slots: mesh.materials.append(material)
        body_slot = len(mesh.materials); mesh.materials.append(gray)
        for fi, poly in enumerate(mesh.polygons):
            poly.material_index = int(d['triangle_materials'][fi]) if head[fi] else body_slot
            poly.use_smooth = True
        for i, name in enumerate(names):
            u = mesh.uv_layers.new(name=name, do_init=False)
            u.data.foreach_set('uv', d['old_loop_uv'][:, :, i, :].ravel())
        if 'MIA_Review12UV' in before_uv:
            u = mesh.uv_layers.new(name='MIA_Review12UV', do_init=False)
            u.data.foreach_set('uv', d['review_loop_uv'].ravel())
        if old_uv_state['active']:
            mesh.uv_layers.active_index = list(mesh.uv_layers.keys()).index(old_uv_state['active'])
        for layer in mesh.uv_layers: layer.active_render = layer.name in old_uv_state['render']
        uv_proof = {}
        for layer in mesh.uv_layers:
            values = np.empty((len(mesh.loops), 2), np.float32); layer.data.foreach_get('uv', values.ravel())
            actual = values.reshape(-1, 3, 2)[head]
            assert np.array_equal(actual, before_uv[layer.name][baseline_face]), ('Changed head UV', layer.name)
            uv_proof[layer.name] = digest(actual)
        attributes = json.loads((meta_path/'head-attributes.json').read_text())['attributes']
        attribute_values = np.load(meta_path/'head-attributes.npz')
        known = d['baseline_vertex'] >= 0
        head_ids = np.unique(d['triangles'][head]); old_head_ids = d['baseline_vertex'][head_ids]
        assert (old_head_ids >= 0).all()
        attribute_proof = {}
        for rec in attributes:
            assert rec['domain'] == 'POINT'
            old_attr = old.attributes.get(rec['name']); assert old_attr is not None, rec['name']
            dtype = attribute_values[rec['npz_key']].dtype
            values = np.empty((len(old.vertices), rec['dimension']), dtype=dtype)
            old_attr.data.foreach_get(rec['property'], values.ravel())
            new_values = np.zeros((len(mesh.vertices), rec['dimension']), dtype=dtype)
            new_values[known] = values[d['baseline_vertex'][known]]
            attr = mesh.attributes.new(rec['name'], rec['data_type'], 'POINT')
            attr.data.foreach_set(rec['property'], new_values.ravel())
            actual = np.empty_like(new_values); attr.data.foreach_get(rec['property'], actual.ravel())
            assert np.array_equal(actual[head_ids], values[old_head_ids]), rec['name']
            attribute_proof[rec['name']] = digest(actual[head_ids])
        supplied = np.zeros((len(mesh.polygons), 3, 3), np.float32)
        supplied[head] = d['source_corner_normals'][head]
        mesh.normals_split_custom_set(supplied.reshape(-1, 3).tolist())
        actual_normals = np.asarray([n.vector[:] for n in mesh.corner_normals], np.float32).reshape(-1, 3, 3)[head]
        supplied_angle = normal_angles(actual_normals, supplied[head])
        old_angle = normal_angles(actual_normals, old_head_normals)
        protected_faces = np.all(d['world'][d['triangles'][head], 2] >= 1.469, axis=1)
        assert float(supplied_angle[protected_faces].max()) < .05, 'Protected source WORLD normal roundtrip changed'
        assert digest(coordinates(mesh)) == report['candidate_sha256']
        proof = dict(report, status='Actual live unselected geometry trial; source/ART pending',
                     technical_verification='template03/verification.json: complete new-face triangle narrow phase and boundary/winding checks passed; not ART',
                     candidate_sha256=digest(coordinates(mesh)), before_sha256=BASE_SHA,
                     head_UV_actual_exact=uv_proof, head_named_POINT_attributes_actual_exact=attribute_proof,
                     head_source_WORLD_normal_input_exact=True,
                     actual_head_max_angle_to_supplied_degrees=float(supplied_angle.max()),
                     actual_protected_head_max_angle_to_supplied_degrees=float(supplied_angle[protected_faces].max()),
                     actual_head_max_angle_to_previous_packed_degrees=float(old_angle.max()),
                     normal_limit='Blender packed normal readback recorded separately; input vectors/UV/geometry exact, not false packed-byte equality',
                     body_UV_final=False, geometry_only_body_material='ProvisionalGray',
                     body_object=BODY, mesh_name=mesh.name, all_other_actor_properties_held=False,
                     legacy_H_rows='Old rows remain for exact restore; while trial active use template03/rows.npz, not stale H indices',
                     native_saved=False, art_accepted=False)
        namespace[KEY] = dict(before_mesh=old, after_mesh=mesh, body_object=body,
                              before_material_slots=original_slots, gray_material=gray,
                              before_group_metadata=group_metadata, before_deform_sha256=old_deform_sha,
                              after_expected_deform_sha256=diagnostics.digest(retained_deform),
                              report=proof, after_rows=dict(np.load(OUT/'rows.npz')))
        transfer = diagnostics.prepare_fresh_mesh(bpy, mesh, retained_deform, group_metadata)
        assert diagnostics.metadata(body) == group_metadata, 'Original group definitions changed'
        assert diagnostics.digest(diagnostics.entries(old)) == old_deform_sha, 'Old mesh deform weights changed'
        body.data = mesh
        for slot in body.material_slots: slot.link = 'DATA'
        assert diagnostics.metadata(body) == group_metadata, 'Swapped candidate group metadata differs'
        assert diagnostics.digest(diagnostics.entries(mesh)) == transfer['sha256'], 'Swapped candidate weights differ'
        assert diagnostics.metadata_for_mesh(bpy, old) == group_metadata, 'Old mesh group definitions changed'
        assert diagnostics.digest(diagnostics.entries(old)) == old_deform_sha, 'Old mesh deform weights changed'
        proof['diagnostic_groups'] = dict(metadata=group_metadata, old_entries=len(old_deform),
                                         old_deform_sha256=old_deform_sha, old_deform_weights_held=True,
                                         retained_transfer=transfer, unknown_groups_allowed=False,
                                         original_mesh_group_definitions_held=True,
                                         candidate_definition_preparation='Exact copies on fresh Mesh via unlinked temporary Object')
        bpy.context.view_layer.update(); installed = True
        assert digest(coordinates(body.data)) == report['candidate_sha256']
        assert actor_properties(body) == other_actors, 'Another actor property changed'
        proof['all_other_actor_properties_held'] = True
        receipt.write_text(json.dumps(proof, indent=2)+'\n', encoding='utf8')
        print(json.dumps(dict(status=proof['status'], candidate_sha256=proof['candidate_sha256'],
                              vertices=len(mesh.vertices), polygons=len(mesh.polygons), body_object=BODY,
                              exact_head_UV=True, exact_head_named_attributes=True,
                              actual_protected_normal_max_degrees=proof['actual_protected_head_max_angle_to_supplied_degrees'],
                              diagnostic_group_names=[g['name'] for g in group_metadata['groups']],
                              retained_diagnostic_entries=transfer['entries'],
                              diagnostic_weight_batches=transfer['unique_weight_batches'],
                              old_deform_sha256=old_deform_sha, retained_deform_sha256=transfer['sha256'],
                              old_deform_weights_held=True,
                              all_other_actor_properties_held=True, native_saved=False)))
    except Exception:
        if installed or body.data == mesh:
            body.data = old
            for slot, (link, material) in zip(body.material_slots, original_slots):
                slot.link = link; slot.material = material
            bpy.context.view_layer.update()
        if group_metadata['groups']:
            body.vertex_groups.active_index = group_metadata['active_index']
        assert diagnostics.metadata(body) == group_metadata
        assert diagnostics.digest(diagnostics.entries(old)) == old_deform_sha
        namespace.pop(KEY, None)
        if mesh.users == 0: bpy.data.meshes.remove(mesh)
        if gray.users == 0: bpy.data.materials.remove(gray)
        raise


main()
