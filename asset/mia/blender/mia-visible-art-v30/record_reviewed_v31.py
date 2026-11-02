"""Record exact integrated component review, keeping all global ART failures open."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;M=P.parents[1];sp=M/'CURRENT_STATE.json'
state=json.loads(sp.read_text(encoding='utf-8'))
expected='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a'
assert state['active_working_correction']['sha256'] in ['9dd072af38d52130aa693c561545b2b70b98f22c3b69145fc2b7211cd1632505',expected],'Do not overwrite a newer working state'
native=P/'integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend'
assert hashlib.sha256(native.read_bytes()).hexdigest()==expected
rel=lambda p:str(p.relative_to(M)).replace('\\','/')
package=P/'reviews/v31-brows-lashes-source4/paired/reference-review.json';pkg=json.loads(package.read_text())
valid=P/'reviews/v31-brows-lashes-source4/paired/evidence-validation.json'
assert json.loads(valid.read_text())['evidence_valid'] and pkg['candidate_native']['sha256']==expected
for tag,count in [('v31-brows-lashes-source4',12),('v31-brows-lashes-poses',17),('v31-close-after',4)]:
 rows=json.loads((P/'reviews'/tag/'source/render-records.json').read_text());assert len(rows)==count
 assert all(r['native_sha256']==expected and r['camera']['clip_end']==10 and r['camera']['pixel_aspect']==[1.,1.] for r in rows)
live=P/'live/v31-brows-lashes-reviewed/live-review.json';l=json.loads(live.read_text());assert l['native_sha256']==expected and l['native_saved'] is False
review=P/'FINAL_SCOPED_REVIEW.md';assert review.is_file()
state['updated']='2026-11-02';state['status']='v31_scoped_brow_closed_lash_reviewed_overall_source_art_open';state['character_complete']=False;state['art_approved']=False
active={'path':rel(native),'sha256':expected,'meaning':'Current packed/live component working review. Lower/straighter brows, Eposterior gap correction, fullCloseBupper-lash cleanup and1216semantic hair-fragment removal. Overall face/body/hair/source ART remains open.','face_review':rel(package),'source_integrity_validation':rel(valid),'scoped_visual_review':rel(review),'live_review':rel(live)}
state['active_working_correction']=active
oldselected=state.get('selected_static_wip',{})
if oldselected.get('sha256')!=expected:state['previous_selected_static_wip']=oldselected
state['selected_static_wip']={'path':rel(native),'sha256':expected,'selection_means':'Current component working review only; not completed Mia/source ART/animation.'}
state['current_face_candidate']={'path':rel(native),'sha256':expected,'status':'Scoped brow direction and fullCloseupperfan improvement independently supported; Halfband/endpoint/globalidentity still open.'}
state['current_surface_wip']={'path':rel(native),'sha256':expected,'selection_means':'FaceA packed pigment and newbrowParamUV ink retained. Source fatigue/nose/inkfinish remain WIP; no newtexture-resolution/PBRcompletion claim.'}
state['diagnostics']['current_live_viewing_setup']=rel(native);state['diagnostics']['current_live_evidence']=rel(live);state['diagnostics']['v31_source_review']=rel(package)
state['stage_status']['corresponding_view_camera_registration']='Actual matchedsource4 on current457 native; frozenfrontIPDscale/translation, zeroextra2Droll, sourceaspectunchanged. NonfrontoldfrozenSRTprovisional andnormalizedproportions/roll excluded. Sourceareas/world,camera.1/10+headcentredORTHOsaved. Evidencevalid; overallARTnotapproved.'
state['stage_status']['face_head_art']='Overall sourceART UNAPPROVED. Lower/straighter eyebrowdirection and boundedfullCloseupperfan/hookcleanup supportedbyfreshactualimages. Cleanuniformink/inferredends/hairONexposure,Halfband/temporalfinish,sourcefaciallength/width/paint residuals remain.'
state['stage_status']['facial_deformation']='Eposteriorseam73bilateral/endpoint+64unilateralscopedchecks; Brow51states/1207986samples+.02313..+.47909mm; ClosedB25stateswith0burial/nonpositivevolumes. Exactintegrated17poses+4aftermacros reviewed, bilateral/unilateralfullClose improved. Arbitrarycombinations,Extra/half style,headfollow/finaleventsunapproved.'
v=state['in_progress_v31'];v['working_native']=rel(native);v['working_sha256']=expected;v['latest_source_package']=rel(package);v['latest_package_integrity']='valid on exact457 native; ART_NOT_EVALUATED';v['live_review']=rel(live);v['final_scoped_review']=rel(review)
v['active_lash_producer']['status']='Completed boundedBhandoff/replay; all4closedarrays integrated into exact457, finalsource/17poses/macros/live independentlyreviewed. Wholelashstyle remainsopen.'
v['scoped_supported_changes']=['Lower/straighter sourcebrowdirection, exactoriginal42controls andskinconformity.','Posterioroutereye/wall/cap contact including testedbilateral/unilateralclosure.','FullClosehangingfan andtallhooks reduced onbothsides; neutralidleRGBbitexact9dd→457.','Only1216classifiedoldfacepolysremovedfromhair; realforelocks retained.']
v['critical_remaining']=['Half-closedgrazingupperband/outercap, fulltemporalangularendpoint/finefrontweight, Extra returnpocketstyle; notwholefanART.','Browinkuniformity/innerfinish; hiddenendsinferred andgenuinehairONexposure differs.','Lowerlashdetail mergeswithpaint512; visible/opaque, noarbitraryenlargement.','Sourceeye-to-mouth/chinlength andfacewidth/cheekidentity needcontinuousmultiviewshape work.','Sourcefatigue/fold/nosepigmentspecificity; currentband/compactnose remainWIP.','Fine darksourcehairshape/linework/root/ear/nape/bun/tips; unadoptedP8/P12probes are notfinishedhair.','BodyoverallART,garments,physics/events/loops/commonidle30fps outputstillbehindgates.']
state['immediate_next']=['Read exact457 native/hash, FINAL_SCOPED_REVIEW and all criticalremainingbefore edits; neverrestore oldv29boundedPASS.','Use currentpairedsource4/actualsourceaspect andfrozenfrontIPDframe; keepnonfrontnormalizationlimits explicit.','Next sourcecorrections mustaddress observedHalf/inkfinish andbroaderfaceidentity/paint/hair in boundedmultiviewsteps; no finalgarment/eventpromotion.','Keep selectedassets/proofs onGit andrecordresiduals; sourcepackagevalidity doesnotgrantART.']
sp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('REVIEWED_V31_STATE',rel(native),expected,'OVERALL_ART_OPEN')
