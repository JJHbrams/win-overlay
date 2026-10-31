"""Bounded static reuse of detailed v07 hair on preserved v09 Face44/body."""
import bpy,sys,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(Path(__file__).resolve().parent))
import refine_mia_head_v06 as h
OUT=ROOT/'asset/mia/blender/mia-static-design-v11';OUT.mkdir(exist_ok=True)
BASE=ROOT/'asset/mia/blender/mia-head-refine-v06/astra-v09/Mia_Astra_Head_v09.blend'
DETAIL=ROOT/'asset/mia/blender/mia-production-stage2-face/v07/Mia_ReusedFoundation_DetailedHair.blend'
SOURCE=Path(r'D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in [BASE,DETAIL,SOURCE]}
bpy.ops.wm.open_mainfile(filepath=str(BASE));face=bpy.data.objects[h.FACE_NAME];body=bpy.data.objects[h.BODY_NAME]
col=bpy.data.collections.new('MIA_V11_STATIC_DETAILED_HAIR');bpy.context.scene.collection.children.link(col)
with bpy.data.libraries.load(str(DETAIL),link=False) as (src,dst):dst.objects=['MIA_PIXAL_HAIR_DESIGN_SEPARATE','SINGLE_HAIR_MIXED_REVIEW']
imports=list(dst.objects)
for o in imports:col.objects.link(o)
bpy.context.view_layer.update()
parts=[];manifest=[]
def mapped(p):
 q=Vector((-p.x,-p.y,p.z));q.z=1.465+(q.z-1.465)*.94
 upper=h._smooth((q.z-1.635)/.075);q.z-=.038*upper;q.x*=1-.072*upper;q=h._crown_dome(q,upper)
 q=h._adult_landmark_map(h._scale_head_about_chin(q));return Vector((-q.x,-q.y,q.z))
def extract(o,ids,name,transform):
 old=o.data;used=sorted({v for i in ids for v in old.polygons[i].vertices});remap={v:i for i,v in enumerate(used)}
 m=bpy.data.meshes.new(name);m.from_pydata([transform(o.matrix_world@old.vertices[i].co) for i in used],[],[[remap[v] for v in old.polygons[i].vertices] for i in ids])
 for mat in old.materials:m.materials.append(mat)
 for layer in old.uv_layers:
  uv=m.uv_layers.new(name=layer.name)
  for new,ix in zip(m.polygons,ids):
   src=old.polygons[ix];new.material_index=src.material_index;new.use_smooth=True
   for a,b in zip(new.loop_indices,src.loop_indices):uv.data[a].uv=layer.data[b].uv
 obj=bpy.data.objects.new(name,m);col.objects.link(obj);obj['source_object']=o.name;obj['source_polygons']=ids;obj['static_hair_only']=True;parts.append(obj)
 manifest.append({'part':name,'source_object':o.name,'polygons':len(ids),'vertices':len(used),'removed_from_source_polygon_count':len(old.polygons)-len(ids)})
 return obj
for o in imports:
 lower=o.name.startswith('SINGLE_HAIR')
 image=next(n.image for n in o.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image);w,hh=image.size;pix=np.array(image.pixels[:]).reshape(hh,w,4);uv=o.data.uv_layers.active.data
 groups={'Rear':[]} if lower else {'Bangs':[],'CrownAndCheekLocks':[]}
 for p in o.data.polygons:
  t=sum((uv[i].uv for i in p.loop_indices),Vector((0,0)))/p.loop_total;c=pix[max(0,min(hh-1,int(t.y*hh))),max(0,min(w-1,int(t.x*w))),:3]
  q=o.matrix_world@p.center
  warm=c[0]-c[2]>.065 and c[0]>.35
  if warm or c.mean()>.30:continue
  if lower:
   if abs(q.x)>.208:continue
   groups['Rear'].append(p.index)
  else:
   # Reject low central neck/paint fragments only inside the hair-owned source.
   if q.z<1.555 and abs(q.x)<.064 and q.y<.035:continue
   groups['Bangs' if q.y<-.025 and q.z<1.685 else 'CrownAndCheekLocks'].append(p.index)
 def fit(p):
  if lower:
   t=(p.z-1.268)/(.176)
   return Vector((p.x*.76,p.y*.76+.018,1.075+.435*t))
  q=mapped(p);q.x*=.90
  if p.y<-.02:q.y+=.012*h._smooth((1.71-p.z)/.15)
  return q
 for group,ids in groups.items():extract(o,ids,'MIA_V11_Hair_'+group,fit)
 bpy.data.objects.remove(o,do_unlink=True)
# Independent scalp support from copies; original full skin is untouched.
capmat=h._flat_paper_material('MIA_V11_IndependentScalp',(.055,.045,.045,1))
for o in [face,body]:
 evalob=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=bpy.data.meshes.new_from_object(evalob);tmp=bpy.data.objects.new('TEMP_SCALP_SOURCE',mesh);tmp.matrix_world=o.matrix_world;ids=[]
 for p in mesh.polygons:
  if o==face and p.material_index!=7:continue
  pts=[tmp.matrix_world@mesh.vertices[v].co for v in p.vertices]
  if all(q.z>1.585 or (q.y>.012 and q.z>1.498) for q in pts):ids.append(p.index)
 cap=extract(tmp,ids,'MIA_V11_Hair_Scalp_'+('Front' if o==face else 'Rear'),lambda p: Vector((p.x*1.008,p.y*1.008,p.z+.0006)))
 cap.data.materials.clear();cap.data.materials.append(capmat)
 for p in cap.data.polygons:p.material_index=0
 bpy.data.objects.remove(tmp,do_unlink=True)
# One left braid and half-up knot remain independently replaceable source parts.
with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n.startswith('MiaHair_') and ('Braid' in n or 'HalfUp_OneClosedKnot' in n or 'Knot_Wrap' in n)]
for o in dst.objects:
 col.objects.link(o)
