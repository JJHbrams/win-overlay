"""Compose actual SOURCE | fresh BASELINE | fresh INTEGRATED using frozen uniform registrations."""
import argparse,json,hashlib,math,copy,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--output-dir',required=True);a=ap.parse_args();OUT=Path(a.output_dir).resolve();manifest=json.loads((OUT/'render-manifest.json').read_text());records=json.loads((OUT/'render-records.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
def transform(im,reg,size):
 scale=reg['uniform_scale'];angle=math.radians(reg['rotation_degrees']);A=scale*np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);inv=np.linalg.inv(A);t=-inv@np.array(reg['translation_xy']);im=im.convert('RGBA').transform(size,Image.Transform.AFFINE,tuple(inv[0])+tuple(t[:1])+tuple(inv[1])+tuple(t[1:]),resample=Image.Resampling.BICUBIC);bg=Image.new('RGBA',size,'#edf1f4');bg.alpha_composite(im);return bg.convert('RGB')
results={}
for part,source_package in manifest['input_packages'].items():
 p=Path(source_package['path']);assert sha(p)==source_package['sha256'];package=json.loads(p.read_text(encoding='utf-8-sig'));folder=OUT/part;folder.mkdir(exist_ok=True);rows=[];size=(640,640) if part=='face' else ((512,1100) if part=='body' else (500,500))
 for old in package['views']:
  name=old['id'];refpath=Path(old['reference']['path']);refpath=refpath if refpath.is_absolute() else (p.parent/refpath).resolve();assert sha(refpath)==old['reference']['sha256'];ref=Image.open(refpath);crop=old['reference']['crop_xyxy'];cropped=ref.crop(crop);crop_path=folder/(name+'-source-crop.png');cropped.save(crop_path)
  # Face's existing registrations use full-source coordinates. Body/hair explicitly use crop-relative coordinates.
  refim=ref if part=='face' else cropped
  assert old['baseline_registration']==old['candidate_registration'],(part,name,'input candidate was independently refitted')
  br=records['baseline/'+part+'/'+name];cr=records['candidate/'+part+'/'+name];assert br['camera']==cr['camera']
  for recorded in (br,cr):assert sha(recorded['render']['path'])==recorded['render']['sha256'], 'Render bytes changed after capture'
  panes=[transform(refim,old['reference_registration'],size),transform(Image.open(br['render']['path']),old['baseline_registration'],size),transform(Image.open(cr['render']['path']),old['baseline_registration'],size)]
  board=Image.new('RGB',(size[0]*3,size[1]+105),'#edf1f4');draw=ImageDraw.Draw(board)
  for i,im in enumerate(panes):board.paste(im,(i*size[0],55));draw.text((i*size[0]+12,15),['SOURCE ART','c02 / FRESH BASELINE','INTEGRATED / FRESH WIP'][i],font=font,fill='#172633')
  draw.text((12,size[1]+65),part+' / '+name+' | original uniform SRT retained; same cameras/light/display; normalized dimensions are not validated',font=small,fill='#172633');bp=folder/(name+'-source-baseline-integrated.png');board.save(bp)
  row={'id':name,'reference':{**artifact(refpath),'crop_xyxy':crop,'crop_artifact':artifact(crop_path)},'baseline_render':br['render'],'candidate_render':cr['render'],'comparison_board':artifact(bp),'baseline_camera':br['camera'],'candidate_camera':cr['camera'],'reference_registration':copy.deepcopy(old['reference_registration']),'baseline_registration':copy.deepcopy(old['baseline_registration']),'candidate_registration':copy.deepcopy(old['baseline_registration']),'pose_uncertainty':old['pose_uncertainty'],'observed_differences':'Fresh integrated replay from the declared native. Integration combines local WIP candidates; producer observations are not substituted for independent inspection of these new images. No ART pass.','unresolved':old.get('unresolved','Independent source likeness review pending.'),'material_mode':'18% diffuse clay, hair hidden, camera-relative white area rig, Freestyle OFF.' if part=='body' else 'Actual native production materials, fixed root white area rig, Standard/None, Freestyle OFF for matched comparison. Active material routes and actual visible keys recorded separately.'}
  rows.append(row)
 result={'schema_version':1,'part':package['part'],'baseline_native':manifest['baseline_native'],'candidate_native':manifest['candidate_native'],'required_views':package['required_views'],'views':rows,'input_source_package':source_package,'reference_coordinate_space':'full original image' if part=='face' else 'declared crop-relative image','registration_policy':'Input uniform SRT copied exactly; candidate uses baseline transform without feature refit. Board column/header translation is layout only.','art_status':'DIAGNOSTIC WIP; independent ART judgment required.'};dest=folder/'reference-review.json';dest.write_text(json.dumps(result,indent=2));results[part]=artifact(dest)
shutil.copyfile(__file__,OUT/'dependencies'/Path(__file__).name)
(OUT/'comparison-manifest.json').write_text(json.dumps({'packages':results,'composer':artifact(__file__),'no_native_or_source_art_modified':True,'art_acceptance':'NOT_EVALUATED'},indent=2));print(json.dumps(results,indent=2))
