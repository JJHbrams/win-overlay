"""Build the non-destructive Mia Stage-1 design blockout from preserved Pixal sources.

Run with Blender background mode only.  This intentionally records mixed semantic regions
instead of pretending a generated, UV-split mesh is production topology.
"""
import argparse, hashlib, json, math, os, sys
from array import array
from collections import Counter
from pathlib import Path
import bpy
from mathutils import Vector

PIXELS = {}
ALBEDO_READS = Counter()
BRAID_SOURCE=Path('D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend')

def base_image(mat):
 if not mat or not mat.use_nodes: return None
 bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not bs: return None
 pending=[l.from_node for l in bs.inputs['Base Color'].links]; visited=set()
 while pending:
  n=pending.pop()
  if n in visited: continue
  visited.add(n)
  if n.type=='TEX_IMAGE' and n.image: return n.image
  pending.extend(l.from_node for pin in n.inputs for l in pin.links)
 return None

def face_rgb(source, poly):
 image=base_image(source.data.materials[poly.material_index])
 if image is None or not source.data.uv_layers.active:
  raise RuntimeError('Missing source albedo/UV for semantic review: '+source.name)
 if image.name not in PIXELS:
  w,h=image.size; pixels=array('f',[0.0])*(w*h*4); image.pixels.foreach_get(pixels)
  PIXELS[image.name]=(w,h,pixels)
 w,h,pixels=PIXELS[image.name]; uv=source.data.uv_layers.active
 u=sum(uv.data[i].uv.x for i in poly.loop_indices)/poly.loop_total
 v=sum(uv.data[i].uv.y for i in poly.loop_indices)/poly.loop_total
 ix=min(w-1,max(0,int(u*w))); iy=min(h-1,max(0,int(v*h))); k=(iy*w+ix)*4
 ALBEDO_READS[source.name]+=1
 return tuple(pixels[k+j] for j in range(3))

def full_label(q,rgb):
 x,y,z=q; r,g,b=rgb; lum=(r+g+b)/3
 warm_skin=r>.48 and r-b>.055 and r-g>.015
 navy=b-r>.018 and lum<.62
 hair=abs(r-b)<.07 and r>=b-.012 and lum<.66
 if abs(x)>.25 and .72<z<.94 and (warm_skin or z<.86): return 'SKIN_MIXED_REVIEW'
 if z>.80: return 'REPLACED_REFERENCE_UPPER_BODY'
 # Keep shoulders/collar instead of removing an entire horizontal torso slice.
 if z>1.375: return 'HEAD_MIXED_REVIEW'
 if z>1.19 and hair and (y>.045 or abs(x)>.115): return 'HAIR_MIXED_REVIEW'
 if z<.24: return 'SHOES_MIXED_REVIEW'
 if warm_skin and (abs(x)>.25 or (abs(x)<.14 and z>1.04)): return 'SKIN_MIXED_REVIEW'
 if y>.105 and .86<z<1.14 and x>.015: return 'BAG_MIXED_REVIEW'
 if z>.92 and r-b>.04 and r-g>.015 and lum<.58: return 'STRAP_MIXED_REVIEW'
 if z>1.0 and ((g>r*1.3 and b>r*1.2) or (r-b>.16 and g>b*1.2)):
  return 'HARDWARE_MIXED_REVIEW'
 if navy and z>.84: return 'CARDIGAN_MIXED_REVIEW'
 if z<1.05: return 'PANTS_MIXED_REVIEW'
 if y<.035 and abs(x)<.18 and z>1.16: return 'CROP_MIXED_REVIEW'
 if y<.035 and abs(x)<.17 and 1.05<z<1.17 and lum>.48: return 'INNER_BAND_MIXED_REVIEW'
 return 'CARDIGAN_MIXED_REVIEW'

def single_label(q,rgb):
 x,y,z=q; r,g,b=rgb; lum=(r+g+b)/3
 if z>1.38: return 'HEAD_MIXED_REVIEW'
 # Neck and gray/brown hair remain; blue clothing, brown strap and colored pin do not.
 if abs(x)<.065 and z>1.285 and r>.48 and r-b>.045: return 'HEAD_MIXED_REVIEW'
 if .10<x<.22 and z<1.445 and y<.04: return 'REPLACED_REFERENCE_BUST_GARMENT_STRAP'
 if y<.09 or z<1.20: return 'REPLACED_REFERENCE_BUST_GARMENT_STRAP'
 if z<1.345 and y<.025 and abs(x)<.135: return 'REPLACED_REFERENCE_BUST_GARMENT_STRAP'
 strap_x=.15-.97*(z-.95)
 if .94<z<1.35 and y<.025 and abs(x-strap_x)<.032: return 'REPLACED_REFERENCE_BUST_GARMENT_STRAP'
 brown_strap=r-b>.075 and r-g>.035
 colored_pin=(g>r*1.25 and b>r*1.2) or (r-b>.18 and g>b*1.2)
 gray_hair=r>=b-.005 and r>=g-.005 and lum<.85
 if gray_hair and not brown_strap and not colored_pin: return 'HAIR_MIXED_REVIEW'
 return 'REPLACED_REFERENCE_BUST_GARMENT_STRAP'

