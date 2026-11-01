"""Freeze actual F2 evidence and inherited D map facts. No Blender mutation."""
from pathlib import Path
import json,hashlib,os
ROOT=Path(__file__).resolve().parent;P=ROOT/'shape-f2';OUT=P/'handoff'
def art(path):
 p=Path(path);assert p.is_file(),p
 return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(path):return json.loads(Path(path).read_text())
d=read(ROOT/'look-d/handoff/handoff-manifest.json');replay=read(OUT/'owner-key-replay-from-d.json');guards=read(OUT/'guard-summary.json');audit=read(OUT/'material-map-audit.json');review=read(P/'review-package/validation.json');verification=read(OUT/'replay-validation.json')
assert review['evidence_valid'] and not review['errors']
assert verification['exact_final_mesh_keys_uv_materialslots'] and verification['repeated_replay_rejected']
assert audit['actual_material_graph_and_packed_maps_equal_D']
for v in ['0','0.5','1']:assert guards['guards']['evaluated_eye_boundary_'+v]['max_delta_m']==0
maps={}
for name,item in d['map_files'].items():
 maps[name]=dict(item);maps[name]['relative_to_f2_native']=os.path.relpath(item['path'],P).replace('\\','/');maps[name].pop('relative_to_native',None)
 assert art(item['path'])['sha256']==item['sha256']==audit['state']['images'][item['node']]['packed_sha256']
changed_keys={name:sorted(k for k in channels if k!='mesh_cache') for name,channels in replay['owners'].items() if channels}
report={
 'status':'FROZEN REVIEW-ONLY LOCAL VOLUME RECOVERY / WHOLE ART UNAPPROVED',
 'native':replay['candidate'],'baseline':replay['baseline'],
 'changes':replay['summary'],'changed_key_names':changed_keys,
 'anatomical_diagnosis':[
  'D/E anterior-to-buccal support recedes rapidly below the high malar region. The user-visible hollow is actual evaluated geometry; all polygons smooth, no custom split normals or sharp edges in the cheek, Armature then Subsurf2.',
  'F recovered central anterior volume around absX20-40mm and Z1.496-1.520m, but attached it to an overly recessed lateral row. At example cage vertices291/259, the F depth dropped about23mm over4mm lateral distance, producing a new angular band.',
  'F2 connects central F depth anchors to lateral buccal support through height-interpolated convex section targets. It retains high malar mass and short anterior fullness, and changes Y only. No chin shortening/projection, eye adjustment, global width scale, topology change or paint revision.',
  'F2 lower/anterior cheek recovery is visually useful in fixed matte and opposite native lights. The upper lower-lid-to-nasal/malar diagonal plane band remains; user-visible hollow is not declared fully resolved.'
 ],
 'source_review':art(P/'review-package/reference-review.json'),'source_review_validation':art(P/'review-package/validation.json'),
 'source_four_records':art(P/'source-four/render-records.json'),'matched_matte_and_two_lights':art(P/'paired/paired-records.json'),
 'limited_blink_records':art(P/'limited-blink/render-records.json'),
 'blink_assessment':'Actual symmetric half/full at front/+60 inspected. Half is partial with iris visible; full shows no visible iris leak or lash detachment in these views. Exact evaluated aperture guard also covers neutral. Not all47 expressions or final rig validation.',
 'exact_replay':art(OUT/'owner-key-replay-from-d.json'),'replay_script':art(ROOT/'replay_f2_into_d.py'),'replay_validation':art(OUT/'replay-validation.json'),'guards':art(OUT/'guard-summary.json'),
 'material_map_audit':art(OUT/'material-map-audit.json'),'material':d['material'],'slot':7,'uv_layer':'UVMap','map_files':maps,
 'consumed_route':d['consumed_route'],'color_only_socket':d['color_only_socket'],
 'material_policy':'Use exact D maps/material unchanged. F2 contains the same packed image bytes. External image paths still point to producer look-d/maps; root may copy/relink in its integrated native without modifying this frozen native. Old MIA_V22_FULL_LINEAR_ALBEDO image node remains archived in material but is not the consumed final pigment route.',
 'integration_order':'Apply archived R28-to-D owner/key replay and D material/cap mapping first, then this guarded D-to-F2 geometry-only replay. Or import final face owner directly with root-owned cap/body mapping. This replay has zero body/cap rows and does not transfer materials, open, save or operate on live Blender.',
 'recipe_chain':[art(ROOT/x) for x in ['build_shape_e.py','build_shape_f.py','build_shape_f2.py','render_shape_e_review.py','render_source_only.py','render_f2_blink.py','compose_f2_source.py','export_f2_replay.py','verify_f2_replay.py','audit_f2_maps.py','package_f2_handoff.py']],
 'failed_F_preserved':{'status':'UNSELECTED: restored central mass with angular lateral attachment','native':art(ROOT/'shape-f/Mia_FaceFinish8_CentralBuccalF.blend'),'manifest':art(ROOT/'shape-f/manifest.json'),'diagnosis':art(ROOT/'shape-f/evaluated-buccal-f-result.json'),'small_evidence':[art(ROOT/'shape-f/targeted'/n) for n in ['matte_yaw+00_elev-10.png','matte_yaw+30_elev-10.png']]},
 'per_acceptance':{'AC1':'LOCAL RECOVERY FOR REVIEW ONLY: anterior/buccal volume visibly restored; upper diagonal transition remains. No full surface approval.','AC2':'FAIL / UNFINISHED: connected cheek/nose/jaw source form still not established. Chin unchanged from D; eye-to-chin SRT cannot prove absolute height.','AC3':'LIMITED MOTION GUARD PASS; source tired contour/iris/line fidelity still incomplete. No new eye edit in F2.','AC6':'D authored maps inherited and actual consumption verified, no new paint authored here. Source-style art acceptance remains unapproved.'},
 'limits':['Original source SRT and fixed cameras retained, no per-view geometry fitting or candidate renormalization. Source profile yaw/gaze uncertainty and old producer hair occlusion remain.','Fixed-local section depths are diagnostic, not homologous anatomical volume or source-calibrated measurements.','Native and UV/material hashes prove provenance/consistency, not art quality. Parent owns independent review and live integration.']
}
(OUT/'handoff-manifest.json').write_text(json.dumps(report,indent=2));print('F2_HANDOFF_READY',json.dumps(art(OUT/'handoff-manifest.json')))
