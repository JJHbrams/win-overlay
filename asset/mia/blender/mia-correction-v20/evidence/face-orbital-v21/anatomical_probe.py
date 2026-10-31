"""Read-only same-camera neutral comparison of 873 / 6794 / c13 geometry."""
import bpy,sys,json,hashlib,math,ast,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay');sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
HERE=Path(__file__).resolve().parent;OUT=HERE/'anatomical-probe';OUT.mkdir(exist_ok=True)
helper=HERE.parent/'verify_v20.py';tree=ast.parse(helper.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(helper),'exec'))
sources=[('v21_main',HERE/'main/Mia_OrbitalGuide_v21.blend',HERE.parent/'frozen/front-landmarks.json')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'mode':'Neutral diffuse only, same rig/camera/neutral geometry. No edits or native save.','resolution':[900,900],'ortho':.29,'target':[0,0,1.55],'stages':{}}
for label,path,landmarks in sources:
 oldhash=sha(path);sc=load(path);skin=bpy.data.objects['MIA_V14_SculptedSkin'];values={k.name:k.value for k in skin.data.shape_keys.key_blocks};assert all(v==0 for k,v in values.items() if k!='Basis')
 ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];bvh=BVHTree.FromPolygons(pts,[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear();profiles=[]
 lm=json.loads(landmarks.read_text())['landmarks']['geometric_eyelid_contours']
 for eye in lm:
  outer=eye['outer_canthus']['world_m'];sign=1 if outer[0]>0 else -1
  for lateral in [-.008,-.004,.002]:
   x=outer[0]+sign*lateral;points=[]
   for drop in np.arange(0,.0261,.002):
    z=outer[2]-drop;hit,normal,poly,dist=bvh.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)))
    if hit is not None:points.append({'drop_m':float(drop),'point':list(hit),'normal':list(normal),'polygon':poly})
   turns=[]
   for p,q in zip(points,points[1:]):
    if q['drop_m']-p['drop_m']>.0021:continue
    turns.append({'drops_m':[p['drop_m'],q['drop_m']],'normal_turn_deg':math.degrees(math.acos(np.clip(np.dot(p['normal'],q['normal']),-1,1)))})
   profiles.append({'side':sign,'outer_canthus_world':outer,'lateral_from_outer_canthus_m':lateral,'points':points,'turns':turns})
 neutral(sc)
 for name,yaw in []:render(sc,label+'_'+name,yaw)
 report['stages'][label]={'native':str(path),'sha256':oldhash,'sha256_after':sha(path),'shape_key_values':values,'profiles':profiles};assert sha(path)==oldhash
(OUT/'diagnostic.json').write_text(json.dumps(report,indent=2));print('ORBITAL_DIAGNOSTIC_DONE')