def coverage_record(source, parts):
 ids=[int(i) for _,ob,_ in parts for i in ob['source_poly_indices']]
 counts=Counter(ids); expected=set(range(len(source.data.polygons)))
 duplicate=sum(n-1 for n in counts.values() if n>1)
 missing=len(expected-set(counts)); invalid=len(set(counts)-expected)
 if duplicate or missing or invalid: raise RuntimeError('Partition coverage failed: '+source.name)
 return {'source':source.name,'faces':len(expected),'assigned':len(ids),'unique_assigned':len(counts),
         'overlap':duplicate,'unassigned':missing,'invalid_indices':invalid}

def av(): return sys.argv[sys.argv.index('--') + 1:]
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def collection(n, parent=None):
 c=bpy.data.collections.new(n); (parent or bpy.context.scene.collection).children.link(c); return c
def import_glb(path, c):
 before=set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(path))
 obs=[o for o in bpy.data.objects if o not in before]
 for o in obs:
  for old in list(o.users_collection): old.objects.unlink(o)
  c.objects.link(o)
 return [o for o in obs if o.type=='MESH']
def bb(obs):
 p=[o.matrix_world@Vector(q) for o in obs for q in o.bound_box]
 return Vector(tuple(min(getattr(x,a) for x in p) for a in 'xyz')),Vector(tuple(max(getattr(x,a) for x in p) for a in 'xyz'))
def move_roots(obs, root):
 for o in obs:
  if o.parent is None: o.parent=root
def split(mesh, labels, c, prefix, idmats):
 # Each source polygon enters exactly one new object; loop/UV values are copied unchanged.
 records=[]; seen=0
 for label, ids in labels.items():
  if not ids: continue
  src=mesh.data; used=sorted({v for i in ids for v in src.polygons[i].vertices}); remap={v:j for j,v in enumerate(used)}
  nm=bpy.data.meshes.new(prefix+'_'+label+'_MESH'); nm.from_pydata([src.vertices[v].co[:] for v in used], [], [[remap[v] for v in src.polygons[i].vertices] for i in ids]); nm.materials.clear()
  for m in src.materials: nm.materials.append(m)
  # from_pydata recreates loops in polygon order, preserving per-face-corner UV lookup.
  uvmax=0.0
  for uv0 in src.uv_layers:
   uv=nm.uv_layers.new(name=uv0.name)
   for ni,oi in enumerate(ids):
    op=src.polygons[oi]; np=nm.polygons[ni]
    for j in range(np.loop_total):
     uv.data[np.loop_start+j].uv=uv0.data[op.loop_start+j].uv[:]
     uvmax=max(uvmax,max(abs(uv.data[np.loop_start+j].uv[k]-uv0.data[op.loop_start+j].uv[k]) for k in (0,1)))
  for ni,oi in enumerate(ids): nm.polygons[ni].material_index=src.polygons[oi].material_index
  for poly in nm.polygons: poly.use_smooth=True
  coerr=max((max(abs(nm.vertices[j].co[k]-src.vertices[v].co[k]) for k in range(3)) for j,v in enumerate(used)),default=0.0)
  ob=bpy.data.objects.new(prefix+'_'+label,nm); c.objects.link(ob); ob.matrix_world=mesh.matrix_world.copy(); ob['source_poly_indices']=ids; ob['source_vertex_indices']=used; ob['semantic_label']=label; ob['id_material']=idmats[label].name;ob['position_max_error']=coerr;ob['uv_loop_max_error']=uvmax
  ob['source_object']=mesh.name; ob['verified_vertex_count']=len(used); ob['verified_uv_loop_count']=len(nm.loops)*len(nm.uv_layers)
  if coerr>1e-7 or uvmax>1e-7: raise RuntimeError('Partition coordinates or UV changed')
  records.append((label,ob,len(ids))); seen+=len(ids)
 return records,seen
def material(n,color):
 m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*color,1)
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=1
 return m
def idmaterial(n,color):
 m=bpy.data.materials.new(n);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');e=nt.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1);e.inputs['Strength'].default_value=1;nt.links.new(e.outputs[0],o.inputs['Surface']);return m
