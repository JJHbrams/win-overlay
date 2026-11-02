"""Bounded source08/16 existing-smile calibration; no new geometry or keys."""
import bpy

def apply_to_current_scene():
    owner=bpy.data.objects['MIA_V27_Foundation_Face']
    path='key_blocks["Face.M_F00_000_00_Fcl_MTH_Fun"].value'
    curve=next(f for f in owner.data.shape_keys.animation_data.drivers if f.data_path==path)
    before=curve.driver.expression
    assert before.count('0.35*p8')==1 and before.count('0.22*p16')==1, 'Smile preset recipe differs; do not overwrite'
    curve.driver.expression=before.replace('0.35*p8','0.65*p8').replace('0.22*p16','0.45*p16')
    ctrl=bpy.data.objects['Mia_FacialControls_v002']
    ctrl['MiaSmileCalibration']='R3 source08Fun0.65/source16Fun0.45 after actual same-camera existing-range probe. Original arrays/manual channel/other presets unchanged. Broader source likeness remains open.'
    ctrl.update_tag();bpy.context.view_layer.update()
    return dict(changed_driver=path,before=before,after=curve.driver.expression,
        tested_values={'P08_MTH_Fun':.65,'P16_MTH_Fun':.45},
        new_geometry_or_keys=False,neutral_and_manual_values_unchanged=True,
        scope='Small closed-smile readability; source eye/lip paint and overall ART are not certified.')
