"""Source-sheet head-roll estimates; actual3D pose, never2D image rotation.

Visible eye/lid axes are provisional with several-degree drawing/occlusion
uncertainty. This does not accept face proportions or prove a full3D pose fit.
"""
from pathlib import Path
import bpy,json
P=Path(__file__).resolve().parent
ROLL={1:5.,2:13.,3:10.,4:18.,5:9.,6:15.,7:9.,8:9.,9:15.,10:14.,11:11.,12:14.,13:10.,14:7.,15:6.,16:13.5}

def apply_to_current_scene():
    ctrl=bpy.data.objects['Mia_FacialControls_v002'];rig=bpy.data.objects['MIA_V06_RIG']
    path='pose.bones["J_Bip_C_Head"].rotation_euler'
    fc=next(f for f in rig.animation_data.drivers if f.data_path==path and f.array_index==2)
    d=fc.driver;before=d.expression
    assert '18*p4' in before and '15*p6' in before and '14*p10' in before, 'Head source recipe changed; do not overwrite'
    rows=json.loads((P/'expression-intents.json').read_text())['panels']
    for row in rows:
        name='p'+str(row['panel'])
        if name not in d.variables:
            v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id=ctrl;v.targets[0].data_path=f'["P{row["panel"]:02}_{row["id"]}"]'
    d.expression='(m+s*('+ '+'.join(f'{ROLL[row["panel"]]:g}*p{row["panel"]}' for row in rows)+')/max(1,t))*0.0174532925199'
    ctrl['MiaHeadRollCalibration']='R3 source-sheet visible eye/lid-axis estimates. P04/06 held after actual projected-axis audit; other under-tilted initial cases corrected provisionally. Yaw/pitch/gaze and full source likeness remain unapproved. HeadPoseStrength0 isolates facial shape.'
    ctrl.update_tag();bpy.context.view_layer.update()
    return dict(changed_driver=path,before=before,after=d.expression,source_roll_deg=ROLL,
        neutral_all_zero_controls_unchanged=True,source_image_warp=False,
        limits='Artist pose estimates from original equal-aspect eye/lid crops, several-degree feature/occlusion uncertainty. No source proportion or full3D pose acceptance; actual16panel review required.')
