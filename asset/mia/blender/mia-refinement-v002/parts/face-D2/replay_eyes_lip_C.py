"""Actual painted gray-mauve fatigue/lip delta; B nose remains separate."""
from pathlib import Path
import sys,importlib.util,hashlib,json,argparse
import bpy
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('nose_B',P/'replay_nose_B.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);A=B.A;h=A.h
S=P/'native/Mia_v002_FacialPaint_B.blend';SHA='9aa3dce60c47505f3d33f99ca176361ad90b92140532d4d7e93e20dc4c1cf665'
ART=P/'art/Mia_GrayMauve_Lip_C.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def apply():
    expected=json.loads((P/'audit/B-material-preconditions.json').read_text())
    uv_expected=json.loads((P/'audit/baseline-guards.json').read_text())['owners']
    assert sha(ART)==expected['C_art_sha256']
    for name in A.SLOTS:
        ob=bpy.data.objects[name];mat=ob.material_slots[0].material
        assert mat.name=='MIA_v002_'+name+'_NoseB'
        assert h.jhash(h.graph(mat.node_tree))==expected['graphs'][mat.name]
        assert A.uvhash(ob)==uv_expected[name]['UV']['UVMap']
    paint=bpy.data.images.load(str(ART),check_existing=False);paint.name='MIA_v002_GrayMauveLip_C_sRGB';paint.colorspace_settings.name='sRGB';paint.pack()
    for name in A.SLOTS:
        ob=bpy.data.objects[name];old=ob.material_slots[0].material;old.use_fake_user=True
        mat=old.copy();mat.name='MIA_v002_'+name+'_RefinedC';n=mat.node_tree.nodes;l=mat.node_tree.links
        uv=n['V30_ActualFaceUV'];xyz=n['V002_ActualUV_RegionSplit'];control=n['V30_ACTUAL_LID_FEATURE_DATA']
        tex=n.new('ShaderNodeTexImage');tex.name='V002C_GrayMauveLip_Paint_sRGB';tex.image=paint;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector'])
        sep=n.new('ShaderNodeSeparateColor');sep.name='V002C_OriginalFeatureData';sep.mode='RGB';l.new(control.outputs['Color'],sep.inputs['Color'])
        def math(op,x,y):
            q=n.new('ShaderNodeMath');q.name='V002C_'+op;q.operation=op
            for i,v in enumerate([x,y]):
                if hasattr(v,'node'):l.new(v,q.inputs[i])
                else:q.inputs[i].default_value=v
            return q.outputs[0]
        def box(x1,y1,x2,y2):
            return math('MULTIPLY',math('MULTIPLY',math('GREATER_THAN',xyz.outputs['X'],x1),math('LESS_THAN',xyz.outputs['X'],x2)),math('MULTIPLY',math('GREATER_THAN',xyz.outputs['Y'],y1),math('LESS_THAN',xyz.outputs['Y'],y2)))
        eyes=math('MAXIMUM',box(.20,.30,.44,.48),box(.56,.30,.80,.48))
        fatigue=math('MULTIPLY',eyes,sep.outputs['Red'])
        lip=math('MULTIPLY',box(.42,.205,.58,.282),control.outputs['Alpha'])
        weight=math('MAXIMUM',fatigue,lip)
        mix=n.new('ShaderNodeMixRGB');mix.name='V002C_FatigueLip_KeepBNoseAndAFold';l.new(weight,mix.inputs[0]);l.new(n['V002B_NoseOnly_AEyes_OriginalLip'].outputs[0],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],n['V30_DirectSourcePigment_NoCleanup'].inputs['Color2'])
        mat['V002C_scope']='Only painted lower-fatigue R support in2strict eye rectangles and lip alpha belowV.282. B nose/upper crease retained. New pigment hue/value, no gain/opacity/light or geometry change.'
        ob.material_slots[0].material=mat

def retained_C(mat,old):
    new=h.graph(mat.node_tree);orig=h.graph(old.node_tree);new['name']=orig['name']
    new['nodes']=[v for v in new['nodes'] if not v['name'].startswith('V002C_')]
    new['links']=[v for v in new['links'] if not v[0].startswith('V002C_') and not v[2].startswith('V002C_')]
    orig['links']=[v for v in orig['links'] if not (v[0]=='V002B_NoseOnly_AEyes_OriginalLip' and v[2]=='V30_DirectSourcePigment_NoCleanup' and v[3]=='Color2')]
    new['links']=sorted(new['links']);orig['links']=sorted(orig['links'])
    return h.jhash(new)==h.jhash(orig) and A.material_drivers(mat)==A.material_drivers(old)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audit-only',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    assert sha(S)==SHA
    owners,raw,mats,images=h.snapshot(S);scene=A.scene_record();O=P/'native/Mia_v002_FacialPaint_C.blend'
    pre={'native':str(S),'sha256':SHA,'C_art_sha256':sha(ART),'graphs':{bpy.data.objects[n].material_slots[0].material.name:h.jhash(h.graph(bpy.data.objects[n].material_slots[0].material.node_tree)) for n in A.SLOTS}}
    if not args.audit_only:
        (P/'audit/B-material-preconditions.json').write_text(json.dumps(pre,indent=2));assert not O.exists();apply();assert A.scene_record()==scene;bpy.ops.wm.save_as_mainfile(filepath=str(O))
    digest=sha(O);now,unused,nowmats,nowimages=h.snapshot(O)
    checks={
        'all_B_geometry_topology_UV_keys_weights_drivers_modifiers_exact':all(h.jhash({k:v for k,v in d.items() if k!='materials'})==h.jhash({k:v for k,v in now[n].items() if k!='materials'}) for n,d in owners.items()),
        'only_three_slot0_materials_changed':all(h.jhash(now[n]['materials'][1:])==h.jhash(d['materials'][1:]) if n in A.SLOTS else h.jhash(now[n]['materials'])==h.jhash(d['materials']) for n,d in owners.items()),
        'all_B_original_graphs_and_packed_images_retained':all(nowmats.get(n)==v for n,v in mats.items()) and all(nowimages.get(n)==v for n,v in images.items()),
        'all_scene_pose_camera_light_world_color_exact':A.scene_record()==scene,
        'C_copies_keep_every_B_node_driver_light_and_nose_fold_link':all(retained_C(bpy.data.objects[n].material_slots[0].material,bpy.data.materials['MIA_v002_'+n+'_NoseB']) for n in A.SLOTS),
        'C_image_packed_sRGB_exact':any(v['packed']==sha(ART) and v['colorspace']=='sRGB' for v in nowimages.values()),
        'input_B_unchanged':sha(S)==SHA,
        'candidate_C_unchanged_by_audit':sha(O)==digest,
    }
    report={'input':str(S),'input_sha256':SHA,'candidate':str(O),'candidate_sha256':digest,'art':str(ART),'art_sha256':sha(ART),'checks':checks,'all_checks_pass':all(checks.values()),'art_acceptance':'UNVERIFIED; actual gray-mauve fatigue and lip render proof pending. Original geometry/UV retained for later deformation review.'}
    path=P/'audit'/('C-fresh-reopen-guard.json' if args.audit_only else 'C-build-reopen-guard.json');path.write_text(json.dumps(report,indent=2));assert all(checks.values()),checks
    print('V002_EYES_LIP_C_GUARDS_PASS',digest,str(path),flush=True)
if __name__=='__main__':main()
