"""Four ray-selected terminal clusters; keep a367 immutable and preserve source UV/IDs."""
import bpy,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;SRC=OUT.parent/'Mia_HairCorrection_v20.blend';BASE=OUT.parents[1]/'mia-body-correction-v20/Mia_BodyCorrection_v20.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p):sha(p) for p in [SRC,BASE]};spec=json.loads((OUT/'tip-inspection.json').read_text());groups={g['id']:g for g in spec['groups']}
bpy.ops.wm.open_mainfile(filepath=str(BASE));baseline=[v.co.copy() for v in bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(SRC));o=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=o.data;s=bpy.context.scene;cam=s.camera

def sig(o):
 data=b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<2f',*v.uv) for l in o.data.uv_layers for v in l.data)
 if o.data.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in o.data.shape_keys.key_blocks for v in k.data)
 return hashlib.sha256(data).hexdigest()
protected={ob.name:sig(ob) for ob in bpy.data.objects if ob.type=='MESH' and ob!=o};uvhash=lambda:hashlib.sha256(b''.join(struct.pack('<2f',*v.uv) for l in m.uv_layers for v in l.data)).hexdigest();uvbefore=uvhash();sourceids=[v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data];original=[v.co.copy() for v in m.vertices];packed={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file}
def views(prefix):
 s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;cam.data.ortho_scale=.52;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 for name,loc in [('profile',(2,0,1.475)),('back',(0,2,1.475))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
views('before')
# Undo our previous tiny UV-seam-incoherent polish. This exact baseline is the same
# 122129-face mesh before that pass; it is not a different source/shape rebuild.
restored=[]
for i,v in enumerate(m.vertices):
 if (v.co-baseline[i]).length>1e-9:v.co=baseline[i];restored.append(i)
# Chosen by visible defect rays/source polygons, not all lower hair and not33oldgroups.
settings={3:(.045,.011,.007,-.004),11:(.043,.010,.006,-.010),19:(.046,.008,.005,-.008),54:(.042,.009,.004,-.003)};selected=set();reports=[]
for gid,(length,inward,backbend,extend) in settings.items():
 g=groups[gid];ids=g['verts'];lo=min(baseline[i].z for i in ids);end=[baseline[i] for i in ids if baseline[i].z<lo+.012];center=sum(end,Vector())/len(end);sgn=1 if center.x>0 else -1;root=lo+length
 for i in ids:
  q=baseline[i].copy();t=max(0,min(1,(root-q.z)/length));fade=t*t*(3-2*t)
  if not t:continue
  # Distal cross-section rounding + curved centerline; attachment/root remains exact.
  q.x=center.x+(q.x-center.x)*(1-.48*fade)-sgn*inward*fade
  q.y=center.y+(q.y-center.y)*(1-.32*fade)+backbend*math.sin(math.pi*t*.65)*fade
  q.z+=extend*fade+.0025*math.sin((baseline[i].x-center.x)*95)*fade
  m.vertices[i].co=q;selected.add(i)
 reports.append({'group':gid,'source_polygon_count':len(g['sourcepolys']),'source_polygons':g['sourcepolys'],'distal_root_z':root,'center':list(center),'end_center_shift_xyz':[-sgn*inward,backbend,extend]})
# One separately ray-identified22-face horizontal frayed strip: taper along its
# own outwardX axis, not a head-height cut. Retain the flyaway and all its faces.
small=json.loads((OUT/'small-tip-inspection.json').read_text());flap=next(g for g in small['groups'] if 197394 in g['sourcepolys'])
for i in flap['verts']:
 q=baseline[i].copy();t=max(0,min(1,(q.x-.180)/.045));fade=t*t*(3-2*t);center_y=.046-.010*t
 q.y=center_y+(q.y-center_y)*(1-.84*fade);q.z+=.007*fade;m.vertices[i].co=q;selected.add(i)
reports.append({'group':'ray197394_horizontal_flyaway','source_polygon_count':len(flap['sourcepolys']),'source_polygons':flap['sourcepolys'],'action':'Own longitudinalX taper and7mm upwardcurve; no deletion'})
# Raw-atlas inspection confirms these are torn strand-cap fragments, not a
# cloth panel. Their semantic lock is the lateral11clump, but extraction left
# disconnected islands. Carry the ray-selected islands with that same curve.
cap=json.loads((OUT/'frayed-cap-selection.json').read_text());cap_groups=[g for g in cap['groups'] if len(g['polys'])<200]
parent=groups[11];lo=min(baseline[i].z for i in parent['verts']);length=.043;root=lo+length;pts=[baseline[i] for i in parent['verts'] if baseline[i].z<lo+.012];center=sum(pts,Vector())/len(pts)
for g in cap_groups:
 for i in g['verts']:
  q=baseline[i].copy();t=max(0,min(1,(root-q.z)/length));fade=t*t*(3-2*t)
  q.x=center.x+(q.x-center.x)*(1-.65*fade)-.010*fade
  q.y=center.y+(q.y-center.y)*(1-.72*fade)+.006*math.sin(math.pi*t*.65)*fade
  q.z+=-.010*fade+.0025*math.sin((baseline[i].x-center.x)*95)*fade
  m.vertices[i].co=q;selected.add(i)
 reports.append({'group':'ray_selected_frayed_cap_'+str(g['id']),'source_polygon_count':len(g['sourcepolys']),'source_polygons':g['sourcepolys'],'action':'Follow lateral11tip curvature with tighter distal width; entire component retained'})
# Geometrically coincident UV seam copies receive exactly the same final coordinate.
buckets={}
for i,q in enumerate(baseline):buckets.setdefault(tuple(round(a,5) for a in q),[]).append(i)
seam_fixes=0
for ids in buckets.values():
 if len(ids)>1 and any(i in selected for i in ids):
  changed=[m.vertices[i].co for i in ids if i in selected];mean=sum(changed,Vector())/len(changed)
  for i in ids:m.vertices[i].co=mean;selected.add(i)
  seam_fixes+=1
m.update();assert uvhash()==uvbefore;assert sourceids==[v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data];assert all(sig(bpy.data.objects[k])==v for k,v in protected.items())
for im in bpy.data.images:
 if im.packed_file:im.use_fake_user=True
DST=OUT/'Mia_HairTailCandidate_v20.blend';cam.location=(0,-2,1.475);cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));s=bpy.context.scene;cam=s.camera;o=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=o.data;assert all(sig(bpy.data.objects[k])==v for k,v in protected.items());assert uvhash()==uvbefore;assert sourceids==[v.value for v in m.attributes['MIA_SOURCE_POLYGON'].data];assert packed=={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file};views('after');assert all(sha(Path(p))==h for p,h in hashes.items())
r={'source_hashes_unchanged':hashes,'native_sha256':sha(DST),'recipe_sha256':sha(Path(__file__)),'selected_terminal_regions':reports,'restored_previous_incoherent_polish_vertices':len(restored),'terminal_sculpt_vertices':len(selected),'UV_seam_groups_coherent':seam_fixes,'main_faces':len(m.polygons),'bothUV_exact':uvbefore,'sourceIDs_exact':True,'all_other_meshes_UV_keys_exact':len(protected),'packed_images_exact':len(packed),'status':'Candidate, actual profile/back review required; not automatically accepted'};(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE',r['native_sha256'])
