"""REJECTED unexecuted face draft. Not a Mia production recipe.

The new skin uses the Face42 loop layout only as a topology template, fitted to
the actual Pixal facial surface.  It deliberately does not transfer Face42 keys.
"""
import argparse, hashlib, json, math, struct, sys
from pathlib import Path
import bpy
from mathutils import Vector
EYE_CENTERS={-1:(-.076,1.510),1:(.076,1.510)}

def cli():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--draft',action='store_true');return p.parse_args(sys.argv[sys.argv.index('--')+1:])
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def col(n,parent=None):
 c=bpy.data.collections.new(n);(parent or bpy.context.scene.collection).children.link(c);return c
def bbox(ob):
 q=[ob.matrix_world@Vector(v) for v in ob.bound_box];return Vector(map(min,*q)),Vector(map(max,*q))
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;b=next((x for x in m.node_tree.nodes if x.type=='BSDF_PRINCIPLED'),None);b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.85;return m
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def obj(c,n,vs,fs,m):
 me=bpy.data.meshes.new(n+'_MESH');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);c.objects.link(o);me.materials.append(m)
 for p in me.polygons:p.use_smooth=True
 return o
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<%dI'%len(p.vertices),*p.vertices))
 for uv in o.data.uv_layers:
  for x in uv.data:h.update(struct.pack('<2f',*x.uv))
 return h.hexdigest()
def split_by_material(src, indices, c, name, material):
 # Exact source coordinate/UV copy. Used for the actual Pixal hair partition.
 used=sorted({v for i in indices for v in src.data.polygons[i].vertices});rem={v:j for j,v in enumerate(used)}
 me=bpy.data.meshes.new(name+'_MESH');me.from_pydata([src.data.vertices[v].co[:] for v in used],[],[[rem[v] for v in src.data.polygons[i].vertices] for i in indices])
 for layer0 in src.data.uv_layers:
  layer=me.uv_layers.new(name=layer0.name)
  for ni,oi in enumerate(indices):
   a=src.data.polygons[oi];b=me.polygons[ni]
   for k in range(b.loop_total):layer.data[b.loop_start+k].uv=layer0.data[a.loop_start+k].uv[:]
 o=bpy.data.objects.new(name,me);c.objects.link(o);o.matrix_world=src.matrix_world.copy()
 if material:me.materials.append(material)
 else:
  for m in src.data.materials:me.materials.append(m)
  for ni,oi in enumerate(indices):me.polygons[ni].material_index=src.data.polygons[oi].material_index
 for p in me.polygons:p.use_smooth=True
 return o
def source_is_hair(src,p):
 # Same conservative color rule used by Stage1: do not delete unknown face pieces.
 if not src.data.uv_layers.active:return False
 im=None;m=src.data.materials[p.material_index]
 if m and m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:im=n.image;break
 if not im:return False
 uv=src.data.uv_layers.active;u=sum(uv.data[i].uv.x for i in p.loop_indices)/p.loop_total;v=sum(uv.data[i].uv.y for i in p.loop_indices)/p.loop_total
 w,h=im.size;pix=im.pixels;ix=min(w-1,max(0,int(u*w)));iy=min(h-1,max(0,int(v*h)));k=(iy*w+ix)*4;r,g,b=pix[k:k+3]
 return r>=b-.005 and r>=g-.005 and (r+g+b)/3<.85
def source_is_skin(src,p):
 if not src.data.uv_layers.active:return False
 m=src.data.materials[p.material_index];im=None
 if m and m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:im=n.image;break
 if not im:return False
 uv=src.data.uv_layers.active;u=sum(uv.data[i].uv.x for i in p.loop_indices)/p.loop_total;v=sum(uv.data[i].uv.y for i in p.loop_indices)/p.loop_total;w,h=im.size;k=(min(h-1,max(0,int(v*h)))*w+min(w-1,max(0,int(u*w))))*4;r,g,b=im.pixels[k:k+3]
 q=src.matrix_world@p.center
 return r>.48 and r-b>.045 and r-g>.015 and q.y<-.015 and q.z>1.407