def aim(ob, target): ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
def guide_material(original):
 image=base_image(original)
 if not image: raise RuntimeError('No albedo for guide material')
 m=bpy.data.materials.new('GUIDE_ALBEDO_'+original.name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
 t=n.new('ShaderNodeTexImage');t.image=image;e=n.new('ShaderNodeEmission');o=n.new('ShaderNodeOutputMaterial')
 m.node_tree.links.new(t.outputs['Color'],e.inputs['Color']);m.node_tree.links.new(e.outputs[0],o.inputs['Surface'])
 return m

def wire_material():
 m=idmaterial('ACTUAL_GEOMETRY_WIREFRAME',(.55,.58,.61));nt=m.node_tree
 e=next(n for n in nt.nodes if n.type=='EMISSION');wire=nt.nodes.new('ShaderNodeWireframe');wire.use_pixel_size=True;wire.inputs['Size'].default_value=.7
 mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.55,.58,.61,1);mix.inputs[2].default_value=(.015,.02,.025,1)
 nt.links.new(wire.outputs[0],mix.inputs[0]);nt.links.new(mix.outputs[0],e.inputs['Color']);return m

def toon_fabric(name, color):
 m=idmaterial(name,color);nt=m.node_tree;e=next(n for n in nt.nodes if n.type=='EMISSION')
 geo=nt.nodes.new('ShaderNodeNewGeometry');dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.2,-.65,.73)
 ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.1;ramp.color_ramp.elements[0].color=(.52,.52,.52,1);ramp.color_ramp.elements[1].position=.7
 mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[1].default_value=(*color,1)
 nt.links.new(geo.outputs['Normal'],dot.inputs[0]);nt.links.new(dot.outputs['Value'],ramp.inputs[0]);nt.links.new(ramp.outputs['Color'],mul.inputs[2]);nt.links.new(mul.outputs[0],e.inputs['Color']);return m

def add_garment_cages(c,idmats):
 def surface(name,verts,faces,mat,label,thickness=.004):
  mesh=bpy.data.meshes.new(name+'_MESH');mesh.from_pydata(verts,[],faces);mesh.update()
  ob=bpy.data.objects.new(name,mesh);c.objects.link(ob);mesh.materials.append(mat)
  for poly in mesh.polygons: poly.use_smooth=True
  ob['role']='NEW_EDITABLE_DESIGN_CAGE_NOT_FINAL_TOPOLOGY';ob['id_material']=idmats[label].name
  if len(faces)>20:
   sub=ob.modifiers.new('Blockout surface smoothing','SUBSURF');sub.levels=sub.render_levels=1
  if thickness:
   mod=ob.modifiers.new('Garment thickness','SOLIDIFY');mod.thickness=thickness;mod.offset=0
  return ob
 crop=toon_fabric('CROP_GUIDE_GRAY',(.24,.265,.285));coat=toon_fabric('CARDIGAN_GUIDE_CHARCOAL',(.043,.062,.071));band=toon_fabric('INNER_BAND_GUIDE',(.48,.46,.42));strap=toon_fabric('STRAP_GUIDE',(.035,.028,.023))
 # The crop has an actual neck opening and a structured raised front hem.
 rows=[(1.155,.154,.151,.087),(1.205,.166,.177,.092),(1.285,.174,.178,.096),(1.34,.218,.111,.105),(1.39,.053,.059,.055)]
 n=48;verts=[];faces=[]
 for j,(z,rx,front,back) in enumerate(rows):
  for i in range(n):
   t=i*math.tau/n;sy=math.sin(t);zz=z+(.018*max(0,-sy) if j==0 else 0)
   verts.append((rx*math.cos(t),-.009+(front if sy<0 else back)*sy,zz))
 for j in range(len(rows)-1):
  for i in range(n): faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 made=[surface('CROP_EDITABLE_BLOCKOUT',verts,faces,crop,'CROP_MIXED_REVIEW',.006)]
 verts=[];faces=[]
 for z,rx,front,back in [(1.105,.139,.107,.084),(1.14,.143,.114,.086)]:
  for i in range(n):
   t=i*math.tau/n;sy=math.sin(t);verts.append((rx*math.cos(t),-.006+(front if sy<0 else back)*sy,z))
 for i in range(n):faces.append((i,(i+1)%n,n+(i+1)%n,n+i))
 made.append(surface('INNER_BAND_EDITABLE_BLOCKOUT',verts,faces,band,'INNER_BAND_MIXED_REVIEW',.004))
 # Open-front cardigan body: surfaces reach the neck/shoulders without planar source cuts.
 rows=[(.82,.205,.155),(.86,.211,.161),(.98,.197,.151),(1.12,.185,.143),(1.26,.211,.142),(1.33,.243,.127),(1.385,.086,.077)]
 n=40;verts=[];faces=[];limit=math.pi-.63
 for z,rx,ry in rows:
  for i in range(n+1):
   t=-limit+2*limit*i/n;verts.append((rx*math.sin(t),.017+ry*math.cos(t),z))
 for row in range(len(rows)-1):
  for i in range(n): a=row*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
 made.append(surface('CARDIGAN_BODY_EDITABLE_BLOCKOUT',verts,faces,coat,'CARDIGAN_MIXED_REVIEW',.009))
 # A-pose sleeves have independent swept volume and open cuffs.
 for side in (-1,1):
  centers=[Vector((side*.175,.012,1.34)),Vector((side*.205,.012,1.32)),Vector((side*.245,.01,1.24)),Vector((side*.287,.004,1.13)),Vector((side*.312,-.009,1.015)),Vector((side*.323,-.015,.885))]
  radii=[.065,.102,.105,.094,.086,.061];verts=[];faces=[];n=24
  for row,(center,radius) in enumerate(zip(centers,radii)):
   tangent=(centers[min(row+1,len(centers)-1)]-centers[max(0,row-1)]).normalized();a=Vector((0,1,0));b=tangent.cross(a).normalized()
   for i in range(n):t=i*math.tau/n;verts.append(tuple(center+a*math.cos(t)*radius*.92+b*math.sin(t)*radius))
  for row in range(len(centers)-1):
   for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
  faces.append(tuple(reversed(range(n))))
  made.append(surface(('LEFT' if side>0 else 'RIGHT')+'_CARDIGAN_SLEEVE_BLOCKOUT',verts,faces,coat,'CARDIGAN_MIXED_REVIEW',.009))
 # Flexible strap guide follows front, hip, rear bag and shoulder in three dimensions.
 path=[(-.15,-.075,1.405),(-.115,-.195,1.30),(-.02,-.188,1.16),(.155,-.145,1.005),(.222,.01,.995),(.128,.222,1.015),(-.11,.16,1.35),(-.15,.045,1.415)]
 verts=[];faces=[]
 for i,p in enumerate(path):
  center=Vector(p);tangent=(Vector(path[(i+1)%len(path)])-Vector(path[(i-1)%len(path)])).normalized();normal=Vector((0,-1 if p[1]<0 else 1,0));width=normal.cross(tangent).normalized()*.014
  verts.extend((tuple(center-width),tuple(center+width)))
 for i in range(len(path)): j=(i+1)%len(path);faces.append((2*i,2*i+1,2*j+1,2*j))
 made.append(surface('STRAP_EDITABLE_BLOCKOUT',verts,faces,strap,'STRAP_MIXED_REVIEW',.003))
 # Fit a clean hip/waist volume to the retained lower trouser legs.
 pants=toon_fabric('PANTS_WAIST_CHARCOAL_GUIDE',(.075,.082,.088));verts=[];faces=[];n=48
 for z,rx,ry in [(.785,.168,.108),(.85,.181,.117),(.94,.174,.111),(1.045,.15,.099)]:
  for i in range(n):t=i*math.tau/n;verts.append((rx*math.cos(t),ry*math.sin(t),z))
 for row in range(3):
  for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
 made.append(surface('PANTS_WAIST_EDITABLE_BLOCKOUT',verts,faces,pants,'PANTS_MIXED_REVIEW',.003))
 return made

