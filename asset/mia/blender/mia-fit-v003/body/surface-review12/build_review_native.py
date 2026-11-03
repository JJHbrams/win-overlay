"""Build two static review scenes on a fresh private R3b. Save ONLY after gates.

Importing exposes build_scenes() for unsaved material preflight, never saves.
"""
from pathlib import Path
import sys,json,importlib.util
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_review,review_fixture as fixture
def read_config():return json.loads((P/'selected-review.json').read_text())
def appearance_api(config):
    path=Path(config['appearance_api'])
    if not path.is_absolute():path=(P/path).resolve()
    if not path.exists():path=Path(config['appearance_fallback_root'])/'install_material.py'
    spec=importlib.util.spec_from_file_location('review12_appearance',path);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);return api
def build_scenes(config,proof_dir):
    assert config['bare_seam_approved'],'Bare surface gate has not passed'
    geometry=P/config['geometry'];surface=P/config['surface'];assert fixture.sha(geometry)==config['geometry_sha256'] and fixture.sha(surface)==config['surface_sha256']
    maps=Path(config['maps']);maps=maps if maps.is_absolute() else (P/maps).resolve()
    if not maps.exists():maps=Path(config['appearance_fallback_root'])/Path(config['maps']).name
    bake=json.loads((maps/'bake-report.json').read_text());assert bake['surface_input_sha256']==config['surface_sha256']
    api=appearance_api(config);mats={state:api.create_material(maps,variant=variant,name='MIA12_Review_'+state) for state,variant in [('SkinOnly','skin'),('Underwear','underwear')]}
    packing={state:api.pack_material_images(mat,relative_prefix='//MIA_Review12Maps/') for state,mat in mats.items()}
    proof_dir=Path(proof_dir);proof_dir.mkdir(exist_ok=True)
    atlas=P/config['atlas'];assert fixture.sha(atlas)==config['atlas_sha256']
    body,proof=install_review.apply(mats['Underwear'],geometry_path=geometry,atlas_path=atlas,proof_path=proof_dir/'installed-source-proof.json',packing_path=proof_dir/'head-normal-packing.json')
    original=bpy.data.objects['MIA_V27_SharedHeadBody'];scene=bpy.context.scene;scene.name='Underwear';fixture.setup(scene)
    slot=proof['body_material_index'];assert slot==12;body.material_slots[slot].link='OBJECT';body.material_slots[slot].material=mats['Underwear']
    skin=scene.copy();skin.name='SkinOnly';assert skin.collection!=scene.collection and body.name in skin.collection.objects
    skin.collection.objects.unlink(body);skinbody=body.copy();skinbody.data=body.data;skinbody.name='MIA_Review12_StaticJoinedBody_SkinOnly';skin.collection.objects.link(skinbody);skinbody.material_slots[slot].link='OBJECT';skinbody.material_slots[slot].material=mats['SkinOnly']
    assert skinbody.data==body.data and body.name not in skin.objects and skinbody.name not in scene.objects
    for s in [scene,skin]:
        for layer in s.view_layers:original.hide_set(True,view_layer=layer)
        s['MIA12_scope']='STATIC fullbody review. No production UV/rig/animation/fullMia ART approval. Saved R3b head/hair, no head scaling.'
        s['MIA12_geometry_sha256']=config['geometry_sha256'];s['MIA12_surface_sha256']=config['surface_sha256'];s['MIA12_material_variant']=s.name
    for state,ob in [('Underwear',body),('SkinOnly',skinbody)]:
        ob['MIA12_static_review_body']=True;ob['MIA12_state']=state
    if bpy.context.window:bpy.context.window.scene=scene
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.clip_start=.1;space.clip_end=10;space.region_3d.view_location=(0,-.015,.87);space.region_3d.view_distance=2.;space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion();space.region_3d.view_perspective='ORTHO';space.shading.type='MATERIAL';space.shading.use_scene_lights=True;space.shading.use_scene_world=True
    result=dict(source_native_sha256=fixture.sha(bpy.data.filepath),geometry=config['geometry'],geometry_sha256=config['geometry_sha256'],surface_sha256=config['surface_sha256'],shared_mesh=body.data.name,body_objects={state:ob.name for state,ob in [('Underwear',body),('SkinOnly',skinbody)]},body_slot=slot,head_slots_DATA_unchanged=True,UV_active=proof['installed_old_UV_active_state'],materials={k:api.audit_material(m) for k,m in mats.items()},packed_images=packing,scope=scene['MIA12_scope'],native_saved=False)
    (proof_dir/'two-scene-proof.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    return dict(Underwear=scene,SkinOnly=skin),dict(Underwear=body,SkinOnly=skinbody),mats,api,result
def main():
    config=read_config();assert config['bare_seam_approved'] and config['material_preflight_approved'] and config.get('proportion_review_approved',False),'Root actual material/proportion gates pending'
    out=P/'native/Mia_v0.0.3_SurfaceReview12.blend';out.parent.mkdir(exist_ok=True);assert not out.exists(),'Do not overwrite frozen review native'
    scenes,bodies,mats,api,proof=build_scenes(config,P/'native-build-proof')
    bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    (P/'native/native-save.json').write_text(json.dumps(dict(path=str(out),sha256=fixture.sha(out),bytes=out.stat().st_size,scope=proof['scope'],saved_before_any_final_capture=True),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('REVIEW12_NATIVE_SAVED',str(out),fixture.sha(out),flush=True)
if __name__=='__main__':main()