def fit_face_template(template,target,skin,c):
 # Face42 supplies loop flow only.  Its placement is a landmark fit to actual
 # warm Pixal skin: chin, eye line, forehead, ear span and front skin plane.
 # This avoids fitting against hair bounds or treating the source's full bbox as a face.
 lo,hi=bbox(template);tl,th=bbox(target)
 def slot_points(ob, slots):
  return [ob.matrix_world@v.co for p in ob.data.polygons if p.material_index in slots for v in (ob.data.vertices[i] for i in p.vertices)]
 tp=slot_points(template,{0,7});eye=slot_points(template,{1})
 if not tp or not eye:raise RuntimeError('Face42 template lacks measured skin/eye landmarks')
 dchin=min(p.z for p in tp);dfore=max(p.z for p in tp);deye=sum(p.z for p in eye)/len(eye);dx0=min(p.x for p in tp);dx1=max(p.x for p in tp);dy=min(p.y for p in tp)
 # Root's source probe records the warm-skin landmarks in this exact Stage1 world frame.
 schin,seye,sfore=1.410,1.510,1.626; sx0,sx1=-.1336,.1264; sy=-.123043
 sz=(sfore-schin)/(dfore-dchin); oz=schin-dchin*sz
 sx=(sx1-sx0)/(dx1-dx0); ox=sx0-dx0*sx
 sy_scale=.92; oy=sy-dy*sy_scale
 scale=Vector((sx,sy_scale,sz))
 out=template.copy();out.data=template.data.copy();out.name='MIA_FACE_SKIN_PRODUCTION_TEMPLATE';c.objects.link(out)
 for v in out.data.vertices:v.co.x=v.co.x*scale.x+ox;v.co.y=v.co.y*scale.y+oy;v.co.z=v.co.z*scale.z+oz
 # Keep skin slots only; eye pieces become explicit separate Mia objects below.
 keep={0,7};ids=[p.index for p in out.data.polygons if p.material_index in keep]
 skinob=split_by_material(out,ids,c,'MIA_FACE_SKIN_PRODUCTION',skin)
 bpy.data.objects.remove(out,do_unlink=True)
 mod=skinob.modifiers.new('Fit to actual Pixal facial target','SHRINKWRAP');mod.target=target;mod.wrap_method='NEAREST_SURFACEPOINT';mod.offset=-.0007
 bpy.context.view_layer.objects.active=skinob;skinob.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);skinob.select_set(False)
 skinob['role']='Face42 loop template fitted by bbox landmarks and shrinkwrap to actual Pixal face target; keys were not transferred';skinob['fit_target']=target.name;skinob['retained_material_source_indices']=sorted(keep)
 b=skinob.shape_key_add(name='Basis');jaw=skinob.shape_key_add(name='MIA_Jaw_Open');ann=skinob.shape_key_add(name='MIA_Annoyed');smile=skinob.shape_key_add(name='MIA_Crooked_Smile')
 counts={k:0 for k in ['jaw','annoyed','smile']}
 for i,p in enumerate(b.data):
  q=skinob.matrix_world@p.co
  if q.z<1.50:jaw.data[i].co.z-=.014;counts['jaw']+=1
  if 1.53<q.z<1.64:ann.data[i].co.z-=.003;counts['annoyed']+=1
  if 1.46<q.z<1.51 and abs(q.x)<.08:smile.data[i].co.z+=(.005 if q.x>0 else -.001);counts['smile']+=1
 centers={}
 for side in (-1,1):
  points=[p for p in eye if p.x*side>0];centers[side]=(sum(p.x*sx+ox for p in points)/len(points),sum(p.z*sz+oz for p in points)/len(points))
 return skinob,counts,{'template_bbox':[list(lo),list(hi)],'target_bbox':[list(tl),list(th)],'fit_method':'template measured landmarks -> recorded Pixal warm-skin landmarks -> shrinkwrap warm-skin target','donor_landmarks':{'chin':dchin,'eye_center':deye,'forehead':dfore,'x_span':[dx0,dx1],'front_y':dy},'pixal_landmarks':{'chin':schin,'eye_center':seye,'forehead':sfore,'x_span':[sx0,sx1],'front_y':sy},'derived_eye_centers':centers,'scale':list(scale),'z_eye_before_shrinkwrap':deye*sz+oz}