def add_bag_blockout(c,idmats):
 coat=toon_fabric('BAG_CHARCOAL_GUIDE',(.035,.047,.052));panel=toon_fabric('BAG_PANEL_GUIDE',(.09,.125,.14));cyan=idmaterial('MEMORY_CYAN_GUIDE',(.035,.55,.64));brass=toon_fabric('MEMORY_BRASS_GUIDE',(.35,.22,.085))
 def box(name,loc,scale,mat,bevel=.01):
  bpy.ops.mesh.primitive_cube_add(size=1,location=loc);ob=bpy.context.object;ob.name=name
  for cc in list(ob.users_collection):cc.objects.unlink(ob)
  c.objects.link(ob)
  for v in ob.data.vertices:
   v.co.x*=scale[0];v.co.y*=scale[1];v.co.z*=scale[2]
  ob.data.materials.append(mat);ob['id_material']=idmats['BAG_MIXED_REVIEW'].name;ob['role']='NEW_EDITABLE_BAG_BLOCKOUT'
  b=ob.modifiers.new('Rounded bag corners','BEVEL');b.width=bevel;b.segments=3
  return ob
 made=[box('BAG_REAR_HIP_BLOCKOUT',(.15,.195,1.005),(.20,.068,.145),coat,.014),box('BAG_MEMORY_PANEL_BLOCKOUT',(.15,.232,1.015),(.153,.009,.083),panel,.009)]
 for x,z in [(.127,1.02),(.176,.985)]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.010,location=(x,.245,z));ob=bpy.context.object;ob.name='MEMORY_BADGE_GUIDE'
  for cc in list(ob.users_collection):cc.objects.unlink(ob)
  c.objects.link(ob);ob.scale.y=.3;ob.data.materials.append(cyan if x<.15 else brass);ob['id_material']=idmats['HARDWARE_MIXED_REVIEW'].name;made.append(ob)
 return made

