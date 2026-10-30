#!/usr/bin/env python3
"""Build the v02 organic-hair checkpoint from frozen Mia anatomy v13 only."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

def arguments():
 p=argparse.ArgumentParser();v=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 for n in ('input','output','output-dir','report'):p.add_argument('--'+n,required=True)
 return p.parse_args(v)
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def mesh_fingerprint(o):
 h=hashlib.sha256();me=o.data
 for v in me.vertices:h.update(('{:.9f},{:.9f},{:.9f};'.format(*v.co)).encode())
 for p in me.polygons:h.update(('p'+','.join(map(str,p.vertices))+';').encode())
 uv=me.uv_layers.active
 if uv:
  for x in uv.data:h.update(('{:.9f},{:.9f};'.format(*x.uv)).encode())
 if me.shape_keys:
  for k in me.shape_keys.key_blocks:
   h.update(k.name.encode())
   for x in k.data:h.update(('{:.9f},{:.9f},{:.9f};'.format(*x.co)).encode())
 return h.hexdigest()
def collection(n):
 c=bpy.data.collections.get(n)
 if not c:c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c)
 return c
def add(o,c):c.objects.link(o);return o
def material(n,color):
 m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.76;b.inputs['Specular IOR Level'].default_value=.13;return m
def tag(o,role,side='CENTER'):
 o['owner']='Mia';o['role']=role;o['anatomical_side']=side;o['deformation_region']=role;o['stage']='HAIR_V02_REFINED';o['construction']='resampled_closed_flattened_quad_clump'
def catmull(points,n=72):
 p=[Vector(x) for x in points];out=[]
 for i in range(n):
  u=i/(n-1)*(len(p)-1);k=min(int(u),len(p)-2);t=u-k;a=p[max(k-1,0)];b=p[k];c=p[k+1];d=p[min(k+2,len(p)-1)]
  out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return out
def interp(a,t):
 x=t*(len(a)-1);i=min(int(x),len(a)-2);return a[i]*(1-x+i)+a[i+1]*(x-i)
def clump(name,controls,widths,depths,mat,c,role,side='CENTER',samples=72):
 pts=catmull(controls,samples);rings=12;verts=[];faces=[];prev=Vector((0,1,0)) if role in ('SIDE_LOCK','TEMPLE_FLOW','CROWN_FLOW') else Vector((1,0,0))
 # Deterministic secondary S-wave perturbation changes actual paths, not just shading/cross section.
 if role in ('SIDE_LOCK','REAR_LAYER'):
  phase=(sum(ord(x) for x in name)*2.3999632297)%(2*math.pi)
  for i,p in enumerate(pts):
   t=i/(samples-1);fall=t*t*(3-2*t);p.x+=fall*.007*math.sin(2*math.pi*1.85*t+phase);p.y+=fall*.009*math.cos(2*math.pi*1.65*t+phase)
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,samples-1)]-pts[max(i-1,0)]).normalized();across=prev-tangent*prev.dot(tangent)
  if across.length<.001:across=Vector((0,1,0))-tangent*tangent.y
  across.normalize()
  if across.dot(prev)<0:across=-across
  normal=tangent.cross(across).normalized();prev=across;w=interp(widths,i/(samples-1));d=interp(depths,i/(samples-1))*.55
  for j in range(rings):
   q=2*math.pi*j/rings;verts.append(p+across*math.cos(q)*w+normal*math.sin(q)*d)
 for i in range(samples-1):
  for j in range(rings):faces.append((i*rings+j,i*rings+(j+1)%rings,(i+1)*rings+(j+1)%rings,(i+1)*rings+j))
 faces += [tuple(range(rings-1,-1,-1)),tuple((samples-1)*rings+j for j in range(rings))]
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.materials.append(mat);me.update();o=add(bpy.data.objects.new(name,me),c);tag(o,role,side)
 for f in me.polygons:f.use_smooth=True
 return o
def scalp(c,mat):
 rx,ry,rz=.120,.133,.132;cen=Vector((0,.015,1.590));rows,segs=18,48;v=[];f=[]
 for i in range(rows+1):
  for j in range(segs):
   phi=2*math.pi*j/segs-math.pi/2;back=(math.sin(phi)+1)/2;t=math.radians(82+73*back)*i/rows;v.append(cen+Vector((rx*math.sin(t)*math.cos(phi),ry*math.sin(t)*math.sin(phi),rz*math.cos(t))))
 for i in range(rows):
  for j in range(segs):f.append((i*segs+j,i*segs+(j+1)%segs,(i+1)*segs+(j+1)%segs,(i+1)*segs+j))
 me=bpy.data.meshes.new('Mia_Hair_ScalpCap_Mesh');me.from_pydata(v,[],f);me.materials.append(mat);me.update();o=add(bpy.data.objects.new('Mia_Hair_ScalpCap',me),c);tag(o,'SCALP_CAP')
 for x in me.polygons:x.use_smooth=True
 z=o.modifiers.new('Scalp_Physical_Thickness','SOLIDIFY');z.thickness=.0022;z.offset=1
def bind(c,arm):
 if not arm or not arm.pose or not arm.pose.bones.get('J_Bip_C_Head'):return
 for o in c.objects:
  if o.type=='MESH':g=o.vertex_groups.new(name='J_Bip_C_Head');g.add(range(len(o.data.vertices)),1,'REPLACE');m=o.modifiers.new('Initial_Rigid_Head_Preview_Not_Final_Dynamics','ARMATURE');m.object=arm;m.show_viewport=True;m.show_render=True;o['initial_binding']='J_Bip_C_Head weight 1 assigned; initial rigid preview only, NOT final dynamics rig'
def world_bounds(o):
 pts=[o.matrix_world@v.co for v in o.data.vertices];return tuple(min(p[i] for p in pts) for i in range(3)),tuple(max(p[i] for p in pts) for i in range(3))
def aim(o,p,t):o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def review_lights(c):
 for n,p,e in [('Key',(.55,-.70,2.0),30),('Fill',(-.55,-.55,1.8),10),('Rim',(0,.65,1.9),18)]:
  d=bpy.data.lights.new('HairReview_'+n,'AREA');d.energy=e;d.shape='DISK';d.size=.7;o=add(bpy.data.objects.new('HairReview_'+n,d),c);aim(o,p,(0,0,1.48))
def main():
 a=arguments();src=Path(a.input);assert src.name=='Mia_AnimeAnatomy_v02_candidate_v13_body.blend','hair stage must start from fixed anatomy v13 input';before=digest(src);bpy.ops.wm.open_mainfile(filepath=str(src));assert before==digest(src)
 assert not bpy.data.collections.get('MIA_HAIR_V02_OWNED'),'reject prior hair-stage collection input'
 assert not any(str(o.get('stage','')).startswith('HAIR_V02') for o in bpy.data.objects),'reject prior hair-stage objects'
 face=bpy.data.objects.get('Mia_Face_AnimeTopology');body=bpy.data.objects.get('Mia_Body_Anatomy_Skin');assert face and body
 canonical=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('Mia_Face_AnimeTopology') or o.name.startswith('Mia_Body_Anatomy_Skin') or o.get('role') in ('FACE_ANIME_TOPOLOGY','BODY_ANATOMY_SKIN'))];faces=[o for o in canonical if o.name.startswith('Mia_Face_AnimeTopology') or o.get('role')=='FACE_ANIME_TOPOLOGY'];bodies=[o for o in canonical if o.name.startswith('Mia_Body_Anatomy_Skin') or o.get('role')=='BODY_ANATOMY_SKIN'];assert len(faces)==1 and len(bodies)==1,([o.name for o in faces],[o.name for o in bodies])
 visible=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and o.name in (face.name,body.name)];assert visible==[face.name,body.name],visible;canonical_before={face.name:mesh_fingerprint(face),body.name:mesh_fingerprint(body)}
 c=collection('MIA_HAIR_V02_OWNED');dark=material('Mia_Hair_V02_NeutralCharcoal',(.025,.023,.028));ash=material('Mia_Hair_V02_NeutralAsh',(.060,.055,.065));scalp(c,dark)
 # Two asymmetric primary swept masses break the former comb-like fringe.
 clump('Mia_Hair_PrimaryFront_Left',[(-.008,-.018,1.726),(-.055,-.070,1.700),(-.112,-.118,1.655),(-.075,-.152,1.590)],[.020,.030,.028,.003],[.004,.006,.005,.001],dark,c,'PRIMARY_FRONT')
 clump('Mia_Hair_PrimaryFront_Right',[(.010,-.015,1.724),(.050,-.060,1.704),(.098,-.108,1.668),(.050,-.148,1.612)],[.018,.029,.025,.003],[.004,.006,.005,.001],dark,c,'PRIMARY_FRONT')
 for i,x in enumerate((-.070,-.030,.018,.062)):
  tip=(1.602,1.575,1.605,1.588)[i];clump('Mia_Hair_SecondaryBang_%02d'%(i+1),[(x*.3,-.052,1.713),(x,-.120,1.675),(x*.68,-.151,tip)],[.010,.016,.002],[.003,.004,.001],dark,c,'FRONT_BANG')
 for side,label in ((-1,'RIGHT'),(1,'LEFT')):
  for j in range(6):
   x=.088+.010*j;end=1.285-.018*(j%3);y=-.022+.014*(j%3);clump('Mia_Hair_SideLock_%s_%02d'%(label,j+1),[(side*(.072+.007*j),.028,1.690),(side*x,-.032,1.630),(side*(x+.012),y,1.545),(side*(x-.004),y-.018,1.455),(side*(x+.014),y+.006,end)],[.010,.016,.018,.015,.002],[.004,.006,.007,.006,.001],dark,c,'SIDE_LOCK',label)
  # One broad parent temple flow covers each dome side, arcs then flicks outward.
  clump('Mia_Hair_PrimaryTemple_'+label,[(side*.012,.005,1.724),(side*.090,-.018,1.700),(side*.145,-.070,1.620),(side*.162,-.040,1.510),(side*.132,-.075,1.355),(side*.170,-.030,1.285)],[.018,.030,.032,.028,.020,.003],[.004,.006,.006,.005,.004,.001],dark,c,'TEMPLE_FLOW',label)
 xs=[-.112,-.096,-.080,-.064,-.048,-.032,-.016,0,.016,.032,.048,.064,.080,.096,.112,.088,-.072,.040]
 for j,x in enumerate(xs):
  layer=j%3;yy=.075+.025*layer;tip=1.235+.025*((j*5)%4);clump('Mia_Hair_RearWave_%02d'%(j+1),[(x*.55,.055,1.704),(x,yy,1.655),(x*1.10,yy+.018,1.570),(x*1.28,yy-.012,1.475),(x*1.14,yy+.020,1.365),(x*1.32,yy-.010,tip)],[.011,.017,.020,.018,.014,.002],[.004,.006,.008,.007,.005,.001],ash if j%5==0 else dark,c,'REAR_LAYER')
 # Broad rear parents and loose center layer give the knot an actual gathered destination.
 for side in (-1,1):clump('Mia_Hair_PrimaryRear_'+('R' if side<0 else 'L'),[(side*.018,.125,1.695),(side*.100,.152,1.650),(side*.142,.130,1.560),(side*.110,.175,1.430),(side*.150,.115,1.285)],[.018,.032,.034,.030,.003],[.004,.007,.007,.006,.001],dark,c,'PRIMARY_REAR')
 clump('Mia_Hair_CenterLoose',[(0,.138,1.690),(-.020,.180,1.620),(.022,.150,1.535),(-.018,.182,1.415),(.020,.140,1.300)],[.016,.027,.027,.022,.003],[.004,.006,.006,.005,.001],ash,c,'PRIMARY_REAR')
 # Surface-flow crown locks bridge the irregular part to temples/rear and break the helmet dome.
 for i,x in enumerate((-.085,-.060,-.035,-.012,.014,.040,.067,.092)):
  side=-1 if x<0 else 1;clump('Mia_Hair_CrownFlow_%02d'%(i+1),[(x*.18,-.005,1.724),(x*.55,-.052,1.708),(x,-.100,1.670),(x*1.22,-.060,1.605),(x*1.38,.010,1.545),(x*1.20,.045,1.485)],[.009,.014,.017,.015,.012,.002],[.003,.004,.004,.004,.003,.001],dark,c,'CROWN_FLOW','LEFT' if side>0 else 'RIGHT')
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.042,location=(0,.145,1.615));k=bpy.context.object;k.name='Mia_Hair_HalfUp_Knot';k.scale=(1.15,.75,.68);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);k.data.materials.append(dark);tag(k,'HALF_UP_KNOT');[q.objects.unlink(k) for q in list(k.users_collection)];c.objects.link(k)
 for q in k.data.polygons:q.use_smooth=True
 for i,sgn in enumerate((-1,0,1,-1,1,0),1):clump('Mia_Hair_KnotWrap_%02d'%i,[(sgn*.070,.120,1.670),(sgn*.052,.178,1.648),(sgn*.010,.190,1.615),(sgn*.045,.181,1.582)],[.009,.012,.012,.002],[.003,.004,.004,.001],dark,c,'KNOT_WRAP')
 for n,phase in enumerate((0,2.094,4.189),1):
  p=[]
  for i in range(12):t=i/11;p.append((.102+.038*t+.007*math.sin(6*math.pi*t+phase),-.010-.130*t+.004*math.cos(6*math.pi*t+phase),1.600-.380*t))
  clump('Mia_Hair_Braid_Left_Strand_%02d'%n,p,[.008,.009,.007,.005,.0025],[.004,.005,.004,.003,.0015],dark,c,'BRAID','LEFT',96)
 bind(c,bpy.data.objects.get('Armature'));bounds={o.name:world_bounds(o) for o in c.objects if o.type=='MESH'};allmin=tuple(min(b[0][i] for b in bounds.values()) for i in range(3));allmax=tuple(max(b[1][i] for b in bounds.values()) for i in range(3));assert allmin[0]>=-.20 and allmax[0]<=.20 and allmin[1]>=-.22 and allmax[1]<=.23 and allmin[2]>=1.16 and allmax[2]<=1.80,(allmin,allmax);kb=bounds['Mia_Hair_HalfUp_Knot'];assert all(kb[1][i]-kb[0][i]<.15 for i in range(3)),kb
 review=collection('MIA_HAIR_REVIEW');d=bpy.data.cameras.new('MIA_HAIR_REVIEW_CAMERA');d.type='ORTHO';cam=add(bpy.data.objects.new('MIA_HAIR_REVIEW_CAMERA',d),review);review_lights(review);sc=bpy.context.scene;sc.camera=cam;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.image_settings.file_format='PNG'
 out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);views={'front':((0,-1,1.49),.72),'left_3q':((.72,-.72,1.49),.72),'right_3q':((-.72,-.72,1.49),.72),'left_profile':((1,0,1.49),.72),'right_profile':((-1,0,1.49),.72),'back':((0,1,1.49),.72),'full_front':((0,-2,.90),2.0),'full_back':((0,2,.90),2.0),'full_left':((1.5,-1.3,.90),2.0),'full_right':((-1.5,-1.3,.90),2.0)};renders=[]
 canonical_after={face.name:mesh_fingerprint(face),body.name:mesh_fingerprint(body)};assert canonical_before==canonical_after,'canonical face/body data changed';bpy.ops.wm.save_as_mainfile(filepath=str(a.output));after=digest(src);assert after==before
 for n,(p,s) in views.items():d.ortho_scale=s;aim(cam,p,(0,.005,1.49) if s<1 else (0,0,.90));sc.render.filepath=str(out/(n+'.png'));bpy.ops.render.render(write_still=True);renders.append(str(out/(n+'.png')))
 Path(a.report).write_text(json.dumps({'input_sha256_before':before,'input_sha256_after':after,'input_unchanged':before==after,'canonical_visible_meshes':visible,'canonical_face_body_data_hash_before':canonical_before,'canonical_face_body_data_hash_after':canonical_after,'canonical_face_body_data_unchanged':canonical_before==canonical_after,'hair_world_bounds':bounds,'hair_world_bounds_total':[allmin,allmax],'hair_collection':c.name,'braid_assemblies':1,'braid_strands':3,'hair_meshes':[o.name for o in c.objects if o.type=='MESH'],'material_limits':{'materials':2,'roughness':.76,'specular_ior_level':.13},'actual_previews':renders,'status':'STAGE_EVIDENCE_ONLY_PENDING_ART_AND_216_AUDIT'},indent=2),encoding='utf-8')
if __name__=='__main__':main()
