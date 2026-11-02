"""D repaint plus actual32lip selection, preserving C and all input geometry."""
from pathlib import Path
import sys,importlib.util,hashlib,json,argparse
import bpy
P=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('eyes_C',P/'replay_eyes_lip_C.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C);A=C.A;h=A.h
S=P/'native/Mia_v002_FacialPaint_C.blend';SHA='548c945e53fca91ef90e57fad2043b9f5c7034d308ef89958f4ef51b66f1b118'
ART=P/'art/Mia_SmoothFatigue_TracedLip_D.png';CONTROL=P/'controls-D/D_Actual32Lip_FatigueControls_RGBA.exr'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def apply():
    pre=json.loads((P/'audit/C-material-preconditions.json').read_text());trace=json.loads((P/'controls-D/actual32-mouth-UV.json').read_text());uvpre=json.loads((P/'audit/baseline-guards.json').read_text())['owners']
    palette=json.loads((P/'controls-D/paint-background-samples.json').read_text())
    assert sha(ART)==pre['D_art_sha256'] and sha(CONTROL)==trace['control_sha256']
    assert palette['art_sha256']==sha(ART)
    for name in A.SLOTS:
        ob=bpy.data.objects[name];mat=ob.material_slots[0].material
        assert mat.name=='MIA_v002_'+name+'_RefinedC' and h.jhash(h.graph(mat.node_tree))==pre['graphs'][mat.name]
        assert A.uvhash(ob)==uvpre[name]['UV']['UVMap']
    paint=bpy.data.images.load(str(ART),check_existing=False);paint.name='MIA_v002_SmoothFatigueLip_D_sRGB';paint.colorspace_settings.name='sRGB';paint.pack()
    control=bpy.data.images.load(str(CONTROL),check_existing=False);control.name='MIA_v002_D_Actual32LipControls';control.colorspace_settings.name='Non-Color';control.alpha_mode='CHANNEL_PACKED';control.pack()
    for name in A.SLOTS:
        ob=bpy.data.objects[name];old=ob.material_slots[0].material;old.use_fake_user=True;mat=old.copy();mat.name='MIA_v002_'+name+'_RefinedD2';n=mat.node_tree.nodes;l=mat.node_tree.links
        uv=n['V30_ActualFaceUV'];xyz=n['V002_ActualUV_RegionSplit'];direct=n['V30_DirectSourcePigment_NoCleanup'];oldfac=direct.inputs['Fac'].links[0].from_socket
        tex=n.new('ShaderNodeTexImage');tex.name='V002D_PaintedSmoothFatigueLip_sRGB';tex.image=paint;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector'])
        data=n.new('ShaderNodeTexImage');data.name='V002D_Actual32Mouth_Data';data.image=control;data.extension='EXTEND';l.new(uv.outputs[0],data.inputs['Vector'])
        sep=n.new('ShaderNodeSeparateColor');sep.name='V002D_ActualSupportChannels';sep.mode='RGB';l.new(data.outputs['Color'],sep.inputs['Color'])
        def math(op,x,y):
            q=n.new('ShaderNodeMath');q.name='V002D_'+op;q.operation=op
            for i,v in enumerate([x,y]):
                if hasattr(v,'node'):l.new(v,q.inputs[i])
                else:q.inputs[i].default_value=v
            return q.outputs[0]
        def value(name,x):
            q=n.new('ShaderNodeValue');q.name=name;q.outputs[0].default_value=x;return q.outputs[0]
        def rgb(name,x):
            q=n.new('ShaderNodeRGB');q.name='V002D_'+name;q.outputs[0].default_value=(*x,1.);return q.outputs[0]
        def vector(op,x,y):
            q=n.new('ShaderNodeVectorMath');q.name='V002D_Vector'+op;q.operation=op
            for i,v in enumerate([x,y]):
                if hasattr(v,'node'):l.new(v,q.inputs[i])
                else:q.inputs[i].default_value=v
            return q.outputs[0]
        def mix(f,x,y,name,mode='MIX'):
            q=n.new('ShaderNodeMixRGB');q.name='V002D_'+name;q.blend_type=mode
            for i,v in enumerate([f,x,y]):
                if hasattr(v,'node'):l.new(v,q.inputs[i])
                else:q.inputs[i].default_value=v
            return q.outputs[0]
        def box(x1,y1,x2,y2):return math('MULTIPLY',math('MULTIPLY',math('GREATER_THAN',xyz.outputs['X'],x1),math('LESS_THAN',xyz.outputs['X'],x2)),math('MULTIPLY',math('GREATER_THAN',xyz.outputs['Y'],y1),math('LESS_THAN',xyz.outputs['Y'],y2)))
        fatigue_enable=value('V002D_FatigueAmendmentEnabled',1.)
        lip_enable=value('V002D_LipAmendmentEnabled',1.)
        eye_roi=math('MAXIMUM',box(.20,.30,.44,.48),box(.56,.30,.80,.48))
        fatigue=math('MULTIPLY',math('MULTIPLY',eye_roi,math('GREATER_THAN',sep.outputs['Red'],.0001)),fatigue_enable)
        lip=math('MULTIPLY',data.outputs['Alpha'],lip_enable)
        lip_ownership=math('GREATER_THAN',lip,.0001)
        # Transfer the authored pigment contrast, not imagegen's lighter blank skin.
        # All sample colors are measured from this unchanged generated image.
        prior=n['V29_OriginalVsSurfaceBypass'].outputs['Color']
        left=rgb('MeasuredBlankSkin_Left',palette['left_fatigue_base']['linearRGB_mean'])
        right=rgb('MeasuredBlankSkin_Right',palette['right_fatigue_base']['linearRGB_mean'])
        base=mix(math('LESS_THAN',xyz.outputs['X'],.5),right,left,'MeasuredEyeBase')
        fatigue_ratio=vector('MINIMUM',vector('DIVIDE',tex.outputs['Color'],base),(1.,1.,1.))
        fatigue_signal=mix(1.,prior,fatigue_ratio,'AuthoredFatigueContrastOnPrior','MULTIPLY')
        lip_base=rgb('MeasuredBlankSkin_Lip',palette['lip_base']['linearRGB_mean'])
        lip_ratio=vector('DIVIDE',tex.outputs['Color'],lip_base)
        dark_lip=vector('MINIMUM',lip_ratio,(1.,1.,1.))
        edge=math('DIVIDE',sep.outputs['Blue'],math('MAXIMUM',data.outputs['Alpha'],.000001))
        lip_factor=mix(edge,dark_lip,lip_ratio,'HighlightOnlyOnActualLowerEdge')
        lip_signal=mix(1.,prior,lip_factor,'AuthoredLipContrastOnPrior','MULTIPLY')
        signal=mix(fatigue,n['V002B_NoseOnly_AEyes_OriginalLip'].outputs[0],fatigue_signal,'Paint_KeepBNoseAndAFold')
        signal=mix(lip_ownership,signal,lip_signal,'Actual32LipOverFatigue')
        l.new(signal,direct.inputs['Color2'])
        # Replace the old broad lip ownership, never overlay it with a new patch.
        domain=box(*trace['lip_replacement_domain'])
        refined=math('MULTIPLY',lip,n['V30_NoseLipGain'].outputs[0])
        if 'V30_FaceRootFade' in n:refined=math('MULTIPLY',refined,n['V30_FaceRootFade'].outputs[0])
        else:
            at=n.new('ShaderNodeAttribute');at.name='V002D_OriginalWallRootFade';at.attribute_name='V29_CosmeticRootFade';refined=math('MULTIPLY',refined,at.outputs['Fac'])
        newfac=math('ADD',math('MULTIPLY',math('SUBTRACT',1.,domain),oldfac),math('MULTIPLY',domain,refined));l.new(newfac,direct.inputs['Fac'])
        mat['V002D_scope']='Smooth authored contrast normalized to measured blank skin; no transferred pale background. Dark-only fatigue; lip highlight only on actual32lower-edge support. C coarse/pale route bypassed; B nose/A fold and all light/geometry/UV/keys retained.'
        ob.material_slots[0].material=mat

def retained_D(mat,old):
    new=h.graph(mat.node_tree);orig=h.graph(old.node_tree);new['name']=orig['name']
    new['nodes']=[v for v in new['nodes'] if not v['name'].startswith('V002D_')];new['links']=[v for v in new['links'] if not v[0].startswith('V002D_') and not v[2].startswith('V002D_')]
    orig['links']=[v for v in orig['links'] if not (v[2]=='V30_DirectSourcePigment_NoCleanup' and v[3] in ['Color2','Fac'])]
    new['links']=sorted(new['links']);orig['links']=sorted(orig['links'])
    return h.jhash(new)==h.jhash(orig) and A.material_drivers(mat)==A.material_drivers(old)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audit-only',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    assert sha(S)==SHA;owners,raw,mats,images=h.snapshot(S);scene=A.scene_record();O=P/'native/Mia_v002_FacialPaint_D2.blend'
    if not args.audit_only:
        pre={'native':str(S),'sha256':SHA,'D_art_sha256':sha(ART),'graphs':{bpy.data.objects[n].material_slots[0].material.name:h.jhash(h.graph(bpy.data.objects[n].material_slots[0].material.node_tree)) for n in A.SLOTS}}
        (P/'audit/C-material-preconditions.json').write_text(json.dumps(pre,indent=2));assert not O.exists();apply();assert A.scene_record()==scene;bpy.ops.wm.save_as_mainfile(filepath=str(O))
    digest=sha(O);now,unused,nowmats,nowimages=h.snapshot(O)
    checks={
      'all_C_geometry_topology_UV_keys_weights_drivers_modifiers_exact':all(h.jhash({k:v for k,v in d.items() if k!='materials'})==h.jhash({k:v for k,v in now[n].items() if k!='materials'}) for n,d in owners.items()),
      'only_three_slot0_materials_changed':all(h.jhash(now[n]['materials'][1:])==h.jhash(d['materials'][1:]) if n in A.SLOTS else h.jhash(now[n]['materials'])==h.jhash(d['materials']) for n,d in owners.items()),
      'all_C_original_graphs_and_packed_images_retained':all(nowmats.get(n)==v for n,v in mats.items()) and all(nowimages.get(n)==v for n,v in images.items()),
      'all_scene_pose_camera_light_world_color_exact':A.scene_record()==scene,
      'D2_copies_keep_C_nodes_drivers_and_all_light_links':all(retained_D(bpy.data.objects[n].material_slots[0].material,bpy.data.materials['MIA_v002_'+n+'_RefinedC']) for n in A.SLOTS),
      'D_art_and_actual32_data_packed_exact':all(any(v['packed']==sha(path) and v['colorspace']==cs for v in nowimages.values()) for path,cs in [(ART,'sRGB'),(CONTROL,'Non-Color')]),
      'input_C_unchanged':sha(S)==SHA,'candidate_D_unchanged_by_audit':sha(O)==digest}
    report={'input':str(S),'input_sha256':SHA,'candidate':str(O),'candidate_sha256':digest,'art':str(ART),'art_sha256':sha(ART),'controls':str(CONTROL),'controls_sha256':sha(CONTROL),'checks':checks,'all_checks_pass':all(checks.values()),'art_acceptance':'UNVERIFIED; C independent face-map review failed. D requires actual quick and source4 review, not approval from map existence.'}
    file=P/'audit'/('D2-fresh-reopen-guard.json' if args.audit_only else 'D2-build-reopen-guard.json');file.write_text(json.dumps(report,indent=2));assert all(checks.values()),checks
    print('V002_SMOOTH_D2_GUARDS_PASS',digest,str(file),flush=True)
if __name__=='__main__':main()