def reuse_authored_braid(c,idmats):
 if not BRAID_SOURCE.exists(): raise RuntimeError('Preserved authored braid source missing')
 with bpy.data.libraries.load(str(BRAID_SOURCE),link=False) as (src,dst):
  dst.objects=[n for n in src.objects if n.startswith('MiaHair_LEFT_OneBraid_Lane') or n=='MiaHair_Braid_Tail']
 made=[];mat=toon_fabric('REUSED_BRAID_GRAPHITE_GUIDE',(.039,.032,.03))
 for ob in dst.objects:
  if not ob or ob.type!='MESH': continue
  ob.name='REUSED_'+ob.name;c.objects.link(ob);ob.hide_render=False;ob.hide_viewport=False
  ob.data.materials.clear();ob.data.materials.append(mat)
  for poly in ob.data.polygons:poly.material_index=0
  for v in ob.data.vertices:
   t=min(1,max(0,(1.60-v.co.z)/.31));v.co.y-=.02+.025*t;v.co.z=1.60+(v.co.z-1.60)*1.18
  ob['role']='REUSED_EDITABLE_BRAID_DESIGN_NOT_FINAL_RIG';ob['id_material']=idmats['HAIR_MIXED_REVIEW'].name;ob['reuse_source']=str(BRAID_SOURCE);made.append(ob)
 if len(made)<3: raise RuntimeError('Braid lanes not found in preserved source')
 return made
