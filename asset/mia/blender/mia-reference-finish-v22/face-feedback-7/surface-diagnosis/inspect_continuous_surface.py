"""Frozen face6 read-only evaluated sections, continuous matte yaw and cage-wire overlay."""
import bpy,sys,ast,json,hashlib,argparse,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
PACKAGE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source',default=str(PACKAGE.parents[1]/'parts/face-finish6/native/f5d17264e07f-Mia_FaceFinish6_v22.blend'))
ap.add_argument('--output-dir',default=str(PACKAGE/'rerun'))
ap.add_argument('--validate-only',action='store_true',help='Check frozen helpers/source without opening the native or rendering.')
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
SOURCE=Path(a.source).resolve();H=Path(a.output_dir).resolve();D=PACKAGE/'dependencies';sys.path.insert(0,str(D));import review_setup as r
tree=ast.parse((D/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rig','constant']],type_ignores=[]),'frozen-review-helpers','exec'))
sh=r.sha(SOURCE)
if a.validate_only:
 print(json.dumps({'source':r.artifact(SOURCE),'dependencies':[r.artifact(D/n) for n in ['review_setup.py','shape_evidence.py']],'output_dir':str(H),'native_opened':False}));sys.exit(0)
if H.exists() and any(H.iterdir()):raise RuntimeError('Output directory must be empty; frozen evidence will not be overwritten: '+str(H))
H.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects['MIA_V14_SculptedSkin'];body=bpy.data.objects['MIA_V06_BODY_SKIN'];dep=bpy.context.evaluated_depsgraph_get();geometries={}
for o in [skin,body,bpy.data.objects['MIA_V14_EyeSurface']]:
 ev=o.evaluated_get(dep);me=ev.to_mesh();toskin=skin.matrix_world.inverted()@ev.matrix_world;pts=[toskin@v.co for v in me.vertices];faces=[list(f.vertices) for f in me.polygons];geometries[o.name]=BVHTree.FromPolygons(pts,faces);ev.to_mesh_clear()
def hit(x,z):
 rows=[]
 for name in [skin.name,body.name]:
  q,n,i,d=geometries[name].ray_cast(Vector((x,.25,z)),Vector((0,-1,0)))
  if q is not None:rows.append({'owner':name,'p':list(q),'normal':list(n),'distance':d})
 return min(rows,key=lambda q:q['distance']) if rows else None
sections={'vertical':[],'horizontal':[]}
for x in [-.065,-.055,-.045,-.035,.035,.045,.055,.065]:
 sections['vertical'].append({'x':x,'samples':[{'z':float(z),'hit':hit(x,float(z))} for z in np.arange(1.475,1.556,.001)]})
for z in [1.480,1.490,1.500,1.510,1.520,1.530,1.535,1.540]:
 sections['horizontal'].append({'z':z,'samples':[{'x':float(x),'hit':hit(float(x),z)} for x in np.arange(-.080,.081,.001)]})
co=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);adj=[set() for v in co]
for e in skin.data.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
region=[]
for i,(x,y,z) in enumerate(co):
 if .025<abs(x)<.075 and 1.480<z<1.550 and y>.005:
  lengths=[float(np.linalg.norm(co[j]-co[i])) for j in adj[i]];region.append({'vertex':i,'co':co[i].tolist(),'valence':len(adj[i]),'edge_minmax_m':[min(lengths),max(lengths)],'neighbors':sorted(adj[i])})
report={'source':r.artifact(SOURCE),'coords':'Skin local+Y front/world-Y; local+X screen-left; neutral frame1. BVH normals are evaluated geometric triangle normals, not custom shading normals.','sections':sections,'cage_region':region,'all_skin_base_vertices':co.tolist(),'all_skin_base_edges':[list(e.vertices) for e in skin.data.edges],'all_skin_base_faces':[list(f.vertices) for f in skin.data.polygons]};(H/'actual-sections-and-cage.json').write_text(json.dumps(report,indent=2))
rig(s);r.hairhide();s.render.use_freestyle=False;clay=constant('SURFACE_DIAG_MATTE',(.18,.18,.18),True)
for o in [skin,body]:
 for slot in o.material_slots:slot.material=clay
for o in s.objects:
 if any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
records=[]
def render(mode,yaw,elevation):
 v={'id':mode,'yaw':yaw,'elevation':elevation,'roll':0};r.camera(s,v);s.render.resolution_x=s.render.resolution_y=700;label=mode+'_yaw%+03d_elev%+03d'%(yaw,elevation);path=H/(label+'.png');s.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'mode':mode,'yaw':yaw,'elevation':elevation,'render':r.artifact(path),'matrix':[list(row) for row in s.camera.matrix_world],'ortho_scale':.29,'resolution':[700,700]})
# Negative elevation first: directly tests user's low-front observation.
for el in [-10,0,10]:
 for yaw in [0,15,30,45,60,75,90,-15,-30,-45,-60,-75,-90]:render('matte',yaw,el)
# Actual neutral armature-evaluated control cage, not tessellated subdiv wire.
sub=next(m for m in skin.modifiers if m.type=='SUBSURF');state=sub.show_viewport;sub.show_viewport=False;bpy.context.view_layer.update();mesh=bpy.data.meshes.new_from_object(skin.evaluated_get(bpy.context.evaluated_depsgraph_get()));sub.show_viewport=state;bpy.context.view_layer.update();wire=bpy.data.objects.new('DIAG_NEUTRAL_CONTROL_CAGE',mesh);s.collection.objects.link(wire);wire.matrix_world=skin.matrix_world.copy();wire.data.materials.clear();wire.data.materials.append(constant('DIAG_WIRE_INK',(.012,.022,.035)));wf=wire.modifiers.new('Actual cage edges','WIREFRAME');wf.thickness=.00014;wf.use_replace=True;wf.use_even_offset=True
for yaw in [0,15,30,45,60,75,90,-15,-30,-45,-60,-75,-90]:render('wire',yaw,0)
for yaw in [0,30,-30]:render('wire',yaw,-10)
assert r.sha(SOURCE)==sh
(H/'render-records.json').write_text(json.dumps({'source':r.artifact(SOURCE),'source_unchanged':True,'records':records,'limitations':'Wire overlay is actual control cage; some edges can be hidden inside smooth evaluated surface. No geometry/native save. Fixed world lights, neutral matte; this diagnoses surface continuity, not original-art likeness.'},indent=2));print('CONTINUOUS_DIAG_DONE',len(records))