def ellipse(c,n,side,kind,m,rx,rz,y):
 cx,cz=EYE_CENTERS[side];vs=[(cx,y,cz)];fs=[];N=32
 for i in range(N):
  t=math.tau*i/N;x=cx+rx*math.cos(t);z=cz+rz*math.sin(t);vs.append((x,y-.006*max(0,1-((x-cx)/rx)**2-((z-cz)/rz)**2),z))
 for i in range(N):fs.append((0,i+1,(i+1)%N+1))
 o=obj(c,n,vs,fs,m);o['role']=kind;b=o.shape_key_add(name='Basis')
 for name,dx,dz in [('Gaze_Left',-.010,0),('Gaze_Right',.010,0),('Gaze_Up',0,.007),('Gaze_Down',0,-.007)]:
  k=o.shape_key_add(name=name)
  for p in k.data:p.co.x+=dx;p.co.z+=dz
 return o
def lid(c,n,side,upper,m):
 cx,cz=EYE_CENTERS[side];rx=.064;rz=.026;N=30;vs=[];fs=[]
 for row,off in enumerate((-.003,.003)):
  for i in range(N):
   t=math.pi-math.pi*i/(N-1) if upper else math.pi+math.pi*i/(N-1);x=cx+rx*math.cos(t);z=cz+rz*math.sin(t)+off*(1 if upper else -1);y=-.132-.006*max(0,1-(x-cx)**2/rx**2)
   vs.append((x,y,z))
 for i in range(N-1):fs.append((i,i+1,N+i+1,N+i))
 o=obj(c,n,vs,fs,m);o['role']='upper/lower eyelid ribbon with contiguous edge loops';o['travel_surface']='MIA_EYE_WHITE shallow ellipsoid front surface'
 b=o.shape_key_add(name='Basis');h=o.shape_key_add(name='MIA_Blink_Half');cl=o.shape_key_add(name='MIA_Blink_Closed')
 for i,p in enumerate(b.data):h.data[i].co.z+=(-.014 if upper else .014);h.data[i].co.y-=.003;cl.data[i].co.z+=(-.028 if upper else .028);cl.data[i].co.y-=.005
 return o
def brow(c,n,side,m):
 cx,ecz=EYE_CENTERS[side];N=14;vs=[];fs=[]
 for r,off in enumerate((-.003,.003)):
  for i in range(N):u=i/(N-1);vs.append((cx-.06+.12*u,-.136,ecz+.053-.008*(2*u-1)**2+off))
 for i in range(N-1):fs.append((i,i+1,N+i+1,N+i))
 o=obj(c,n,vs,fs,m);o['role']='separate brow loop';b=o.shape_key_add(name='Basis');a=o.shape_key_add(name='MIA_Brow_Annoyed')
 for i,p in enumerate(b.data):a.data[i].co.z-=.008*max(0,1-abs(p.co.x-cx)/.06)
 return o
def mouth(c,dark,lip):
 cx=.004;cz=1.470;rx=.052;rz=.010;N=28;vs=[(cx,-.121,cz)];fs=[]
 for i in range(N):t=math.tau*i/N;vs.append((cx+rx*math.cos(t),-.132,cz+rz*math.sin(t)))
 for i in range(N):fs.append((0,i+1,(i+1)%N+1))
 cav=obj(c,'MIA_MOUTH_CAVITY',vs,fs,dark);cav['role']='separate cavity';b=cav.shape_key_add(name='Basis');o=cav.shape_key_add(name='MIA_Mouth_Open');s=cav.shape_key_add(name='MIA_Crooked_Smile')
 for i,p in enumerate(b.data):o.data[i].co.z=cz+(p.co.z-cz)*2.7;s.data[i].co.z+=.006 if p.co.x>cx else -.001
 vs=[];fs=[]
 for r,sc in enumerate((1.1,.9)):
  for i in range(N):t=math.tau*i/N;vs.append((cx+rx*sc*math.cos(t),-.134,cz+rz*sc*math.sin(t)))
 for i in range(N):fs.append((i,(i+1)%N,N+(i+1)%N,N+i))
 loop=obj(c,'MIA_MOUTH_LIP_LOOP',vs,fs,lip);loop['role']='concentric mouth deformation loop';b=loop.shape_key_add(name='Basis');o=loop.shape_key_add(name='MIA_Mouth_Open');s=loop.shape_key_add(name='MIA_Crooked_Smile')
 for i,p in enumerate(b.data):o.data[i].co.z=cz+(p.co.z-cz)*2;s.data[i].co.z+=.006 if p.co.x>cx else -.001
 return cav,loop
