"""Portable guarded three-slot material delta; never copies a source scene."""
from pathlib import Path
import argparse,hashlib,json,sys,importlib.util
import bpy
import numpy as np

P=Path(__file__).resolve().parent
C=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
BASE=C/'blender/mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend'
BASE_SHA='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a'
ART=P/'art/Mia_FatigueCreaseNose_A.png'
ART_SHA='27eaffd7f6b53537389b61f7f0f3b7109c71fba340af5be54fcf8c3295155cf8'
SLOTS={'MIA_V27_SharedHeadBody':'V30_Face_SourceIllustrated','V28G_InnerLid_-1':'V30_V28G_InnerLid_-1_SourceRootFade','V28G_InnerLid_1':'V30_V28G_InnerLid_1_SourceRootFade'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('guard_helpers',P/'guard_helpers.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

def uvhash(ob):
    return h.digest(h.arr(ob.data.uv_layers['UVMap'].data,'uv',2).tobytes())

def material_drivers(mat):
    ad=mat.node_tree.animation_data
    if not ad:return []
    return [{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[(v.name,v.type,[(t.id.name if t.id else None,t.data_path) for t in v.targets]) for v in f.driver.variables]} for f in ad.drivers]

def retained_copy(mat,old):
    graph=h.graph(mat.node_tree);original=h.graph(old.node_tree)
    graph['name']=original['name']
    graph['nodes']=[n for n in graph['nodes'] if not n['name'].startswith('V002_')]
    graph['links']=[link for link in graph['links'] if not link[0].startswith('V002_') and not link[2].startswith('V002_')]
    original['links']=[link for link in original['links'] if not (link[0]=='V30_SOURCE_PAINT_sRGB' and link[2]=='V30_DirectSourcePigment_NoCleanup' and link[3]=='Color2')]
    graph['links']=sorted(graph['links']);original['links']=sorted(original['links'])
    return h.jhash(graph)==h.jhash(original) and material_drivers(mat)==material_drivers(old)

def scene_record():
    s=bpy.context.scene
    def val(x):
        if hasattr(x,'name'):return x.name
        return h.value(x)
    obs={}
    for ob in s.objects:
        r={'matrix_world':[list(v) for v in ob.matrix_world],'hide_render':ob.hide_render,'hide_viewport':ob.hide_viewport,'hide_get':ob.hide_get(),'parent':ob.parent.name if ob.parent else None,'parent_type':ob.parent_type,'parent_bone':ob.parent_bone}
        if ob.type in {'CAMERA','LIGHT'}:
            r['data']={p:val(getattr(ob.data,p)) for p in (['type','lens','ortho_scale','clip_start','clip_end','shift_x','shift_y'] if ob.type=='CAMERA' else ['type','energy','color','shape','size','size_y','shadow_soft_size']) if hasattr(ob.data,p)}
        if ob.type=='ARMATURE':r['pose']={b.name:[list(v) for v in b.matrix_basis] for b in ob.pose.bones}
        if ob.type=='MESH' and ob.data.shape_keys:r['active_keys']={k.name:k.value for k in ob.data.shape_keys.key_blocks}
        obs[ob.name]=r
    return {'objects':obs,'world':h.graph(s.world.node_tree) if s.world and s.world.use_nodes else None,'frame':s.frame_current,'camera':s.camera.name if s.camera else None,'render':{k:val(getattr(s.render,k)) for k in ['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','use_freestyle']},'color':{k:val(getattr(s.view_settings,k)) for k in ['view_transform','look','exposure','gamma']}}

def apply():
    """Apply to the current scene only after exact material and UV preconditions."""
    expected=json.loads((P/'audit/baseline-guards.json').read_text())
    assert sha(ART)==ART_SHA
    for name,oldname in SLOTS.items():
        ob=bpy.data.objects[name]
        assert ob.material_slots[0].material.name==oldname,(name,'slot changed')
        assert h.jhash(h.graph(ob.material_slots[0].material.node_tree))==expected['material_graphs'][oldname],(name,'active material changed')
        assert uvhash(ob)==expected['owners'][name]['UV']['UVMap'],(name,'face UV changed; re-evaluate rather than silently refit')
    paint=bpy.data.images.load(str(ART),check_existing=False);paint.name='MIA_v002_FatigueCreaseNose_A_sRGB';paint.colorspace_settings.name='sRGB';paint.pack()
    created=[]
    for name,oldname in SLOTS.items():
        ob=bpy.data.objects[name];old=ob.material_slots[0].material
        old.use_fake_user=True
        mat=old.copy();mat.name='MIA_v002_'+name+'_PaintA';nodes=mat.node_tree.nodes;links=mat.node_tree.links
        oldpaint=nodes['V30_SOURCE_PAINT_sRGB'];uv=nodes['V30_ActualFaceUV']
        newpaint=nodes.new('ShaderNodeTexImage');newpaint.name='V002_RefinedPaint_A_sRGB';newpaint.image=paint;newpaint.extension='EXTEND';newpaint.interpolation='Linear';links.new(uv.outputs[0],newpaint.inputs['Vector'])
        sep=nodes.new('ShaderNodeSeparateXYZ');sep.name='V002_ActualUV_RegionSplit';links.new(uv.outputs[0],sep.inputs[0])
        region=nodes.new('ShaderNodeMapRange');region.name='V002_EyesNose_KeepOriginalLip';region.clamp=True;region.interpolation_type='SMOOTHSTEP';region.inputs['From Min'].default_value=.29;region.inputs['From Max'].default_value=.31;region.inputs['To Min'].default_value=0.;region.inputs['To Max'].default_value=1.;links.new(sep.outputs['Y'],region.inputs['Value'])
        mix=nodes.new('ShaderNodeMixRGB');mix.name='V002_PaintA_EyesNose_OriginalLip';links.new(region.outputs['Result'],mix.inputs[0]);links.new(oldpaint.outputs['Color'],mix.inputs[1]);links.new(newpaint.outputs['Color'],mix.inputs[2])
        links.new(mix.outputs['Color'],nodes['V30_DirectSourcePigment_NoCleanup'].inputs['Color2'])
        mat['V002_scope']='Only new imagegen paint through existing actual lid-root selectors above UVV0.29..0.31. Old lip, original maps/materials, geometry, UV, keys, weights, lighting path preserved.'
        ob.material_slots[0].material=mat;created.append(mat.name)
    return created

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--native',default=str(BASE));ap.add_argument('--sha256',default=BASE_SHA);ap.add_argument('--output',default=str(P/'native/Mia_v002_FacialPaint_A.blend'));ap.add_argument('--audit-only',action='store_true')
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    src=Path(args.native).resolve();out=Path(args.output).resolve()
    assert out.is_relative_to(P) and sha(src)==args.sha256
    expected=json.loads((P/'audit/baseline-guards.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(src),use_scripts=False);scene_before=scene_record()
    if not args.audit_only:
        assert not out.exists(),'Use a new immutable candidate output'
        apply();out.parent.mkdir(parents=True,exist_ok=True)
        assert scene_record()==scene_before,'Material-only delta changed a scene control'
        bpy.ops.wm.save_as_mainfile(filepath=str(out))
    candidate_sha=sha(out)
    owners,raw,mats,images=h.snapshot(out)
    allowed=set(SLOTS)
    checks={
        'original_geometry_topology_UV_keys_namedweights_drivers_modifiers_exact':all(h.jhash({k:v for k,v in d.items() if k!='materials'})==h.jhash({k:v for k,v in owners[n].items() if k!='materials'}) for n,d in expected['owners'].items()),
        'only_three_face_wall_slot0_materials_changed':all(h.jhash(owners[n]['materials'][1:])==h.jhash(d['materials'][1:]) if n in allowed else h.jhash(owners[n]['materials'])==h.jhash(d['materials']) for n,d in expected['owners'].items()),
        'all_original_material_graphs_and_constants_exact':all(mats.get(n)==v for n,v in expected['material_graphs'].items()),
        'all_original_packed_images_and_colorspaces_exact':all(images.get(n)==v for n,v in expected['images'].items()),
        'all_pose_camera_light_world_color_render_records_exact':scene_record()==scene_before,
        'new_paint_packed_sRGB_and_exact':any(v['packed']==ART_SHA and v['colorspace']=='sRGB' and v['size']==[1254,1254] for v in images.values()),
        'new_materials_retain_all_original_nodes_drivers_and_light_links':all(retained_copy(bpy.data.objects[n].material_slots[0].material,bpy.data.materials[old]) for n,old in SLOTS.items()),
        'input_native_unchanged':sha(src)==args.sha256,
        'candidate_unchanged_by_audit':sha(out)==candidate_sha,
    }
    report={'input_native':str(src),'input_sha256':args.sha256,'candidate':str(out),'candidate_sha256':candidate_sha,'art':str(ART),'art_sha256':ART_SHA,'checks':checks,'all_checks_pass':all(checks.values()),'scope':'Fresh reopen material/map delta only; technical preservation is not art acceptance.','new_materials':[owners[n]['materials'][0] for n in SLOTS]}
    path=P/'audit'/('fresh-reopen-guard.json' if args.audit_only else 'candidate-guard.json');path.write_text(json.dumps(report,indent=2))
    assert all(checks.values()),checks
    print('V002_FRESH_MATERIAL_GUARDS_PASS',candidate_sha,str(path),flush=True)

if __name__=='__main__':main()
