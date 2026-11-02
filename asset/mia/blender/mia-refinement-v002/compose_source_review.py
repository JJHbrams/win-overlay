"""Source | frozen457 | integrated candidate, with unchanged uniform registration."""
from pathlib import Path
import argparse, copy, hashlib, json, math
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--before-records', required=True)
ap.add_argument('--after-records', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args()
out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
assert not (out/'reference-review.json').exists()
oldpath = P.parent/'mia-face-finish-v29/final-review/source-boards/reference-review.json'
old = json.loads(oldpath.read_text())
before = json.loads(Path(a.before_records).read_text())
after = json.loads(Path(a.after_records).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
by = lambda rows, name: next(x for x in rows if x['id']==name)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)

def transformed(im, reg):
    scale=reg['uniform_scale'];angle=math.radians(reg['rotation_degrees']);c,s=math.cos(angle),math.sin(angle);x,y=reg['translation_xy']
    return im.convert('RGBA').transform((640,640),Image.Transform.AFFINE,
        (c/scale,s/scale,-(c*x+s*y)/scale,-s/scale,c/scale,(s*x-c*y)/scale),
        Image.Resampling.BICUBIC,fillcolor=(237,242,246,255))

rows=[]
for r in old['views']:
    view=r['id'];src=(oldpath.parent/r['reference']['path']).resolve();im=Image.open(src).convert('RGBA')
    crop=r['reference']['crop_xyxy'];canvas=Image.new('RGBA',im.size,(237,242,246,255));canvas.paste(im.crop(crop),crop[:2])
    reg=copy.deepcopy(r['candidate_registration'])
    if view=='front':
        reg={'uniform_scale':1.1698146556808693,'rotation_degrees':0.,'translation_xy':[-142.01146815879025,-223.93878303771004],
             'normalization_basis':'Frozen opening-centre/IPD scalar and translation. IPD excluded from independent proportion acceptance. No eye-chin normalization or extra2D roll.'}
    else:
        reg['notes']='Provisional historical pose/display normalization retained unchanged for both models; absolute facial proportion and roll are excluded from acceptance.'
    b=by(before,view+'-hairOFF');c=by(after,view+'-hairOFF');h=by(after,view+'-hairON')
    assert b['camera']==c['camera'], (view,'Camera/pose/light/display mismatch; do not hide it by image fitting')
    assert all(sha(q['path'])==q['sha256'] for q in [b,c,h])
    assert Image.open(b['path']).size==Image.open(c['path']).size
    tiles=[transformed(canvas,r['reference_registration']),transformed(Image.open(b['path']),reg),transformed(Image.open(c['path']),reg),transformed(Image.open(h['path']),reg)]
    board=Image.new('RGB',(2560,740),(237,242,246));draw=ImageDraw.Draw(board)
    for i,(tile,label) in enumerate(zip(tiles,['SOURCE / original aspect','v0.0.1 / frozen457','v002 / hair OFF','v002 / hair ON'])):
        board.paste(tile.convert('RGB'),(i*640,50));draw.text((i*640+8,12),label,font=font,fill=(24,38,49))
    draw.text((10,702),view+' | common ORTHO0.1..10m, pose/light/display; uniform SRT only. ART remains subject to independent review.',font=font,fill=(24,38,49))
    path=out/(view+'-source-v001-v002.png');assert not path.exists();board.save(path)
    ref=copy.deepcopy(r['reference']);ref.update(path=str(src),sha256=sha(src))
    rows.append(dict(id=view,reference=ref,baseline_render={'path':b['path'],'sha256':b['sha256']},
        candidate_render={'path':c['path'],'sha256':c['sha256']},candidate_hair_on={'path':h['path'],'sha256':h['sha256']},
        comparison_board={'path':str(path),'sha256':sha(path)},baseline_camera=b['camera'],candidate_camera=c['camera'],
        reference_registration=r['reference_registration'],baseline_registration=reg,candidate_registration=reg,
        pose_uncertainty=r['pose_uncertainty']+' Nonfront absolute proportions are excluded. Source hair occludes face in several panels.',
        observed_differences='Integrated facial pigment/independent mouth geometry and selected hair finish; see actual per-view visual review, not render completion.',
        unresolved=['Overall source identity, nose/lip graphic finish, crown/nape hair and expression contacts require actual review.']+
            ([] if view=='front' else ['Historical nonfront normalization excludes absolute proportion/roll judgments.']),
        material_mode='Actual integrated production shaders under exactly three source area lights. Neutral and orbit diagnostics are separate.' ))
pkg=dict(schema_version=1,part='face',required_views=['front','profile','left_oblique','right_oblique'],
    baseline_native={'path':before[0]['native'],'sha256':before[0]['native_sha256']},
    candidate_native={'path':after[0]['native'],'sha256':after[0]['native_sha256']},views=rows,
    scope='Current integrated source comparison. No generated illustration is substituted for model pixels. Evidence integrity does not grant ART approval.')
(out/'reference-review.json').write_text(json.dumps(pkg,indent=2)+'\n',encoding='utf-8')
print('V002_SOURCE_PACKAGE_COMPOSED',out/'reference-review.json')
