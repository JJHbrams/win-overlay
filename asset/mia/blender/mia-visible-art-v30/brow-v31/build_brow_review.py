"""Immutable source | before | after | hair-on boards, uniform SRT only."""
import argparse, copy, hashlib, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P=Path(__file__).resolve().parent
V=P.parent
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);ap.add_argument('--baseline-tag',default='brows-v31-before-source4');a=ap.parse_args()
O=V/'reviews'/a.tag/'paired';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
oldpath=V.parent/'mia-face-finish-v29/final-review/source-boards/reference-review.json'
old=json.loads(oldpath.read_text())
before=json.loads((V/'reviews'/a.baseline_tag/'source/render-records.json').read_text())
after=json.loads((V/'reviews'/a.tag/'source/render-records.json').read_text())
by=lambda rows,name:next(x for x in rows if x['id']==name)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)

def transformed(im,reg):
 scale=reg['uniform_scale'];angle=math.radians(reg['rotation_degrees']);c,s=math.cos(angle),math.sin(angle);x,y=reg['translation_xy']
 return im.convert('RGBA').transform((640,640),Image.Transform.AFFINE,(c/scale,s/scale,-(c*x+s*y)/scale,-s/scale,c/scale,(s*x-c*y)/scale),Image.Resampling.BICUBIC,fillcolor=(237,242,246,255))

rows=[]
for r in old['views']:
 view=r['id'];src=(oldpath.parent/r['reference']['path']).resolve();im=Image.open(src).convert('RGBA');crop=r['reference']['crop_xyxy'];sc=Image.new('RGBA',im.size,(237,242,246,255));sc.paste(im.crop(crop),crop[:2])
 reg=copy.deepcopy(r['candidate_registration'])
 if view=='front':
  reg={'uniform_scale':1.1698146556808693,'rotation_degrees':0.,'translation_xy':[-142.01146815879025,-223.93878303771004],
       'normalization_basis':'One frozen C opening-centre/IPD scalar+translation, no eye/chin normalization or extra display rotation; IPD excluded from independent validation.'}
 else:
  reg['notes']='Retained provisional old frozen source pose display, same for before/after. Eye/chin normalization and small extra display roll exclude absolute facial proportion/roll validation. Brow change and3D contact review only.'
 b=by(before,view+'-hairOFF');c=by(after,view+'-hairOFF');h=by(after,view+'-hairON')
 assert b['camera']==c['camera']
 tiles=[transformed(sc,r['reference_registration']),transformed(Image.open(b['path']),reg),transformed(Image.open(c['path']),reg),transformed(Image.open(h['path']),reg)]
 board=Image.new('RGB',(2560,740),(237,242,246));d=ImageDraw.Draw(board)
 for i,(tile,label) in enumerate(zip(tiles,['SOURCE / original aspect','BEFORE / original alpha brows','AFTER / independent source brows','AFTER / hair ON'])):
  board.paste(tile.convert('RGB'),(i*640,50));d.text((i*640+8,12),label,font=font,fill=(24,38,49))
 d.text((10,702),view+' / frozen common camera, light, pose and uniform display. Covered brow ends inferred; full face and hair ART still open.',font=font,fill=(24,38,49))
 path=O/(view+'-source-before-after.png');assert not path.exists();board.save(path)
 ref=copy.deepcopy(r['reference']);ref['path']=str(src);ref['sha256']=sha(src)
 row={'id':view,'reference':ref,'baseline_render':{'path':b['path'],'sha256':b['sha256']},'candidate_render':{'path':c['path'],'sha256':c['sha256']},'comparison_board':{'path':str(path),'sha256':sha(path)},
      'baseline_camera':b['camera'],'candidate_camera':c['camera'],'reference_registration':r['reference_registration'],'baseline_registration':reg,'candidate_registration':reg,
      'pose_uncertainty':r['pose_uncertainty']+' Brow full ends covered by hair; only visible source runs are targets.',
      'observed_differences':'New2independent brow owners lower/flatten generic donor arch, use broader visible central strokes and source-side slopes; old slot4 alpha archived. See actual images and independent scoped review for visual judgment.',
      'unresolved':['Covered tails/inner ends are inferred, not an observed full-brow blueprint.','Full face length/makeup/hair residuals remain open; this package cannot accept those.']+([] if view=='front' else ['Old provisional nonfront normalization limits absolute position/proportion judgments.']),
      'material_mode':'Actual production skin/eyes/paint unchanged; only2brow materials/owners differ. Brows are graphic ink, separate from crease/liner/lashes.'}
 rows.append(row)
pkg={'schema_version':1,'part':'face','required_views':['front','profile','left_oblique','right_oblique'],
     'baseline_native':{'path':before[0]['native'],'sha256':before[0]['native_sha256']},'candidate_native':{'path':after[0]['native'],'sha256':after[0]['native_sha256']},
     'scope':'Source eyebrow correction only; original eye/skin/lash/paint/body/hair geometry preserved. Evidence integrity does not certify whole-source ART.', 'views':rows}
(O/'reference-review.json').write_text(json.dumps(pkg,indent=2),encoding='utf-8')
print(O/'reference-review.json')