def render(scene,cam,out,name,target,scale,clay=None,wire=False,ids=False):
 key=name.replace('semanticID_','').replace('head_','').replace('proxy_','')
 yaw={'front':0,'side':90,'back':180,'threequarter_right':45,'threequarter_left':315,'perspective':35}[key]
 r=scale*3; rad=math.radians(yaw);cam.location=target+Vector((r*math.sin(rad),-r*math.cos(rad),scale*.10));aim(cam,target);cam.data.type='PERSP' if name=='perspective' else 'ORTHO';cam.data.ortho_scale=scale;cam.data.lens=58
 old=scene.view_layers[0].material_override; scene.view_layers[0].material_override=wire_material() if wire else clay
 saved=[]
 if ids:
  for o in scene.objects:
   if o.type=='MESH' and 'id_material' in o:
    saved.append((o,list(o.data.materials),[p.material_index for p in o.data.polygons]))
    o.data.materials.clear();o.data.materials.append(bpy.data.materials[o['id_material']])
    for p in o.data.polygons:p.material_index=0
 for o in scene.objects: o.show_wire=wire and o.type=='MESH';o.show_all_edges=wire and o.type=='MESH'
 scene.render.filepath=str(out/(name+('_semanticID' if ids else ('_clay' if clay else '_guidecolor'))+('_wire' if wire else '')+'.png'));bpy.ops.render.render(write_still=True);scene.view_layers[0].material_override=old
 for ob,mats,indices in saved:
  ob.data.materials.clear()
  for m in mats: ob.data.materials.append(m)
  for p,i in zip(ob.data.polygons,indices): p.material_index=i
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--single',required=True);p.add_argument('--full',required=True);p.add_argument('--body-proxy');a=p.parse_args(av());out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
 before={'pixal_single':digest(a.single),'pixal_full':digest(a.full)}
 if a.body_proxy: before['body_proxy']=digest(a.body_proxy)
 before['authored_braid']=digest(BRAID_SOURCE)
 expected={'pixal_single':'97d76c20e08d92b1e05079b9ec5d340683863a843f1d434a7dcd7c907fb34ada','pixal_full':'40ee1d976a20988e8959102a6ec053a892fd432b9d47adf38322fbf562e55972','body_proxy':'d90744a9ec2370ae8d9564e482fbffd6b2485334f9571278d4482ce26ac943ca','authored_braid':'9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6'}
 if any(value!=expected[key] for key,value in before.items()):
  raise RuntimeError('This design recipe is calibrated to the recorded source hashes; re-review changed sources before fitting')
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.name='Mia_DesignBlockout_v01';s['stage_status']='INCOMPLETE — static Stage 1 design blockout only; not retopology, rig, expressions, physics, or 30fps event approval';s.render.engine='BLENDER_EEVEE';s.render.resolution_x=700;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 world=bpy.data.worlds.new('Mia neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.055,.065,.08,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35;s.world=world
 visible=collection('MIA_STAGE1_VISIBLE'); archive=collection('ARCHIVE_REPLACED_REFERENCE'); proxies=collection('PROXIES_HIDDEN')
 labels_all=['HEAD_MIXED_REVIEW','HAIR_MIXED_REVIEW','SKIN_MIXED_REVIEW','CROP_MIXED_REVIEW','INNER_BAND_MIXED_REVIEW','CARDIGAN_MIXED_REVIEW','PANTS_MIXED_REVIEW','SHOES_MIXED_REVIEW','BAG_MIXED_REVIEW','STRAP_MIXED_REVIEW','HARDWARE_MIXED_REVIEW','REPLACED_REFERENCE_UPPER_BODY','REPLACED_REFERENCE_BUST_GARMENT_STRAP']
 palette=[(.85,.15,.15),(.2,.25,.9),(.95,.65,.15),(.15,.8,.35),(.75,.2,.8),(.1,.7,.75),(.8,.45,.15),(.25,.85,.85),(.95,.25,.5),(.5,.8,.15),(.7,.7,.7),(.15,.15,.15)]
 idmats={n:idmaterial('ID_'+n,palette[i%len(palette)]) for i,n in enumerate(labels_all)}
 fullraw=collection('SOURCE_FULL_RAW',archive); full=import_glb(a.full,fullraw);lo,hi=bb(full);scale=1.7/(hi.z-lo.z);root=bpy.data.objects.new('FULL_PREVIEW_ROOT_UNIFORM',None);fullraw.objects.link(root);move_roots(full,root);root.scale=(scale,)*3;bpy.context.view_layer.update();lo,hi=bb(full);root.location.z-=lo.z;bpy.context.view_layer.update();lo,hi=bb(full)
 # full source is one generated surface: broad static ownership labels remain MIXED_REVIEW pending visual ID review.
 fullparts=[]; coverage=[]
 for source in full:
  labels={n:[] for n in labels_all[:-1]}
  for poly in source.data.polygons:
   q=source.matrix_world@poly.center; z=q.z; x=q.x; y=q.y
   label=full_label(q,face_rgb(source,poly))
   labels[label].append(poly.index)
  parts,n=split(source,labels,visible,'FULL',idmats);coverage.append(coverage_record(source,parts));fullparts+=parts
  source.hide_render=True;source.hide_viewport=True
 # hide full generated head to prevent duplicate face; its preserved partition stays in archive.
 for label,ob,n in fullparts:
  if label in {'REPLACED_REFERENCE_UPPER_BODY','HEAD_MIXED_REVIEW','HAIR_MIXED_REVIEW','CROP_MIXED_REVIEW','INNER_BAND_MIXED_REVIEW','CARDIGAN_MIXED_REVIEW','STRAP_MIXED_REVIEW','HARDWARE_MIXED_REVIEW','BAG_MIXED_REVIEW'}: ob.hide_render=True;ob.hide_viewport=True
 single_raw=collection('SOURCE_SINGLE_RAW',archive); single=import_glb(a.single,single_raw);sl,sh=bb(single);ss=.78/(sh.z-sl.z);sr=bpy.data.objects.new('SINGLE_HEAD_PREVIEW_ROOT_UNIFORM',None);single_raw.objects.link(sr);move_roots(single,sr);sr.scale=(ss,)*3;bpy.context.view_layer.update();sl,sh=bb(single);sr.location+=Vector((-(sl.x+sh.x)/2,-(sl.y+sh.y)/2,1.75-sh.z));bpy.context.view_layer.update()
 singleparts=[]
 for source in single:
  labels={'HEAD_MIXED_REVIEW':[],'HAIR_MIXED_REVIEW':[],'REPLACED_REFERENCE_BUST_GARMENT_STRAP':[]}
  for poly in source.data.polygons:
   q=source.matrix_world@poly.center; labels[single_label(q,face_rgb(source,poly))].append(poly.index)
  parts,n=split(source,labels,visible,'SINGLE',idmats);coverage.append(coverage_record(source,parts));singleparts+=parts;source.hide_render=True;source.hide_viewport=True
 for label,ob,n in singleparts:
  if label.startswith('REPLACED'): ob.hide_render=True;ob.hide_viewport=True
 new_garments=add_garment_cages(visible,idmats)+add_bag_blockout(visible,idmats)
 reused_braid=reuse_authored_braid(visible,idmats)
 # independent, hidden scalp volume proxy; it is evidence, not a shell replacement.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(0,.055,1.61));sc=bpy.context.object;sc.name='SCALP_VOLUME_PROXY_HIDDEN';sc.scale=(.09,.10,.13)
 for cc in list(sc.users_collection):cc.objects.unlink(sc)
 proxies.objects.link(sc);sc.hide_render=True;sc.hide_viewport=True
 if a.body_proxy and Path(a.body_proxy).exists():
  bc=collection('OPTIONAL_NATIVE_BODY_PROXY_PRESERVED',proxies)
  with bpy.data.libraries.load(a.body_proxy,link=False) as (src,dst): dst.objects=list(src.objects)
  for o in dst.objects:
   if o: bc.objects.link(o);o.hide_render=True;o.hide_viewport=True
 guide_cache={}
 for ob in visible.objects:
  if ob.type=='MESH':
   for slot in ob.material_slots:
    original=slot.material
    if 'source_object' in ob:
     if original.name not in guide_cache: guide_cache[original.name]=guide_material(original)
     slot.material=guide_cache[original.name]
 # An explicit editable neck volume joins the design surfaces; no source face is edited.
 neck_source=single[0]; candidates=[]
 for poly in neck_source.data.polygons:
  q=neck_source.matrix_world@poly.center
  if abs(q.x)<.05 and 1.37<q.z<1.49:
   r,g,b=face_rgb(neck_source,poly)
   if r>.48 and r-b>.045:
    candidates.append((abs(q.z-1.43),poly))
 if not candidates: raise RuntimeError('No reliable neck albedo sample')
 sample_poly=min(candidates,key=lambda item:item[0])[1]
 sample_uv=sum((neck_source.data.uv_layers.active.data[i].uv for i in sample_poly.loop_indices),Vector((0,0)))/sample_poly.loop_total
 neck_vertices=[]; neck_faces=[]; rings=[(1.30,.055,.062),(1.35,.051,.059),(1.42,.043,.052),(1.48,.050,.059)]
 for z,rx,ry in rings:
  neck_vertices.extend((rx*math.cos(i*math.tau/32),-.012+ry*math.sin(i*math.tau/32),z) for i in range(32))
 for row in range(len(rings)-1):
  for i in range(32):
   j=(i+1)%32;neck_faces.append((row*32+i,row*32+j,(row+1)*32+j,(row+1)*32+i))
 neck_faces.extend((tuple(reversed(range(32))),tuple((len(rings)-1)*32+i for i in range(32))))
 neck_mesh=bpy.data.meshes.new('NECK_DESIGN_BRIDGE_MESH');neck_mesh.from_pydata(neck_vertices,[],neck_faces)
 neck=bpy.data.objects.new('NECK_DESIGN_VOLUME_BRIDGE',neck_mesh);visible.objects.link(neck)
 neck['role']='NEW_DESIGN_VOLUME_NOT_FINAL_TOPOLOGY';neck['id_material']=idmats['SKIN_MIXED_REVIEW'].name
 neck_mesh.materials.append(guide_cache[neck_source.data.materials[sample_poly.material_index].name])
 neck_uv=neck_mesh.uv_layers.new(name='GUIDE_POINT_SAMPLE')
 for loop in neck_uv.data: loop.uv=sample_uv
 for poly in neck_mesh.polygons: poly.use_smooth=True
 # A separate abdomen volume makes the layer gap explicit rather than retaining torn cloth fragments.
 n=32;verts=[];faces=[]
 for z,rx,ry in [(.97,.15,.092),(1.035,.145,.09),(1.10,.128,.083),(1.18,.146,.097)]:
  for i in range(n): t=i*math.tau/n;verts.append((rx*math.cos(t),ry*math.sin(t),z))
 for row in range(3):
  for i in range(n): faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
 me=bpy.data.meshes.new('ABDOMEN_DESIGN_VOLUME_MESH');me.from_pydata(verts,[],faces);abd=bpy.data.objects.new('ABDOMEN_EDITABLE_BLOCKOUT',me);visible.objects.link(abd)
 me.materials.append(neck_mesh.materials[0]);abd['id_material']=idmats['SKIN_MIXED_REVIEW'].name;abd['role']='NEW_EDITABLE_ANATOMY_BLOCKOUT'
 uv=me.uv_layers.new(name='GUIDE_POINT_SAMPLE')
 for loop in uv.data:loop.uv=sample_uv
 for poly in me.polygons:poly.use_smooth=True
 # cameras/lights
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='MIA_STAGE1_CAMERA';s.camera=cam
 for loc,en,size in [((-3,-4,4),1100,3),((3,-3,2),650,3),((2,3,3),800,2)]:
  bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.data.energy=en;L.data.shape='DISK';L.data.size=size;aim(L,Vector((0,0,.9)))
 clay=material('MIA_CLAY',(.43,.46,.5)); guide=material('MIA_GUIDE_CHARCOAL',(.12,.14,.17))
 for name in ['front','side','back','threequarter_right','threequarter_left','perspective']: render(s,cam,out,name,Vector((0,0,.88)),1.95)
 for name in ['front','side','back']: render(s,cam,out,'semanticID_'+name,Vector((0,0,.88)),1.95,ids=True)
 render(s,cam,out,'front',Vector((0,0,.88)),1.95,clay);render(s,cam,out,'threequarter_right',Vector((0,0,.88)),1.95,clay);render(s,cam,out,'threequarter_right',Vector((0,0,1.58)),.62,clay,True)
 for name in ['front','side','back','threequarter_right','threequarter_left']:
  render(s,cam,out,'head_'+name,Vector((0,0,1.49)),.58)
 visibility=[(o,o.hide_render) for o in visible.objects if o.type=='MESH']
 for o,_ in visibility: o.hide_render=True
 sc.hide_render=False;render(s,cam,out,'proxy_front',Vector((0,.055,1.61)),.4,clay);sc.hide_render=True
 for o,hidden in visibility: o.hide_render=hidden
 after={'pixal_single':digest(a.single),'pixal_full':digest(a.full)}
 if a.body_proxy: after['body_proxy']=digest(a.body_proxy)
 after['authored_braid']=digest(BRAID_SOURCE)
 if before!=after: raise RuntimeError('external source hash changed')
 rows=[]
 for o in [x for x in visible.objects if x.type=='MESH']:
  lo,hi=bb([o]);rows.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'bbox_min':list(lo),'bbox_max':list(hi),'uv_layers':[u.name for u in o.data.uv_layers]})
 checks=[{'part':ob.name,'source':ob['source_object'],'position_max_error':ob['position_max_error'],
          'uv_loop_max_error':ob['uv_loop_max_error'],'vertices_compared':ob['verified_vertex_count'],
          'uv_loops_compared':ob['verified_uv_loop_count']} for ob in visible.objects if 'source_object' in ob]
 if not checks or any(r['vertices_compared']==0 or r['uv_loops_compared']==0 for r in checks): raise RuntimeError('Empty partition verification')
 report={'status':'INCOMPLETE','sources_before_sha256':before,'sources_after_sha256':after,'source_face_coverage':coverage,'coverage_all_100_percent':all(x['faces']==x['assigned'] and not x['overlap'] and not x['unassigned'] for x in coverage),'uv_partition_verification':checks,'parts':rows,'traceability':'Pixal full clothing/body is first-pass regional semantic ownership; Pixal single HEAD/HAIR partitions are visible and full head is hidden. Single bust/strap is hidden preserved reference.','unresolved':['semantic boundaries require ID review','generated partitions are not production topology or rig-ready','final retopo, UV transfer, rig, expression, physics and 30fps events are downstream']}
 report['albedo_sample_counts']=dict(ALBEDO_READS)
 report['classification_limit']='Color/spatial labels are a reviewed first pass, not clean production boundaries. Ambiguous regions remain MIXED_REVIEW.'
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 render(s,cam,out,'front',Vector((0,0,.88)),1.95)
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':
    area.spaces.active.region_3d.view_location=Vector((0,0,.88));area.spaces.active.region_3d.view_distance=3.1
    area.spaces.active.shading.type='MATERIAL'
 linked_before=[]
 for blocks in (bpy.data.node_groups,bpy.data.materials,bpy.data.images,bpy.data.meshes,bpy.data.armatures,bpy.data.actions,bpy.data.objects,bpy.data.collections):
  for datablock in list(blocks):
   if datablock.library:
    linked_before.append(datablock.name);datablock.make_local()
 report['localized_datablocks']=linked_before
 report['body_proxy_face_key_count']=next((len(ob.data.shape_keys.key_blocks) for ob in bpy.data.objects if ob.type=='MESH' and ob.name.startswith('Mia_Face_AnimeTopology') and ob.data.shape_keys),0)
 report['remaining_library_paths']=[lib.filepath for lib in bpy.data.libraries if lib.users>0]
 report['active_linked_datablocks']=[datablock.name for blocks in (bpy.data.node_groups,bpy.data.materials,bpy.data.images,bpy.data.meshes,bpy.data.armatures,bpy.data.actions,bpy.data.objects,bpy.data.collections) for datablock in blocks if datablock.library]
 report['new_neck_bridge']={'vertices':len(neck_mesh.vertices),'polygons':len(neck_mesh.polygons),'albedo_sample_uv':list(sample_uv),'purpose':'editable design volume; retopology and junction polish remain downstream'}
 report['new_garment_cages']=[{'name':ob.name,'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons)} for ob in new_garments]
 report['reused_authored_braid']=[ob.name for ob in reused_braid]
 report['import_triangle_accounting']={'pixal_single':{'raw_glb_triangles':198518,'duplicate_index_faces':5,'blender_imported_faces':198513},'pixal_full':{'raw_glb_triangles':196262,'duplicate_index_faces':2,'blender_imported_faces':196260},'coverage_basis':'Blender-imported faces, after exact duplicate triangle removal; original GLB bytes remain unchanged'}
 report['images']=[{'name':im.name,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images]
 bpy.ops.file.pack_all()
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(out/('Mia_DesignBlockout_'+out.name+'.blend')),check_existing=False)
if __name__=='__main__':main()