def pose(obs,gaze='Center',blink='Neutral',expr='Neutral',single=None):
 for o in obs:
  if not getattr(o.data,'shape_keys',None):continue
  for k in o.data.shape_keys.key_blocks:k.value=0
  ks=o.data.shape_keys.key_blocks
  if gaze in ks:ks[gaze].value=1
  if blink=='Half' and 'MIA_Blink_Half' in ks:ks['MIA_Blink_Half'].value=1
  if blink=='Closed' and 'MIA_Blink_Closed' in ks:ks['MIA_Blink_Closed'].value=1
  if expr=='Annoyed' and 'MIA_Annoyed' in ks:ks['MIA_Annoyed'].value=1
  if expr=='Annoyed' and 'MIA_Brow_Annoyed' in ks:ks['MIA_Brow_Annoyed'].value=1
  if expr=='Smile' and 'MIA_Crooked_Smile' in ks:ks['MIA_Crooked_Smile'].value=1
  if expr=='Open' and 'MIA_Mouth_Open' in ks:ks['MIA_Mouth_Open'].value=1
  if expr=='Open' and 'MIA_Jaw_Open' in ks:ks['MIA_Jaw_Open'].value=1
 if single:next(o for o in obs if o.name==single).data.shape_keys.key_blocks['MIA_Blink_Closed'].value=1
def render(s,cam,out,n,yaw=0,clay=False,wire=False):
 t=Vector((.005,-.06,1.55));r=math.radians(yaw);cam.location=t+Vector((.84*math.sin(r),-.84*math.cos(r),.025));aim(cam,t);cam.data.type='ORTHO';cam.data.ortho_scale=.52
 old=s.view_layers[0].material_override
 if clay or wire:oldmat=mat('TEMP_'+n,(.43,.44,.46) if clay else (.08,.09,.1));s.view_layers[0].material_override=oldmat
 for o in s.objects:
  if o.type=='MESH':o.show_wire=wire;o.show_all_edges=wire
 s.render.filepath=str(out/(n+('_wire' if wire else '_clay' if clay else '')+'.png'));bpy.ops.render.render(write_still=True);s.view_layers[0].material_override=old
 for o in s.objects:
  if o.type=='MESH':o.show_wire=o.show_all_edges=False
