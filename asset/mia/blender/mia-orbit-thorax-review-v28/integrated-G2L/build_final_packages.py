"""Actual integrated-native review boards; immutable sources, uniform SRT only.

Run after render_face.py source4 and render_body.py geometry-clay. Paired
baseline pixels and scene records come from the corresponding frozen producer
review. These packages certify evidence coverage, never overall art approval.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import shutil

from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
REPO = P.parents[4]
EYE = Path('C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-orbit-review-v28')
BODY = Path('C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay/asset/mia/blender/mia-thorax-review-v28')
BASE = REPO / 'asset/mia/blender/mia-reference-finish-v22/face-rebuild-10/selected-v27'
NATIVE = P / 'Mia_Foundation_v28_G2L.blend'
FONT = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 21)


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def artifact(p):
    p = p.resolve()
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def transform(im, reg, render=False):
    s = reg['uniform_scale'] * (1000/768 if render else 1)
    angle = math.radians(reg['rotation_degrees'])
    c, t = math.cos(angle), math.sin(angle)
    x, y = reg['translation_xy']
    return im.convert('RGBA').transform((640, 640), Image.Transform.AFFINE,
        (c/s, t/s, -(c*x+t*y)/s, -t/s, c/s, (t*x-c*y)/s),
        Image.Resampling.BICUBIC, fillcolor=(237,242,246,255))


def face():
    original = read(BASE / 'reference-review.json')
    br = {r['id']: r for r in read(EYE/'renders/baseline-e9-corrected/source4-records.json')}
    cr = {r['id']: r for r in read(P/'renders/integrated/source4-records.json')}
    dest = P/'face-source4'
    dest.mkdir(exist_ok=True)
    rows = []
    for v in original['views']:
        name = v['id']
        ref = (BASE/v['reference']['path']).resolve()
        source = Image.open(ref).convert('RGBA')
        crop = v['reference']['crop_xyxy']
        cropped = source.crop(crop)
        cp = dest/(name+'-source-crop.png')
        cropped.save(cp)
        canvas = Image.new('RGBA', source.size, (237,242,246,255))
        canvas.paste(cropped, (crop[0],crop[1]))
        reg = copy.deepcopy(v['candidate_registration'])
        reg['normalization_basis'] = 'Frozen e9 source4 uniform SRT; actual768 render resolution adjustment only. Eye/chin span and roll normalized, excluded from independent proportion validation. Candidate not refitted.'
        images = [transform(canvas, v['reference_registration'])]
        for parent, mode in [(EYE,'hairON'),(EYE,'hairOFF'),(P,'hairOFF'),(P,'hairON')]:
            tag = 'baseline-e9-corrected' if parent == EYE else 'integrated'
            images.append(transform(Image.open(parent/'renders'/tag/(name+'-'+mode+'.png')), reg, True))
        board = Image.new('RGB',(3200,740),(237,242,246))
        draw = ImageDraw.Draw(board)
        labels = ['SOURCE / original aspect','e9 / hair ON','e9 / hair OFF','v28 G2+J / hair OFF','v28 G2+J / hair ON']
        for i,(tile,label) in enumerate(zip(images,labels)):
            board.paste(tile.convert('RGB'),(i*640,50))
            draw.text((i*640+12,12),label,font=FONT,fill=(24,38,49))
        draw.text((12,702), name+' | same actual camera/light/pose/display + frozen uniform SRT | local correction review',font=FONT,fill=(24,38,49))
        bp = dest/(name+'-source-baseline-integrated.png')
        board.save(bp)
        bc, cc = br[name+'-hairOFF']['camera'], cr[name+'-hairOFF']['camera']
        assert bc == cc, 'Actual scene mismatch: '+name
        rr = copy.deepcopy(reg)
        rr['uniform_scale'] *= 1000/768
        rows.append({'id':name,
            'reference':dict(artifact(ref),crop_xyxy=crop,crop_artifact=artifact(cp)),
            'baseline_render':artifact(EYE/'renders/baseline-e9-corrected'/(name+'-hairOFF.png')),
            'candidate_render':artifact(P/'renders/integrated'/(name+'-hairOFF.png')),
            'comparison_board':artifact(bp), 'baseline_camera':bc,'candidate_camera':cc,
            'reference_registration':v['reference_registration'],
            'baseline_registration':rr,'candidate_registration':copy.deepcopy(rr),
            'pose_uncertainty':v['pose_uncertainty'],
            'observed_differences':'Integrated actual saved native: flatter upper run, broader lower run, lateral turn and independent outer lashes; inward lid return and coordinated curved ocular carriers retain supported cheek. Hair-off columns expose previously occluded structure.',
            'unresolved':['Latest user feedback REOPENS contour acceptance: upper-lid inclination and upward noseward inner-canthus finish differ from art; eye H correction pending.','Whole-face identity/paint and hair are not fully accepted.','Source gaze, subtle pose and occluded anatomy remain uncertain.','Full42 expression combinations and final animation not validated.'],
            'material_mode':'Original production routes, actual connected review world and area rig recorded in camera metadata; all skin matte diagnostics available separately. Hair visibility only changes by labeled column.'})
    pkg={'schema_version':1,'part':'face','baseline_native':artifact(BASE/'native/e9c865412130-Mia_Foundation_v27.blend'),'candidate_native':artifact(NATIVE),'required_views':['front','profile','left_oblique','right_oblique'],'views':rows,'status':'Integrated bounded correction; package validation does not grant overall ART acceptance.'}
    (dest/'reference-review.json').write_text(json.dumps(pkg,indent=2),encoding='utf-8')


def body_camera(r):
    c,d=r['camera'],r['display']
    return {'projection':c['projection'],'matrix':c['matrix'],'ortho_scale':c['ortho_scale'],
        'frame':c['frame'],'active_shape_keys':c['active_keys'],
        'lighting':{'areas':r['lights'],'world_linear':[.18,.18,.18],'world_strength':.15,'other_lights_disabled':True},
        'color_management':{'view_transform':d['transform'],'look':d['look'],'exposure':d['exposure'],'gamma':d['gamma']},
        'resolution':c['resolution'],'pixel_aspect':c['pixel_aspect'],'lens_shift':c['lens_shift'],
        'actual_native_rig_pose':r['pose'],'freestyle':False,'engine':'BLENDER_EEVEE'}


def body():
    registration = read(P/'source4-uniform-G2L/registration.json')
    raw_b=read(BODY/'renders/baseline/geometry-clay/render-records.json')
    raw_c=read(P/'renders/integrated/geometry-clay/render-records.json')
    rows=[]
    for row in registration['views']:
        name=row['render_view']
        b,c=raw_b['records'][name],raw_c['records'][name]
        bc,cc=body_camera(b),body_camera(c)
        assert bc == cc, 'Actual body scene mismatch: '+name
        rr=row['source_registration']
        assert rr['scale_xy']==[rr['uniform_scale']]*2
        r={'uniform_scale':rr['uniform_scale'],'translation_xy':rr['translation_xy'],'rotation_degrees':0,
           'normalization_basis':'Source shoulder-to-waist span normalized to Z1.38..1.145m; that span is excluded from independent proportion validation.',
           'notes':'Original source aspect/color unchanged; crop and scalar scale/translation only; landmarks±10px, illustrated yaw uncertain.'}
        sr={'uniform_scale':1.,'translation_xy':[0.,0.],'rotation_degrees':0.,'normalization_basis':'Same700x800 orthographic canvas; common display crop only, no candidate fit.'}
        rows.append({'id':row['id'],'reference':dict(row['reference'],crop_xyxy=row['crop_xyxy']),
            'baseline_render':{'path':b['path'],'sha256':b['sha256']},
            'candidate_render':{'path':c['path'],'sha256':c['sha256']},'comparison_board':row['board'],
            'baseline_camera':bc,'candidate_camera':cc,'reference_registration':r,'baseline_registration':sr,'candidate_registration':copy.deepcopy(sr),
            'pose_uncertainty':{'source_yaw_degrees':rr['reference_yaw_estimate_degrees'],'yaw_uncertainty_degrees':rr['yaw_uncertainty_degrees'],'landmark_uncertainty_px':10,'support_note':'Source bra supports mass and hides the nude attachment; arms/pose differ.'},
            'observed_differences':'Actual G3 core-first foundation with new whole L soft mass. Source-informed apex placement retained; lower trajectory redistributes fullness and rolls into the inferior attachment instead of the previous straight/conical return. Core-only and rotating evidence are separate.',
            'unresolved':['Source bra obscures nude attachment; not an exact anatomical trace.','Pelvis/legs/hair/garments and full animation remain outside this correction.'],
            'material_mode':'Actual neutral diffuse geometry-only route; legacy outline disabled identically. Original production route reviewed separately.'})
    dest=P/'source4-uniform-G2L'
    pkg={'schema_version':1,'part':'body','baseline_native':artifact(BASE/'native/e9c865412130-Mia_Foundation_v27.blend'),'candidate_native':artifact(NATIVE),'required_views':['front','profile','back','oblique'],'views':rows,'status':'Actual integrated bounded thorax correction; art acceptance is a separate visual judgment.'}
    (dest/'reference-review.json').write_text(json.dumps(pkg,indent=2),encoding='utf-8')


if __name__=='__main__':
    face()
    body()
    print('INTEGRATED_SOURCE_PACKAGES_WRITTEN')
