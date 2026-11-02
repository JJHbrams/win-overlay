"""Compose only selected bounded components on the current scene.

No native replay/save inside apply(). New source-bound body, fine fringe and
central rear fill are separate pending modules; this does not certify them.
"""
from pathlib import Path
import importlib.util
import bpy

P=Path(__file__).resolve().parent.parent
def module(path):
    path=Path(path);spec=importlib.util.spec_from_file_location('mia_v003_'+path.stem,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def apply(*, diagnostic_guides=True, provisional_brow_ink=True):
    results=[]
    results.append(module(P/'eyes/apply_lower_lid.py').apply())
    results.append(module(P/'eyes/apply_aligned_crease.py').apply(P/'eyes/upper-crease-visible-C.json'))
    results.append(module(P/'hair/apply_baked_v29_crown.py').apply(P/'hair/v29-pigment',mode='combined'))
    results.append(module(P/'hair/rear-loop-cleanup/apply_loop_mask.py').apply(P/'hair/rear-loop-cleanup'))
    if provisional_brow_ink:
        results.append(module(P/'brow-visibility-analysis/candidate/partial_brow_display.py').apply_to_current_scene(strength=.60))
    if diagnostic_guides:
        full=module(P/'body/install_fullbody_scaffold.py').install()
        neck=module(P/'body/install_neck_supplement.py').install(full)
        full.hide_render=neck.hide_render=True
        for obj in full.all_objects:obj.hide_set(True)
        results.append(dict(diagnostic_guides=full.name,neck=neck.name,hidden=True))
    bpy.context.view_layer.update()
    return dict(components=results,body_surface_changed=False,new_fine_fringe_applied=False,
        central_rear_fill_applied=False,provisional_brow_ink_is_geometry_completion=False,
        native_saved=False,art_approved=False)
