import argparse,ast,sys,json,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).parent;V22=ROOT.parents[1]
sys.path.insert(0,str(ROOT));from build_eye_contour import eye_loops
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir);assert not OUT.exists();OUT.mkdir(parents=True)
names={'render_visible','keys','hair_hide','material','aim','setup','camera_and_lights','record','routes','production_uv'};rig=V22/'render_integrated_review.py';tree=ast.parse(rig.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(rig),'exec'))
package=V22/'parts/face-finish8-f2-review/reference-review.json';data=json.loads(package.read_text(encoding='utf-8-sig'));views={v['id']:v['baseline_camera'] for v in data['views']};sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={'baseline':Path(a.baseline),'candidate':Path(a.candidate)};records={};gaps={}
def save(role,name,s,lamps):
 p=OUT/role/(name+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records[role+'/'+name]={'render':str(p),'sha256':sha(p),'camera':record(s,lamps)}
for role,path in sources.items():
 (OUT/role).mkdir();s,lamps=setup(path,'face')
 for view in ['front','left_oblique','right_oblique','profile']:
  camera_and_lights(s,lamps,views[view],'face');save(role,view,s,lamps)
 skin=bpy.data.objects['MIA_V14_SculptedSkin'];P=np.array([v.co[:] for v in skin.data.shape_keys.key_blocks[0].data]);loops=eye_loops(skin.data,P);close=next(k for k in skin.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'))
 hair_hide();camera_and_lights(s,lamps,views['front'],'face');gaps[role]={}
 for state,value in [('neutral_bare',0),('halfblink',.5),('fullblink',1)]:
  close.value=value;skin.data.shape_keys.update_tag();bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();K=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();gaprows=[]
  for loop in loops:
   ts=np.linspace(.15,.90,51)
   zz=[]
   for part in ['upper','lower']:
    ids=loop[part];x=(abs(P[ids,0])-loop['x0'])/(loop['x1']-loop['x0']);ix=np.argsort(x);zz.append(np.interp(ts,x[ix],K[ids[ix],2]))
   g=(zz[0]-zz[1])*1000;gaprows.append({'side':loop['side'],'signed_vertical_gap_mm_min_max_mean':[float(g.min()),float(g.max()),float(g.mean())]})
  gaps[role][state]=gaprows;save(role,state,s,lamps)
 close.value=0;bpy.context.view_layer.update();clay=material('clay')
 for slot in skin.material_slots:slot.material=clay
 for view in ['front','left_oblique']:
  camera_and_lights(s,lamps,views[view],'face');save(role,'matte_'+view,s,lamps)
for k in ['front','left_oblique','right_oblique','profile','neutral_bare','halfblink','fullblink','matte_front','matte_left_oblique']:assert records['baseline/'+k]['camera']==records['candidate/'+k]['camera']
(OUT/'render-records.json').write_text(json.dumps(records,indent=2));(OUT/'blink-gap-diagnostic.json').write_text(json.dumps(gaps,indent=2));(OUT/'manifest.json').write_text(json.dumps({'sources':{r:{'path':str(p),'sha256':sha(p)} for r,p in sources.items()},'same_camera_lighting_pose':True,'source_package':{'path':str(package),'sha256':sha(package)},'renderer':{'path':str(Path(__file__)),'sha256':sha(__file__)},'art_status':'UNREVIEWED','limits':['Neutral four source-camera views, front half/fullblink and two matte angles only. Not full expression validation.','Signed vertical boundary gap diagnostic is not eyelid-eye collision detection.']},indent=2));print('EYE_REVIEW_DONE')