bpy.context.view_layer.update()
for o in list(dst.objects):
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=bpy.data.meshes.new_from_object(e);world=o.matrix_world.copy();name=o.name
 new=bpy.data.objects.new('MIA_V11_'+name,mesh);col.objects.link(new)
 for v in mesh.vertices:v.co=mapped(world@v.co)
 new.data.materials.clear();new.data.materials.append(capmat)
 for p in new.data.polygons:p.material_index=0
 new['source_object']=name;parts.append(new);manifest.append({'part':new.name,'source_object':name,'role':'one left braid' if 'Braid' in name else 'half-up knot','polygons':len(mesh.polygons)})
 bpy.data.objects.remove(o,do_unlink=True)
s,c=h._review_scene(face,body)
for o in parts:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
s.render.resolution_x=s.render.resolution_y=850;c.data.ortho_scale=.75;h._aim(c,(0,-2,1.39),(0,.015,1.39))
bpy.ops.file.pack_all();native=OUT/'Mia_Static_DetailedHair_v11.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native))
# All evidence is rendered from the actual saved static assembly.
bpy.ops.wm.open_mainfile(filepath=str(native));s=bpy.context.scene;c=s.camera
for label,loc in [('front',(0,-2,1.39)),('three_quarter_l',(1.4,-1.4,1.39)),('three_quarter_r',(-1.4,-1.4,1.39)),('profile',(2,0,1.39)),('back',(0,2,1.39))]:
 h._aim(c,loc,(0,.015,1.39));s.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
report={'native_sha256':sha(native),'recipe_sha256':sha(Path(__file__).resolve()),'source_sha256_before':before,'source_sha256_after':{str(p):sha(p) for p in [BASE,DETAIL,SOURCE]},'parts':manifest,'base_choice':'v09 preserves approved body and complete Face44; v10 ribbon hair and cheek taper excluded','limits':['Static sculpt study, not ART approved','Detailed source contains prior cut boundaries; cleanup is restricted to hair-owned polygons','Original Face44 eye/mouth material islands remain on their preserved master; hair parts are separate','No rig weights motion or pose validation authored']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2))
print('NATIVE_SHA',report['native_sha256'])
