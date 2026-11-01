"""Fresh actual EEVEE material comparison under the frozen source camera/lighting."""
import argparse,ast,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent;V22=ROOT.parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(V22/'integration-wip-8-review/Mia_ReferenceFinish_v22.blend'));ap.add_argument('--candidate',required=True);ap.add_argument('--output-dir',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir);assert not OUT.exists();OUT.mkdir(parents=True)
names={'render_visible','keys','hair_hide','material','aim','setup','camera_and_lights','record','routes','production_uv'}
rig=V22/'render_integrated_review.py';tree=ast.parse(rig.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(rig),'exec'))
package=V22/'parts/face-finish8-f2-review/reference-review.json';data=json.loads(package.read_text(encoding='utf-8-sig'));views={v['id']:v['baseline_camera'] for v in data['views']}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source={r:Path(p) for r,p in [('baseline',a.source),('candidate',a.candidate)]};records={}
for role,path in source.items():
 s,lamps=setup(path,'face');folder=OUT/role;folder.mkdir()
 for view in ['front','left_oblique']:
  camera_and_lights(s,lamps,views[view],'face');p=folder/(view+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records[role+'/'+view]={'render':str(p),'sha256':sha(p),'camera':record(s,lamps)}
 hair_hide();camera_and_lights(s,lamps,views['front'],'face');p=folder/'bare_lit.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records[role+'/bare_lit']={'render':str(p),'sha256':sha(p),'camera':record(s,lamps)}
 for sl in bpy.data.objects['MIA_V14_SculptedSkin'].material_slots:
  if not sl.material or not sl.material.use_nodes:continue
  m=sl.material.copy();sl.material=m;n=m.node_tree.nodes;mul=n.get('PigmentTimesControlledLight')
  if mul and mul.inputs[1].is_linked:
   em=next((x for x in n if x.type=='EMISSION'),None)
   if em:m.node_tree.links.new(mul.inputs[1].links[0].from_socket,em.inputs[0])
 p=folder/'color_only.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records[role+'/color_only']={'render':str(p),'sha256':sha(p),'camera':record(s,lamps)}
for k in ['front','left_oblique','bare_lit','color_only']:assert records['baseline/'+k]['camera']==records['candidate/'+k]['camera']
(OUT/'render-records.json').write_text(json.dumps(records,indent=2));(OUT/'manifest.json').write_text(json.dumps({'sources':{r:{'path':str(p),'sha256':sha(p)} for r,p in source.items()},'face_package':{'path':str(package),'sha256':sha(package)},'same_conditions':True,'native_saved':False,'art_status':'NOT_EVALUATED'},indent=2))
print('MATERIAL_REVIEW_DONE')
