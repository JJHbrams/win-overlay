"""Shared fixed source-view review setup; no scene save here."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay')
CANON=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay')
SOURCE=CANON/'asset/mia/blender/mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend'
OUT=Path(__file__).resolve().parent
REF=CANON/'asset/mia/references'
VIEWS=[
 dict(id='front',reference=str(REF/'received/mia-face-reaffirmed-20261031.png'),crop=[340,220,700,490],anchors=[[515.5,312.5],[519,463]],yaw=0,elevation=0,roll=-6.6,uncertainty='Portrait near-front: yaw +/-6, pitch +/-6, roll +/-3 degrees. Eye midpoint/pupil estimate +/-2 pixels; hair covers temple. Eye-to-chin normalization cannot prove face height.'),
 dict(id='profile',reference=str(REF/'mia-clean-master-v22.png'),crop=[525,48,605,120],anchors=[[558,70],[553,107]],yaw=80,elevation=0,roll=0,uncertainty='Small drawn SIDE panel: estimated yaw70..90, pitch +/-6, visible eye is stylized and not a calibrated anatomical center. Anchors +/-2 original pixels. Forehead/bridge partially hair-occluded. Compare silhouette and lip/nose shape, not exact depth from iris alone.'),
 dict(id='left_oblique',reference=str(REF/'mia-expression-style-confirmed-20261031.png'),crop=[1230,45,1405,180],anchors=[[1305.5,91.5],[1321,157]],yaw=25,elevation=2,roll=-15,uncertainty='Expression04: image-left facing, yaw15..35, pitch +/-8, roll-15 +/-7. Sideways eye gaze differs from neutral; pupil centers approximate orbital anchors. Mouth neutral-ish; far outline partially occluded.'),
 dict(id='right_oblique',reference=str(REF/'mia-expression-style-confirmed-20261031.png'),crop=[850,45,1030,180],anchors=[[948,99.5],[960,166]],yaw=-10,elevation=-3,roll=-15,uncertainty='Expression03 is the closest near-front opposite subtle-angle evidence, not a confirmed -45 view: yaw estimated -15..+5, pitch -8..+5, roll-15 +/-7. Upward gaze/open mouth differ from neutral. Do not infer exact opposing temple depth or closed-mouth likeness from this panel.')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def artifact(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def aim(o,loc,target):o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def hairhide():
 members={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and (o.name in members or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):o.hide_render=True
def camera(s,v):
 yaw=math.radians(v['yaw']);el=math.radians(v['elevation']);target=Vector((0,0,1.55));loc=target+Vector((2*math.sin(yaw)*math.cos(el),-2*math.cos(yaw)*math.cos(el),2*math.sin(el)))
 aim(s.camera,loc,target);s.camera.rotation_mode='QUATERNION';s.camera.rotation_quaternion=s.camera.rotation_euler.to_quaternion()@Quaternion((0,0,1),math.radians(v['roll']))
 s.camera.data.type='ORTHO';s.camera.data.ortho_scale=.29;s.camera.data.shift_x=s.camera.data.shift_y=0
 s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.film_transparent=True
 bpy.context.view_layer.update()
def landmarks(s,v):
 eye=bpy.data.objects['MIA_V14_EyeSurface'];ids={i for p in eye.data.polygons if p.material_index==5 for i in p.vertices};groups=[[eye.matrix_world@eye.data.vertices[i].co for i in ids if (eye.matrix_world@eye.data.vertices[i].co).x*sign>0] for sign in [-1,1]]
 centers=[sum(g,Vector())/len(g) for g in groups];a=centers[1] if v['id']=='profile' else sum(centers,Vector())/2
 skin=bpy.data.objects['MIA_V14_SculptedSkin'];ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ev.matrix_world@x.co for x in me.vertices];chin=min([p for p in pts if abs(p.x)<.008 and p.y<-.025],key=lambda p:p.z);ev.to_mesh_clear()
 def pix(p):q=world_to_camera_view(s,s.camera,p);return [q.x*1000,(1-q.y)*1000]
 return {'anchor_pixels':[pix(a),pix(chin)],'anchor_world':[list(a),list(chin)],'definition':'Mean curved iris carrier center(s), not a fitted gaze pupil; actual evaluated central chin minimumZ. Same definition before/after.'}
def record(s,v,mode):
 lights=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'hidden':o.hide_render} for o in s.objects if o.type=='LIGHT']
 return {'projection':'ORTHO','ortho_scale':.29,'matrix':[list(r) for r in s.camera.matrix_world],'yaw':v['yaw'],'elevation':v['elevation'],'image_roll':v['roll'],'frame':s.frame_current,'active_shape_keys':{k.name:k.value for k in bpy.data.objects['MIA_V14_SculptedSkin'].data.shape_keys.key_blocks if k.value},'lighting':{'mode':mode,'lights':lights,'world':s.world.name if s.world else None,'production_skin':'Fixed normal-direction ramp to emission; scene lamps are not the skin shading controller'},'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'resolution':[1000,1000],'pixel_aspect':[1,1],'lens_shift':[0,0]}
def renders(path,folder):
 folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()));s=bpy.context.scene;s.frame_set(1);hairhide();records={}
 for v in VIEWS:
  camera(s,v);s.render.filepath=str(folder/(v['id']+'.png'));bpy.ops.render.render(write_still=True);records[v['id']]={'camera':record(s,v,'Source production toon, same inherited color management'),'landmarks':landmarks(s,v)}
 (folder/'render-records.json').write_text(json.dumps(records,indent=2));return records