def main():
 a=cli();inp=Path(a.input).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True);before=sha(inp);bpy.ops.wm.open_mainfile(filepath=str(inp));s=bpy.context.scene;s.name='Mia_Stage2_FaceExpression_v01';s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 vis=col('MIA_STAGE2_FACE_VISIBLE');arc=col('MIA_STAGE2_ARCHIVE');ctl=col('MIA_STAGE2_CONTROLS');src=bpy.data.objects.get('SINGLE_HEAD_MIXED_REVIEW');template=bpy.data.objects.get('Mia_Face_AnimeTopology') or bpy.data.objects.get('Face')
 if not src or not template:raise RuntimeError('Stage1 mixed source or Face42 topology reference missing')
 old={n:sig(bpy.data.objects[n]) for n in ['SINGLE_HEAD_MIXED_REVIEW','SINGLE_HAIR_MIXED_REVIEW','FULL_SKIN_MIXED_REVIEW','FULL_PANTS_MIXED_REVIEW','FULL_SHOES_MIXED_REVIEW'] if bpy.data.objects.get(n)}
 # Retain the full source in view so every bang stays exactly where Pixal made it.
 # Only a warm-skin copy is hidden and used as a fitting target for the new face.
 skinids=[p.index for p in src.data.polygons if source_is_skin(src,p)]
 if len(skinids)<100:raise RuntimeError('Could not establish a warm-skin Pixal fitting target')
 target=split_by_material(src,skinids,arc,'MIA_PIXAL_WARM_SKIN_TARGET_HIDDEN',None);target.hide_render=target.hide_viewport=True
 hair=bpy.data.objects.get('SINGLE_HAIR_MIXED_REVIEW')
 src['stage2_disposition']='visible source retained for all hair; hidden warm-skin target used only for fit; no polygons deleted'
 skin=mat('MIA_SKIN',(0.68,.54,.52));white=mat('MIA_EYE_WHITE',(.78,.80,.79));iris=mat('MIA_IRIS_GRAY',(.30,.40,.42));pupil=mat('MIA_PUPIL',(.018,.022,.027));liner=mat('MIA_LINER',(.035,.026,.03));browm=mat('MIA_BROW',(.10,.085,.09));lip=mat('MIA_LIP',(.30,.16,.17));mouthm=mat('MIA_MOUTH',(.045,.018,.025))
 face,changed,fit=fit_face_template(template,target,skin,vis)
 for key,value in fit['derived_eye_centers'].items():EYE_CENTERS[int(key)]=tuple(value)
 obs=[face,hair]
 for side,label in [(-1,'L'),(1,'R')]:
  obs+=[ellipse(vis,'MIA_EYE_WHITE_'+label,side,'separate eye white',white,.061,.026,-.125),ellipse(vis,'MIA_IRIS_'+label,side,'separate iris',iris,.023,.020,-.129),ellipse(vis,'MIA_PUPIL_'+label,side,'separate pupil',pupil,.010,.014,-.131),lid(vis,'MIA_LID_UPPER_'+label,side,True,liner),lid(vis,'MIA_LID_LOWER_'+label,side,False,liner),brow(vis,'MIA_BROW_'+label,side,browm)]
 cav,loop=mouth(vis,mouthm,lip);obs += [cav,loop]
 bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='MIA_STAGE2_FACE_CAMERA';cam.data.type='ORTHO';s.camera=cam
 for oldc in list(cam.users_collection):oldc.objects.unlink(cam)
 ctl.objects.link(cam)
 for loc,en in [((-2,-3,4),700),((2,-3,2),380),((1,2,3),350)]:
  bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.data.energy=en;L.data.shape='DISK';L.data.size=2.5;aim(L,(0,0,1.5))
  for oldc in list(L.users_collection):oldc.objects.unlink(L)
  ctl.objects.link(L)
 # inexpensive neutral review first; full state set follows in the same saved checkpoint.
 pose(obs);render(s,cam,out,'neutral_front');render(s,cam,out,'neutral_side',90);render(s,cam,out,'neutral_threequarter_right',45);render(s,cam,out,'neutral_threequarter_left',315);render(s,cam,out,'neutral_front',0,True);render(s,cam,out,'neutral_threequarter_right',45,True,True)
 if not a.draft:
  for blink in ['Neutral','Half','Closed']:
   for gaze in ['Center','Gaze_Left','Gaze_Right','Gaze_Up','Gaze_Down']:pose(obs,gaze,blink);render(s,cam,out,'eyes_'+blink.lower()+'_'+gaze.lower())
  for e in ['Annoyed','Smile','Open']:
   pose(obs,'Center','Neutral',e);render(s,cam,out,'expression_'+e.lower()+'_front');render(s,cam,out,'expression_'+e.lower()+'_threequarter',45)
  pose(obs,single='MIA_LID_UPPER_L');render(s,cam,out,'eyes_independent_left_closed');pose(obs,single='MIA_LID_UPPER_R');render(s,cam,out,'eyes_independent_right_closed');pose(obs)
 rows=[]
 for o in obs:
  ks={}
  if getattr(o.data,'shape_keys',None):
   b=o.data.shape_keys.key_blocks[0]
   for k in o.data.shape_keys.key_blocks[1:]:ks[k.name]=sum((p.co-q.co).length>1e-7 for p,q in zip(b.data,k.data))
  rows.append({'name':o.name,'role':o.get('role',''),'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'shape_key_nonzero_vertices':ks})
 after=sha(inp);now={n:sig(bpy.data.objects[n]) for n in old}
 report={'status':'STAGE2_FACE_EXPRESSION_CHECKPOINT; ART_NOTAPPROVED; FULL_CHARACTER_RIG_AND_EVENTS_INCOMPLETE','input_sha256_before':before,'input_sha256_after':after,'input_unchanged':before==after,'face_fit':fit,'skin_shape_delta_counts':changed,'source_partition':{'warm_skin_target_faces':len(skinids),'policy':'full mixed source retained visible for all bangs; hidden warm-skin target is a fitting reference only; no source polygons deleted'},'parts':rows,'stage1_meshes_unchanged':old==now,'renders':sorted(p.name for p in out.glob('*.png')),'limitations':['visual/art approval remains human gate','Face42 topology template was fitted; its original keys were not transferred','no final armature, weights, collision, sprite events or final texture']}
 (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'Mia_Stage2_FaceExpression_v01.blend'),check_existing=False);print('SAVED',out/'Mia_Stage2_FaceExpression_v01.blend')
if __name__=='__main__':main()
