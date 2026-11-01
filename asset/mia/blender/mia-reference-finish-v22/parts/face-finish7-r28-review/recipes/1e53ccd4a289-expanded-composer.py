"""Actual SOURCE | R23 | R28 with archived uniform SRT; no image fitting."""
import ast,copy,json,hashlib,math,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent;R28=OUT.parent;H=R28.parent
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22')
TEMPLATE=CAN/'parts/face-finish7-r23/reference-review.json';COMPOSER=CAN/'face-feedback-7/r23-source-comparison/dependencies/compose_integrated_review.py';VALIDATOR=CAN/'integration-wip-6/validate_reference_review.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
artifact=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
tree=ast.parse(COMPOSER.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='transform'],type_ignores=[]),str(COMPOSER),'exec'))
template=json.loads(TEMPLATE.read_text());baseline_records=H/'candidate-r23/neutral-source-four/render-records.json';candidate_records=R28/'source-four/render-records.json';br=json.loads(baseline_records.read_text());cr=json.loads(candidate_records.read_text());baseline={r['label']:r for r in br['records']};candidate={r['label']:r for r in cr['records']}
for record in [br,cr]:assert sha(record['source']['path'])==record['source']['sha256']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);rows=[];size=(640,640);camera_template_errors={}
notes={
 'front':'R28 retains the R23 aperture/upper-lash shape and restores anterior malar/buccal fullness. Source identity is not accepted: the medial cheek/nasal transition still reads as intersecting planes in low-angle diagnostics.',
 'left_oblique':'R28 outer malar support is fuller than R23, with the narrow R25 shelf reduced. The medial lower-lid/nasal-to-malar transition remains angular in the diagnostic low oblique, so this source view does not establish a broad continuous cheek PASS.',
 'right_oblique':'The opposite near-front source comparison uses the original uncertain pose and differing gaze/mouth expression. R28 keeps R23 eye contours and restores cheek depth; this is not a calibrated opposite45-degree likeness check.',
 'profile':'R28 does not intentionally project the chin or alter the ear/neck. Hair obscures much of the orbital/cheek detail in this source camera; the small stylized source does not justify numeric facial depth claims.'}
for old in template['views']:
 name=old['id'];label='native_hair_'+name;b=baseline[label];c=candidate[label];assert b['camera']==c['camera'],name
 for record in [b,c]:assert sha(record['render']['path'])==record['render']['sha256'];assert not record['camera']['active_shape_keys']
 refpath=Path(old['reference']['path']);refpath=refpath if refpath.is_absolute() else (TEMPLATE.parent/refpath).resolve();assert sha(refpath)==old['reference']['sha256'];ref=Image.open(refpath);crop=old['reference']['crop_xyxy'];crop_path=OUT/(name+'-source-crop.png');ref.crop(crop).save(crop_path)
 assert old['baseline_registration']==old['candidate_registration']
 panes=[transform(ref,old['reference_registration'],size),transform(Image.open(b['render']['path']),old['baseline_registration'],size),transform(Image.open(c['render']['path']),old['baseline_registration'],size)]
 board=Image.new('RGB',(1920,780),'#edf1f4');draw=ImageDraw.Draw(board)
 labels=['ORIGINAL SOURCE ART','R23 / REJECTED CHEEK SURFACE','R28 / LOCAL RESTORED-VOLUME CANDIDATE']
 for i,pane in enumerate(panes):board.paste(pane,(640*i,55));draw.text((640*i+12,16),labels[i],font=font,fill='#172633')
 draw.text((12,711),name+' | WORKING CANDIDATE / ART UNAPPROVED | original uniform SRT retained; no candidate refit',font=small,fill='#172633')
 draw.text((12,738),'Uncertain source yaw/gaze; normalized eye-to-chin distance is excluded from validation. Raw native/render/source hashes recorded.',font=small,fill='#172633');board_path=OUT/(name+'-source-r23-r28.png');board.save(board_path)
 camera_template_errors[name]=max(abs(x-y) for a,z in zip(old['candidate_camera']['matrix'],b['camera']['matrix']) for x,y in zip(a,z));assert camera_template_errors[name]<1e-6
 rows.append({'id':name,'reference':{**artifact(refpath),'crop_xyxy':crop,'crop_artifact':artifact(crop_path)},'baseline_render':copy.deepcopy(b['render']),'candidate_render':copy.deepcopy(c['render']),'comparison_board':artifact(board_path),'baseline_camera':copy.deepcopy(b['camera']),'candidate_camera':copy.deepcopy(c['camera']),'reference_registration':copy.deepcopy(old['reference_registration']),'baseline_registration':copy.deepcopy(old['baseline_registration']),'candidate_registration':copy.deepcopy(old['baseline_registration']),'pose_uncertainty':old['pose_uncertainty'],'observed_differences':notes[name],'unresolved':'R28 is an unapproved working candidate. Medial transition modestly softer than R27, but independent AC-SURFACE remains FAIL. Lowfront/lowoblique medial lower-lid/nasal-to-malar plane junction remains; broad convex continuous cheek and source likeness are not passed. Producer hair is inherited, not live Hair0d. R19 surface acceptance is revoked; R23 eyes are retained separately.','material_mode':'Actual existing native_hair neutral source-four renders, unchanged production materials/lighting/display; actual per-view camera/light/key records copied exactly for both candidates.'})
package={'schema_version':1,'part':'face','baseline_native':br['source'],'candidate_native':cr['source'],'required_views':template['required_views'],'views':rows,'input_source_package':artifact(TEMPLATE),'reference_coordinate_space':'full original image','registration_policy':'Archived source/baseline uniform SRT copied exactly from input package; same transform applied to R23 and R28. No source, candidate, feature, anisotropic or silhouette refit. Layout translation only.','art_status':'WORKING CANDIDATE / ART UNAPPROVED; AC-SURFACE FAIL; not adopted','actual_render_record_sources':{'baseline':artifact(baseline_records),'candidate':artifact(candidate_records)},'archived_camera_max_component_difference':camera_template_errors,'recipe':artifact(__file__),'archived_composer':artifact(COMPOSER)}
(OUT/'reference-review.json').write_text(json.dumps(package,indent=2));shutil.copyfile(VALIDATOR,OUT/'validate_reference_review.py');shutil.copyfile(COMPOSER,OUT/'archived-compose-integrated-review.py')
assert sha(br['source']['path'])==br['source']['sha256'] and sha(cr['source']['path'])==cr['source']['sha256']
(OUT/'package-provenance.json').write_text(json.dumps({'package':artifact(OUT/'reference-review.json'),'baseline_native':br['source'],'candidate_native':cr['source'],'validator':artifact(OUT/'validate_reference_review.py'),'composer':artifact(__file__),'source_art_and_natives_modified':False,'geometry_frozen':True,'art_acceptance':'NOT_EVALUATED'},indent=2));print(json.dumps(artifact(OUT/'reference-review.json'),indent=2))
