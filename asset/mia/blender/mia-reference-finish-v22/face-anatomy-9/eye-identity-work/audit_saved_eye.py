import bpy,json,sys,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT));from build_eye_contour import snapshot
SOURCE=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-connected-v26/Mia_ConnectedLoft_Q7_SurfaceFit.blend');NATIVE=ROOT/'e2-q7/Mia_EyeContour_E2.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
data={}
for role,path in [('source',SOURCE),('candidate',NATIVE)]:
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);skin=bpy.data.objects['MIA_V14_SculptedSkin'];k=skin.data.shape_keys.key_blocks
 data[role]={'snapshot':snapshot(),'keys':{x.name:np.array([v.co[:] for v in x.data]) for x in k},'mods':[(m.name,m.type,m.show_viewport,m.show_render) for m in skin.modifiers],'key_order':[x.name for x in k],'groups':[g.name for g in skin.vertex_groups],'weights':hashlib.sha256(json.dumps([[(g.group,g.weight) for g in v.groups] for v in skin.data.vertices]).encode()).hexdigest(),'images':{im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}}
before=data['source'];after=data['candidate'];allowed={'MIA_V14_SculptedSkin','MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1'};changed=[]
for name,row in before['snapshot'].items():
 if after['snapshot'][name]!=row:changed.append(name)
 if name not in allowed:assert after['snapshot'][name]==row,name
 else:
  for field in ('uv','topology','materials','matrix'):assert after['snapshot'][name][field]==row[field],(name,field)
for field in ('mods','key_order','groups','weights','images'):assert before[field]==after[field],field
key_deltas={}
for name,P in before['keys'].items():
 d=np.linalg.norm(after['keys'][name]-P,axis=1)*1000;key_deltas[name]={'changed':int(np.count_nonzero(d>1e-5)),'max_mm':float(d.max())}
close=next(n for n in key_deltas if n.endswith('Fcl_EYE_Close'));assert key_deltas[close]['max_mm']==0, key_deltas[close]
report={'source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'candidate':{'path':str(NATIVE),'sha256':sha(NATIVE)},'actual_modified_owners':changed,'non_target_mesh_keys_uv_materials_transforms_exact':True,'target_uv_topology_materials_transforms_exact':True,'skin_modifier_order_weights_groups_key_order_exact':True,'all_packed_images_exact':True,'key_deltas':key_deltas,'full_close_skin_key_exact':True,'limits':['Full-close stored skin shape is exactly preserved, but this does not validate all mixed expressions.','Actual neutral4, half/fullblink and matte2 images are separate evidence; no general collision/rig or ART PASS.']}
(ROOT/'e2-q7/saved-native-audit.json').write_text(json.dumps(report,indent=2));print('SAVED_EYE_AUDIT_DONE',changed,key_deltas[close])
