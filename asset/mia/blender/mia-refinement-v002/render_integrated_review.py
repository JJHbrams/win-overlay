"""Actual immutable-scene source views,16 expressions and bounded head/gaze checks."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, math, runpy, sys
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--native', required=True)
ap.add_argument('--sha256', required=True)
ap.add_argument('--tag', required=True)
ap.add_argument('--suite', choices=['source', 'expressions', 'orbit', 'critical', 'intermediates'], required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:])
old = P.parent/'mia-visible-art-v30/render_native_review.py'
sys.argv = [str(old), '--', '--native', a.native, '--sha256', a.sha256,
            '--tag', a.tag, '--preset', 'source', '--only', '__setup_only_no_frames__']
env = runpy.run_path(str(old), run_name='v002_final_review_setup')
render = env['render']
g = render.__globals__
out = P/'review'/a.tag/a.suite
out.mkdir(parents=True, exist_ok=True)
g['out'] = out
env['a'].only = ''
ctrl = bpy.data.objects['Mia_FacialControls_v002']
base = copy.deepcopy(env['spec'])
base['resolution'] = [512,512]
rows = json.loads((P/'expressions/expression-intents.json').read_text())['panels']
poses = []

def reset():
    for name in ctrl.keys():
        if name.startswith('P') and name[:3][1:].isdigit() or name.startswith('Manual') or name in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']:
            ctrl[name] = 0.
    ctrl['Strength'] = ctrl['HeadPoseStrength'] = ctrl['GazeStrength'] = 1.
    ctrl.update_tag()
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

def actual(label, spec=base, hair_off=False, neutral=False):
    # The factory configures all archived lights off. Record before rendering.
    active = [o for o in bpy.context.scene.objects if o.type == 'LIGHT' and not o.hide_render]
    assert len(active) == 3 and set(o.name for o in active) == set(o.name for o in env['lamps'])
    dental = [o for o in bpy.context.scene.objects if 'DentalCrowns' in o.name]
    assert len(dental) == 2 and all(not o.hide_render for o in dental)
    render(label, spec, hair_off, neutral)
    poses.append(dict(id=label, controls={n:ctrl[n] for n in ctrl.keys() if isinstance(ctrl[n],(int,float)) and ctrl[n]},
        head_local_euler=list(env['head'].rotation_euler),
        active_lights_before=[dict(name=o.name, watts=o.data.energy) for o in active],
        dental_objects_visible=[o.name for o in dental],
        effective_dental_hide=ctrl.get('_EffectiveSmallMouthDentalHide'),
        source_aperture={k.name:k.value for k in bpy.data.objects['MIA_V27_SharedHeadBody'].data.shape_keys.key_blocks if k.name.startswith('Mia.v003.SourceSurprise.')},
        iris_gaze={o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.name.startswith('Mia.Gaze.') and k.value} for o in bpy.context.scene.objects if o.name.startswith('V28G_Iris_')}))

reset()
if a.suite == 'source':
    for row in env['pkg']['views']:
        v = copy.deepcopy(row['candidate_camera'])
        # Preserve original camera raster for exact baseline/candidate pairing.
        for suffix, hide, gray in [('hairON',False,False),('hairOFF',True,False),('neutral',True,True)]:
            actual(row['id']+'-'+suffix, v, hide, gray)
    for row in env['pkg']['views']:
        v=copy.deepcopy(row['candidate_camera']);v['resolution']=[512,512];v['ortho_scale']=.72
        v['matrix'][2][3]-=.08
        actual(row['id']+'-hairWide',v,False,False)
        originals={o.name:list(o.data.materials) for o in env['hair']}
        for o in env['hair']:
            for i in range(len(o.data.materials)):o.data.materials[i]=env['gray']
        actual(row['id']+'-hairWide-neutral',v,False,True)
        for o in env['hair']:
            for i,m in enumerate(originals[o.name]):o.data.materials[i]=m
elif a.suite == 'expressions':
    for row in rows:
        reset()
        ctrl[f"P{row['panel']:02}_{row['id']}"] = 1.
        ctrl.update_tag()
        bpy.context.scene.frame_set(row['panel']+1)
        bpy.context.view_layer.update()
        for suffix, hide in [('hairON',False),('hairOFF',True)]:
            actual(f"P{row['panel']:02}-{row['id']}-"+suffix, base, hide)
    reset()
    for prop, val in [('GazeX',1.),('GazeX',-1.),('GazeY',1.),('GazeY',-1.),('Manual_EYE_Close',.5),('Manual_EYE_Close',1.)]:
        reset(); ctrl[prop]=val; ctrl.update_tag(); bpy.context.scene.frame_set(len(poses)+20); bpy.context.view_layer.update()
        actual('probe-'+prop+'-'+str(val), base, True)
    for panel in [4,6,10]:
        reset(); row=rows[panel-1]; ctrl[f"P{panel:02}_{row['id']}"]=1.; ctrl.update_tag(); bpy.context.scene.frame_set(panel+1); bpy.context.view_layer.update()
        v=copy.deepcopy(env['pkg']['views'][1]['candidate_camera']);v['resolution']=[512,512]
        actual(f'head-pose-P{panel:02}-profile',v,False)
elif a.suite == 'intermediates':
    cases=[
        ('auto-half-hide',{'P01_neutral_observe':.5,'P12_surprised':.5},.5),
        ('normalized-grin-blend',{'P12_surprised':1.,'P10_toothy_grin':1.},.25),
        ('surprise-right-half-close',{'Manual_EYE_Surprised':.8,'Manual_EYE_Close_R':.5,'Manual_MTH_A':.28,'ManualSmallMouthDentalHide':.5},.5),
        ('surprise-left-three-quarter-close',{'Manual_EYE_Surprised':.8,'Manual_EYE_Close_L':.75},0.)]
    for i,(label,values,expected) in enumerate(cases):
        reset();ctrl['HeadPoseStrength']=ctrl['GazeStrength']=0.
        for name,value in values.items():
            assert name in ctrl,name
            ctrl[name]=value
        ctrl.update_tag();bpy.context.scene.frame_set(i+101);bpy.context.view_layer.update()
        assert abs(ctrl['_EffectiveSmallMouthDentalHide']-expected)<1e-6,(label,ctrl['_EffectiveSmallMouthDentalHide'])
        actual(label,base,True)
elif a.suite in ['orbit','critical']:
    angles = [(f'{i:03}',i*15,8+17*math.sin(math.radians(i*30))) for i in range(24)] if a.suite=='orbit' else [
        ('highFront',0,45),('lowFront',0,-30),('lowRight',35,-30),('lowLeft',-35,-30),('highLeft',-35,40),('profileLow',85,-20)]
    for label,yaw,pitch in angles:
        y,p=math.radians(yaw),math.radians(pitch)
        target=Vector((0,0,1.55));cam=env['cam']
        cam.location=target+Vector((2*math.sin(y)*math.cos(p),-2*math.cos(y)*math.cos(p),2*math.sin(p)))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update()
        v=copy.deepcopy(base);v['matrix']=[list(r) for r in cam.matrix_world];v['ortho_scale']=.36 if a.suite=='orbit' else .29
        v['estimated_yaw_pitch_roll_deg']=[yaw,pitch,0]
        actual(label+'-production',v,a.suite=='critical')
        if a.suite=='critical':actual(label+'-neutral',v,True,True)
reset()
assert hashlib.sha256(Path(a.native).read_bytes()).hexdigest()==a.sha256
(out/'pose-control-records.json').write_text(json.dumps(dict(native=a.native,sha256=a.sha256,suite=a.suite,poses=poses,
    wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native_saved=False,
    scope='Actual Blender review; preset head/gaze angles remain estimates. P07 hand gesture is not a facial morph. No ART pass from render completion.'),indent=2)+'\n',encoding='utf-8')
print('V002_INTEGRATED_REVIEW_DONE',a.suite,len(poses),flush=True)
