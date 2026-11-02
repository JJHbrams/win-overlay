"""Nose-only generated paint over A; every A eye/lip route is retained."""
from pathlib import Path
import sys,importlib.util,hashlib,json,argparse
import bpy
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('paint_A',P/'replay_material_delta.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A);h=A.h
S=P/'native/Mia_v002_FacialPaint_A.blend';SHA='57e9f7f945675ac206b0f49d5608f29ceb5131f45ce4f3d4b0761e8cc9a5298b'
ART=P/'art/Mia_Nose_B.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def apply():
    expected=json.loads((P/'audit/A-material-preconditions.json').read_text())
    uv_expected=json.loads((P/'audit/baseline-guards.json').read_text())['owners']
    assert sha(ART)==expected['nose_art_sha256']
    for name in A.SLOTS:
        ob=bpy.data.objects[name];mat=ob.material_slots[0].material
        assert mat.name=='MIA_v002_'+name+'_PaintA'
        assert h.jhash(h.graph(mat.node_tree))==expected['graphs'][mat.name]
        assert A.uvhash(ob)==uv_expected[name]['UV']['UVMap']
    paint=bpy.data.images.load(str(ART),check_existing=False);paint.name='MIA_v002_Nose_B_sRGB';paint.colorspace_settings.name='sRGB';paint.pack()
    for name in A.SLOTS:
        ob=bpy.data.objects[name];old=ob.material_slots[0].material;old.use_fake_user=True
        mat=old.copy();mat.name='MIA_v002_'+name+'_NoseB';n=mat.node_tree.nodes;l=mat.node_tree.links
        uv=n['V30_ActualFaceUV'];xyz=n['V002_ActualUV_RegionSplit']
        tex=n.new('ShaderNodeTexImage');tex.name='V002B_NosePaint_sRGB';tex.image=paint;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector'])
        def math(op,x,y):
            q=n.new('ShaderNodeMath');q.name='V002B_'+op;q.operation=op
            for i,v in enumerate([x,y]):
                if hasattr(v,'node'):l.new(v,q.inputs[i])
                else:q.inputs[i].default_value=v
            return q.outputs[0]
        # Strict rectangular containment is ownership, not authored pigment.
        # Existing anatomical alpha support supplies its original feather.
        containment=math('MULTIPLY',math('GREATER_THAN',xyz.outputs['X'],.455),math('LESS_THAN',xyz.outputs['X'],.545))
        containment=math('MULTIPLY',containment,math('MULTIPLY',math('GREATER_THAN',xyz.outputs['Y'],.30),math('LESS_THAN',xyz.outputs['Y'],.45)))
        weight=math('MULTIPLY',containment,n['V30_ACTUAL_LID_FEATURE_DATA'].outputs['Alpha'])
        mix=n.new('ShaderNodeMixRGB');mix.name='V002B_NoseOnly_AEyes_OriginalLip';l.new(weight,mix.inputs[0]);l.new(n['V002_PaintA_EyesNose_OriginalLip'].outputs[0],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],n['V30_DirectSourcePigment_NoCleanup'].inputs['Color2'])
        mat['V002B_scope']='Only generated nose paint within UVrectangle[.455,.30,.545,.45] and existing actual alpha support. Every A eye/crease/makeup and original lip input retained; no light/gain change.'
        ob.material_slots[0].material=mat

def retained_B(mat,old):
    new=h.graph(mat.node_tree);orig=h.graph(old.node_tree);new['name']=orig['name']
    new['nodes']=[v for v in new['nodes'] if not v['name'].startswith('V002B_')]
    new['links']=[v for v in new['links'] if not v[0].startswith('V002B_') and not v[2].startswith('V002B_')]
    orig['links']=[v for v in orig['links'] if not (v[0]=='V002_PaintA_EyesNose_OriginalLip' and v[2]=='V30_DirectSourcePigment_NoCleanup' and v[3]=='Color2')]
    new['links']=sorted(new['links']);orig['links']=sorted(orig['links'])
    return h.jhash(new)==h.jhash(orig) and A.material_drivers(mat)==A.material_drivers(old)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audit-only',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    assert sha(S)==SHA
    owners,raw,mats,images=h.snapshot(S);scene=A.scene_record()
    O=P/'native/Mia_v002_FacialPaint_B.blend'
    pre={'native':str(S),'sha256':SHA,'nose_art_sha256':sha(ART),'graphs':{bpy.data.objects[n].material_slots[0].material.name:h.jhash(h.graph(bpy.data.objects[n].material_slots[0].material.node_tree)) for n in A.SLOTS}}
    if not args.audit_only:
        (P/'audit/A-material-preconditions.json').write_text(json.dumps(pre,indent=2))
        assert not O.exists();apply();assert A.scene_record()==scene;bpy.ops.wm.save_as_mainfile(filepath=str(O))
    digest=sha(O);now,unused,nowmats,nowimages=h.snapshot(O)
    checks={
        'all_A_geometry_topology_UV_keys_weights_drivers_modifiers_exact':all(h.jhash({k:v for k,v in d.items() if k!='materials'})==h.jhash({k:v for k,v in now[n].items() if k!='materials'}) for n,d in owners.items()),
        'only_three_slot0_materials_changed':all(h.jhash(now[n]['materials'][1:])==h.jhash(d['materials'][1:]) if n in A.SLOTS else h.jhash(now[n]['materials'])==h.jhash(d['materials']) for n,d in owners.items()),
        'all_A_original_graphs_and_packed_images_retained':all(nowmats.get(n)==v for n,v in mats.items()) and all(nowimages.get(n)==v for n,v in images.items()),
        'all_scene_pose_camera_light_world_color_exact':A.scene_record()==scene,
        'B_copies_keep_every_A_node_driver_light_and_eye_lip_link':all(retained_B(bpy.data.objects[n].material_slots[0].material,bpy.data.materials['MIA_v002_'+n+'_PaintA']) for n in A.SLOTS),
        'nose_image_packed_sRGB_exact':any(v['packed']==sha(ART) and v['colorspace']=='sRGB' for v in nowimages.values()),
        'input_A_unchanged':sha(S)==SHA,
        'candidate_B_unchanged_by_audit':sha(O)==digest,
    }
    report={'input':str(S),'input_sha256':SHA,'candidate':str(O),'candidate_sha256':digest,'art':str(ART),'art_sha256':sha(ART),'checks':checks,'all_checks_pass':all(checks.values()),'art_acceptance':'UNVERIFIED; generated B narrower/frayed nose plane still risks wedge appearance. Await actual quickproof and moved light.'}
    path=P/'audit'/('B-fresh-reopen-guard.json' if args.audit_only else 'B-build-reopen-guard.json');path.write_text(json.dumps(report,indent=2));assert all(checks.values()),checks
    print('V002_NOSE_B_GUARDS_PASS',digest,str(path),flush=True)
if __name__=='__main__':main()
