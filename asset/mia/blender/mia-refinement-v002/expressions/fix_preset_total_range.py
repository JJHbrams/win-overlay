"""Fix the aggregate preset property's runtime clamp; preserve all formulas."""
import bpy

def apply_to_current_scene():
    ctrl=bpy.data.objects['Mia_FacialControls_v002']
    panels=[k for k in ctrl.keys() if k.startswith('P') and k[:3][1:].isdigit()]
    assert len(panels)==16
    driver=next(f for f in ctrl.animation_data.drivers if f.data_path=='["PresetTotal"]')
    assert driver.driver.type=='SUM' and len(driver.driver.variables)==16
    before=ctrl.id_properties_ui('PresetTotal').as_dict()
    assert before['max'] in [1.,16.],before
    assert all(ctrl.id_properties_ui(k).as_dict()['max']==1. for k in panels)
    ctrl.id_properties_ui('PresetTotal').update(min=0.,max=16.,soft_min=0.,soft_max=16.)
    ctrl['MiaPresetNormalization']='Aggregate PresetTotal range0..16, matching sixteen individual0..1 presets. Original SUM driver and per-channel normalization formulas retained. Fixes confirmed evaluated clamp at1 for totals above1.'
    ctrl.update_tag();bpy.context.view_layer.update()
    after=ctrl.id_properties_ui('PresetTotal').as_dict()
    assert after['max']==after['soft_max']==16.
    return dict(owner=ctrl.name,property='PresetTotal',before_UI=before,after_UI=after,
        driver_formula_changed=False,geometry_material_or_pose_changed=False,
        scope='Runtime aggregate range only. Single presets/neutral unchanged; mixed presets require actual fresh verification.')
