"""Root integration entry point. Applies materials to CURRENT scene only."""
from pathlib import Path
import importlib.util
P=Path(__file__).resolve().parent
def _load(name,filename):
    spec=importlib.util.spec_from_file_location(name,P/filename);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def apply_to_current_scene():
    """No scene open/save, geometry mutation, camera/light/pose or Git changes.

    Requires the original V30 three skin/wall graphs and exact facial UV chart.
    Applies the D2 challenger; this function does not grant ART acceptance.
    Call only after root has reviewed the D2 result. Root must compare its
    current input/output owners and re-evaluate paint after form/UV changes.
    """
    A=_load('portable_A','replay_material_delta.py')
    B=_load('portable_B','replay_nose_B.py')
    C=_load('portable_C','replay_eyes_lip_C.py')
    D=_load('portable_D2','replay_smooth_D.py')
    A.apply();B.apply();C.apply();D.apply()
    return {name:'MIA_v002_'+name+'_RefinedD2' for name in A.SLOTS}
