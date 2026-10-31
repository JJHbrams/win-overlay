"""Package the reviewed design checkpoint and approved references; no geometry edits."""
import hashlib
import json
import sys
from pathlib import Path
import bpy

out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
repo=Path(__file__).resolve().parents[3]
scene=bpy.context.scene;scene.name='Mia_Stage1_Design_Review'
scene['stage_status']='TECHNICAL_BLOCKOUT_ONLY; ART_NOTAPPROVED; RIG_AND_ANIMATION_INCOMPLETE'
refs=bpy.data.collections.new('APPROVED_REFERENCES_20261031_HIDDEN');scene.collection.children.link(refs)
reference_rows=[]
for name,file in [('MASTER','mia-clean-master-v22.png'),('FACE16','mia-expression-style-confirmed-20261031.png')]:
 path=repo/'asset/mia/references'/file;im=bpy.data.images.load(str(path),check_existing=True);im.pack()
 ob=bpy.data.objects.new('APPROVED_'+name+'_IMAGE_GUIDE',None);refs.objects.link(ob)
 ob.empty_display_type='IMAGE';ob.data=im;ob.empty_display_size=1.7;ob.hide_render=ob.hide_viewport=True
 reference_rows.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
notes=bpy.data.texts.new('MIA_STAGE1_REVIEW_NOTES')
notes.write('Stage 1 design checkpoint. Technical native/UV/source preservation checks passed.\nART NOT APPROVED: eyes/eyelids, hand boundaries, wardrobe fit and source partition boundaries require further modeling.\nHigh-resolution head/waves and lower trousers/shoes are design surfaces, not production topology.\nNew separate garment, strap, bag and anatomy volumes are editable blockout cages.\nThe prior authored braid and original Face42/body research are retained. No automatic shape-key transfer.\nApproved concept references are packed in APPROVED_REFERENCES_20261031_HIDDEN.\nRetopology, expression controls, manual weights, correctives, collision and 30fps events are not complete.\n')
report=json.loads((out/'report.json').read_text(encoding='utf-8'))
report['status']='TECHNICAL_BLOCKOUT_CHECKPOINT; ART_NOTAPPROVED; CHARACTER_INCOMPLETE'
report['traceability']={'head_and_waves':'preserved high-resolution single-head design surface; mixed boundaries await production retopology','braid':'prior authored native braid reused with recorded design fitting','lower_body':'preserved generated lower-trouser/shoe design surface','upper_body':'new editable crop, inner band, cardigan, sleeves, hip/waist, strap, rear bag and neck/abdomen volumes','hidden_sources':'complete imported source partitions and original anatomy/Face42 research preserved'}
report['unresolved']=['eye/eyelid/iris structures and expression likeness','hand/wrist junctions and garment fit polish','production head/hair/garment topology and clean semantic boundaries','final UV/texture, facial/body rig, manual weights, correctives and deformation tests','secondary motion, clip transitions, common idle calibration and 30fps events']
report['approved_reference_images']=reference_rows
report['review_native']='Mia_Stage1_DesignReview.blend'
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(out/report['review_native']))
report['review_native_sha256']=hashlib.sha256((out/report['review_native']).read_bytes()).hexdigest()
(out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('REVIEW_PACKAGE_SAVED',report['review_native_sha256'])
