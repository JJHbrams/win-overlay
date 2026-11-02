"""Scoped hair-library replay. Importable in an already-open Blender target.

This transports an explicitly selected WIP; it does not grant an art PASS.
Only baseline-visible hair and the bundle's new actors are mutable. Archived
donors, body/head/eyes, existing materials/images, camera, lights and world stay
untouched. The source rig is never imported.
"""
import argparse, collections, hashlib, json, sys, re, math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix, Vector

def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return [v.bl_rna.identifier,v.name]
 if hasattr(v,'bl_rna'):
  out={'rna_struct':v.bl_rna.identifier,'properties':_rna(v)}
  if v.bl_rna.identifier=='CurveMapping':out['curves']=[[(list(p.location),p.handle_type) for p in c.points] for c in v.curves]
  return out
 try:return [_plain(x) for x in v]
 except TypeError:return re.sub(r'0x[0-9A-Fa-f]+','<runtime-address>',str(v))

def _digest(v):
 return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def mesh_signature(ob):
 m=ob.data;h=hashlib.sha256();h.update(np.asarray([v.co[:] for v in m.vertices],dtype='<f4').tobytes())
 h.update(np.asarray([f.loop_total for f in m.polygons],dtype='<i4').tobytes());h.update(np.asarray([l.vertex_index for l in m.loops],dtype='<i4').tobytes())
 h.update(np.asarray([(f.material_index,int(f.use_smooth)) for f in m.polygons],dtype='<i4').tobytes())
 for u in m.uv_layers:h.update(u.name.encode());h.update(np.asarray([v.uv[:] for v in u.data],dtype='<f4').tobytes())
 if m.shape_keys:
  for k in m.shape_keys.key_blocks:h.update(k.name.encode());h.update(np.asarray([v.co[:] for v in k.data],dtype='<f4').tobytes())
 return h.hexdigest()

def uv_state(ob):
 return {'active_index':ob.data.uv_layers.active_index,'layers':[[u.name,u.active_render,u.active_clone] for u in ob.data.uv_layers]}

def group_state(ob):
 weights=[[] for _ in ob.vertex_groups]
 for v in ob.data.vertices:
  for g in v.groups:weights[g.group].append([v.index,g.weight])
 return [{'name':g.name,'weights':weights[g.index]} for g in ob.vertex_groups]

def _rna(obj,skip=()):
 out={}
 for p in obj.bl_rna.properties:
  if p.identifier in {'rna_type','id_data','users','use_fake_user','is_updated','is_updated_data','execution_time','runtime','preview','session_uid',*skip} or p.type=='COLLECTION':continue
  try:out[p.identifier]=_plain(getattr(obj,p.identifier))
  except (AttributeError,TypeError,ValueError,RuntimeError):pass
 return out

def tree_state(tree,seen=None):
 if tree is None:return None
 seen=set() if seen is None else seen
 if tree.as_pointer() in seen:return ['recursive',tree.name]
 seen.add(tree.as_pointer());nodes=[]
 for n in sorted(tree.nodes,key=lambda x:x.name):
  row={'name':n.name,'type':n.bl_idname,'properties':_rna(n,{'inputs','outputs','internal_links','parent','node_tree','image','color_ramp'}),'inputs':[(s.identifier,_plain(getattr(s,'default_value',None))) for s in n.inputs],'outputs':[(s.identifier,_plain(getattr(s,'default_value',None))) for s in n.outputs]}
  if getattr(n,'image',None):row['image']=[n.image.name,n.image.colorspace_settings.name]
  if getattr(n,'node_tree',None):row['group']=tree_state(n.node_tree,seen.copy())
  if getattr(n,'color_ramp',None):row['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in n.color_ramp.elements]}
  nodes.append(row)
 return {'nodes':nodes,'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links)}

def material_signature(mat):
 return _digest({'properties':_rna(mat,{'node_tree','preview','animation_data'}),'nodes':tree_state(mat.node_tree) if mat.use_nodes else None})

def nonhair_snapshot(mutable_names):
 """Hashes existing actors, all shape coordinates/values, and their graphs."""
 objects={};materials={};images={}
 for ob in bpy.context.scene.objects:
  if ob.name in mutable_names:continue
  row={'type':ob.type,'matrix':_plain(ob.matrix_world),'render':ob.hide_render,'viewport':ob.hide_get(),'parent':ob.parent.name if ob.parent else None,'parent_type':ob.parent_type,'parent_bone':ob.parent_bone,'constraints':[_rna(c) for c in ob.constraints],'modifiers':[_rna(m) for m in ob.modifiers]}
  if ob.type=='MESH':
   row['mesh']=mesh_signature(ob);row['slots']=[m.name if m else None for m in ob.data.materials]
   row['vertex_groups']=_digest({'names':[g.name for g in ob.vertex_groups],'weights':[[(g.group,g.weight) for g in v.groups] for v in ob.data.vertices]})
   if ob.data.shape_keys:row['keys']=[(k.name,k.value,k.mute,k.vertex_group,k.relative_key.name) for k in ob.data.shape_keys.key_blocks]
   for m in ob.data.materials:
    if m and m.name not in materials:materials[m.name]=material_signature(m)
  elif ob.type=='ARMATURE':row['pose']={b.name:_plain(b.matrix_basis) for b in ob.pose.bones}
  elif ob.type in {'LIGHT','CAMERA'}:row['data']=_rna(ob.data,{'preview','animation_data'})
  objects[ob.name]=_digest(row)
 # Existing images are never edited by replay; include packed bytes, spaces
 # and reference metadata, without decoding millions of pixels.
 for im in bpy.data.images:
  try:packed=hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None
  except (RuntimeError,TypeError):packed=None
  images[im.name]=_digest([im.source,im.filepath,im.colorspace_settings.name,list(im.size),packed])
 sc=bpy.context.scene;w=sc.world
 return {'objects':objects,'materials':materials,'images':images,'world':_digest({'name':w.name if w else None,'props':_rna(w,{'node_tree','preview','animation_data'}) if w else None,'nodes':tree_state(w.node_tree) if w and w.use_nodes else None}),'scene':_digest({'camera':sc.camera.name if sc.camera else None,'frame':sc.frame_current,'view_settings':_rna(sc.view_settings),'render':_rna(sc.render,{'image_settings','ffmpeg','bake','views','stereo_views'}),'image_settings':_rna(sc.render.image_settings),'engine':sc.render.engine})}

def verify_preserved(before,after):
 delta={}
 for category in ['objects','materials','images']:
  changed=[name for name,h in before[category].items() if after[category].get(name)!=h]
  if changed:delta[category]=changed
 for category in ['world','scene']:
  if before[category]!=after[category]:delta[category]=True
 return delta

def _restore_groups(ob,groups):
 ob.vertex_groups.clear()
 for r in groups:
  g=ob.vertex_groups.new(name=r['name'])
  byweight=collections.defaultdict(list)
  for vi,w in r['weights']:byweight[float(w)].append(int(vi))
  for w,ids in byweight.items():g.add(ids,w,'REPLACE')

def bind_rigid_head(ob,rig,bone='J_Bip_C_Head'):
 world=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone=bone;bpy.context.view_layer.update();ob.matrix_world=world;bpy.context.view_layer.update()
 error=float(np.max(np.abs(np.asarray(ob.matrix_world)-np.asarray(world))))
 if error>2e-6:raise RuntimeError('Head attachment changed world transform: '+ob.name+' '+str(error))
 return error

def diagnose_head_follow(hair_objects,rig,head_name='MIA_V27_SharedHeadBody',bone='J_Bip_C_Head'):
 """Two reversible CPU poses; never repair or rebind the existing head.

 Rigid-parent rest preservation is not proof that the actual character head
 is driven by that rig. Report measured evaluated head/hair motion separately.
 """
 head=bpy.data.objects.get(head_name)
 if not head or head.type!='MESH':return {'status':'missing_existing_head','head_attachment_usable':False,'nonhair_binding_modified':False}
 pb=rig.pose.bones[bone];original={k:tuple(getattr(pb,k)) for k in ['location','rotation_euler','rotation_quaternion','rotation_axis_angle','scale']};oldbasis=pb.matrix_basis.copy();oldbone=(rig.matrix_world@pb.matrix).copy()
 def evaluated_points(ob,indices=None):
  eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh()
  try:
   if indices is None:indices=np.arange(len(me.vertices),dtype=int)
   return np.asarray([eo.matrix_world@me.vertices[int(i)].co for i in indices],dtype=float)
  finally:eo.to_mesh_clear()
 bpy.context.view_layer.update();allhead=evaluated_points(head);pivot=np.array(oldbone.translation);mask=(allhead[:,2]>pivot[2]+.025)&(np.abs(allhead[:,0]-pivot[0])<.14)&(np.abs(allhead[:,1]-pivot[1])<.18);headids=np.flatnonzero(mask)
 if len(headids)>512:headids=headids[np.linspace(0,len(headids)-1,512).astype(int)]
 if not len(headids):return {'status':'no_evaluated_head_samples','head_attachment_usable':False,'nonhair_binding_modified':False}
 h0=allhead[headids];hair_samples=[]
 for ob in hair_objects:
  pts=evaluated_points(ob);ids=np.linspace(0,len(pts)-1,min(len(pts),64)).astype(int);hair_samples.append((ob,ids,pts[ids]))
 rows=[];axis=oldbone.to_3x3().inverted()@Vector((1,0,0));axis.normalize()
 try:
  for degrees in [-12.,12.]:
   pb.matrix_basis=oldbasis@Matrix.Rotation(math.radians(degrees),4,axis);bpy.context.view_layer.update();delta=(rig.matrix_world@pb.matrix)@oldbone.inverted();D=np.asarray(delta,dtype=float);h=evaluated_points(head,headids);expected=np.c_[h0,np.ones(len(h0))]@D.T;move=np.linalg.norm(h-h0,axis=1);expected_move=np.linalg.norm(expected[:,:3]-h0,axis=1);error=np.linalg.norm(h-expected[:,:3],axis=1);hair_move=[];hair_error=[]
   for ob,ids,p0 in hair_samples:
    p=evaluated_points(ob,ids);pred=np.c_[p0,np.ones(len(p0))]@D.T;hair_move.extend(np.linalg.norm(p-p0,axis=1));hair_error.extend(np.linalg.norm(p-pred[:,:3],axis=1))
   static=bool(float(move.max())<1e-6 and max(hair_move,default=0)>.001);consistent=bool(float(error.max())<.0001 and max(hair_error,default=0)<.0001 and float(expected_move.max())>.001)
   rows.append({'nod_degrees':degrees,'actual_bone_world_delta':[list(r) for r in delta],'head_sample_count':len(headids),'evaluated_head_max_move_m':float(move.max()),'evaluated_head_rms_move_m':float(np.sqrt(np.mean(move**2))),'rigid_head_expected_max_move_m':float(expected_move.max()),'head_vs_rigid_bone_max_error_m':float(error.max()),'head_vs_rigid_bone_rms_error_m':float(np.sqrt(np.mean(error**2))),'hair_max_move_m':max(hair_move,default=0),'hair_vs_rigid_bone_max_error_m':max(hair_error,default=0),'head_static_while_hair_moves':static,'consistent_rigid_head_motion':consistent})
 finally:
  for k,v in original.items():setattr(pb,k,v)
  bpy.context.view_layer.update()
 head_rest=float(np.max(np.linalg.norm(evaluated_points(head,headids)-h0,axis=1)));hair_rest=max((float(np.max(np.linalg.norm(evaluated_points(ob,ids)-p0,axis=1))) for ob,ids,p0 in hair_samples),default=0)
 if max(head_rest,hair_rest)>2e-6:raise RuntimeError('Head-follow diagnostic did not restore the evaluated rest pose')
 usable=all(r['consistent_rigid_head_motion'] for r in rows)
 return {'status':'consistent_rigid_head_motion' if usable else ('existing_head_static' if any(r['head_static_while_hair_moves'] for r in rows) else 'head_motion_mixed_or_unverified'),'head_attachment_usable':usable,'existing_head':head.name,'existing_head_modifiers':[(m.name,m.type,getattr(getattr(m,'object',None),'name',None)) for m in head.modifiers],'head_bone_use_deform':pb.bone.use_deform,'rig_pose_position':rig.data.pose_position,'poses':rows,'head_restoration_max_error_m':head_rest,'hair_restoration_max_error_m':hair_rest,'nonhair_binding_modified':False,'limits':'A CPU coupling diagnostic, not clipping, expression, animation or ART approval. If false, do not call the hair attached to the actual character head.'}

def apply_hair_bundle(manifest_path,bind_head=False,report_path=None):
 manifest_path=Path(manifest_path);cfg=json.loads(manifest_path.read_text(encoding='utf-8'));lib=manifest_path.parent/cfg['library'];bundle_sha=sha(lib)
 if bundle_sha!=cfg['library_sha256']:raise RuntimeError('Hair library hash does not match manifest')
 if not cfg.get('technical_replay_only'):raise RuntimeError('Missing transport-only provenance flag')
 baseline={r['name']:r for r in cfg['baseline_visible_hair']};active={r['name']:r for r in cfg['active_hair']};mutable=set(baseline)|set(active)
 if all((ob:=bpy.data.objects.get(name)) and ob.get('mia_v30_hair_bundle_sha256')==bundle_sha and mesh_signature(ob)==row['mesh_sha256'] for name,row in active.items()):
  before=nonhair_snapshot(mutable);errors=[];rig=bpy.data.objects.get('MIA_V06_RIG')
  if bind_head:
   if not rig or 'J_Bip_C_Head' not in rig.pose.bones:raise RuntimeError('Existing target head rig is required')
   for name in active:
    ob=bpy.data.objects[name]
    if not any(m.type=='ARMATURE' for m in ob.modifiers) and not (ob.parent==rig and ob.parent_type=='BONE' and ob.parent_bone=='J_Bip_C_Head'):errors.append(bind_rigid_head(ob,rig))
  motion=diagnose_head_follow([bpy.data.objects[n] for n in active],rig) if bind_head else None
  delta=verify_preserved(before,nonhair_snapshot(mutable))
  if delta:raise RuntimeError('Idempotent binding changed non-hair state: '+json.dumps(delta))
  report={'status':'already_applied','library_sha256':bundle_sha,'active_hair':sorted(active),'art_acceptance':False,'nonhair_preserved':True,'head_binding_requested':bind_head,'head_binding_rest_world_max_error':max(errors,default=0),'head_motion_consistency':motion}
  if report_path:Path(report_path).write_text(json.dumps(report,indent=2),encoding='utf-8')
  return report
 for name,row in baseline.items():
  ob=bpy.data.objects.get(name)
  if ob is None or ob.type!='MESH' or mesh_signature(ob)!=row['mesh_sha256']:raise RuntimeError('Baseline hair guard failed before mutation: '+name)
  if row.get('uv_state') and uv_state(ob)!=row['uv_state']:raise RuntimeError('Baseline active UV guard failed: '+name)
 for name in set(active)-set(baseline):
  if name in bpy.data.objects:raise RuntimeError('Unowned target object name collision: '+name)
 rig=bpy.data.objects.get('MIA_V06_RIG')
 if bind_head and (not rig or rig.type!='ARMATURE' or 'J_Bip_C_Head' not in rig.pose.bones):raise RuntimeError('Existing MIA_V06_RIG/J_Bip_C_Head required; importing a rig is forbidden')
 before=nonhair_snapshot(mutable);before_objects=set(bpy.data.objects);before_rigs={o.name for o in bpy.data.objects if o.type=='ARMATURE'};before_images=set(bpy.data.images);before_mats=set(bpy.data.materials)
 with bpy.data.libraries.load(str(lib),link=False) as (source,dest):
  if source.armatures or source.scenes or source.cameras or source.lights:raise RuntimeError('Hair library contains a forbidden rig/scene/camera/light')
  if set(source.objects)!=set(row['library_object'] for row in active.values()):raise RuntimeError('Hair library object set differs from manifest')
  dest.objects=[row['library_object'] for row in active.values()]
 imported={o.name:o for o in dest.objects};linked=[];rest_errors={}
 for name,row in active.items():
  inc=imported[row['library_object']];ob=bpy.data.objects.get(name)
  if ob is not None:
   olddata=ob.data;olddata.use_fake_user=True;ob.data=inc.data
   # Copy all source transport modifiers, with existing target rig references.
   ob.modifiers.clear()
   for mr in row['modifiers']:
    mod=ob.modifiers.new(mr['name'],mr['type'])
    for k,v in mr['properties'].items():
     if k in {'name','type','object'}:continue
     try:setattr(mod,k,v)
     except (AttributeError,TypeError,ValueError,RuntimeError):pass
    if mr.get('target_object'):
     if mr['target_object']!='MIA_V06_RIG' or not rig:raise RuntimeError('Unsupported modifier target '+str(mr['target_object']))
     mod.object=rig
   bpy.data.objects.remove(inc,do_unlink=True)
  else:
   ob=inc;ob.name=name;collection=next((bpy.data.collections.get(n) for n in row['collections'] if bpy.data.collections.get(n)),None) or bpy.context.scene.collection;collection.objects.link(ob);linked.append(name)
  _restore_groups(ob,row['vertex_groups']);ob.parent=None;ob.parent_type='OBJECT';ob.matrix_world=Matrix(row['matrix_world']);ob.hide_render=False;ob.hide_viewport=row.get('hide_viewport',False);ob.hide_set(row.get('hide_set',False));ob['mia_v30_hair_bundle_sha256']=bundle_sha;ob['mia_v30_hair_source_owner']=name
  # Unbound transport objects must never retain any imported parent/rig.
  for mod in ob.modifiers:
   if mod.type=='ARMATURE':mod.object=rig
  if bind_head and not any(m.type=='ARMATURE' for m in ob.modifiers):rest_errors[name]=bind_rigid_head(ob,rig)
  if mesh_signature(ob)!=row['mesh_sha256']:raise RuntimeError('Replayed mesh/UV/key mismatch: '+name)
  if row.get('uv_state') and uv_state(ob)!=row['uv_state']:raise RuntimeError('Replayed active UV mismatch: '+name)
  if _digest(group_state(ob))!=_digest(row['vertex_groups']):raise RuntimeError('Replayed semantic weights mismatch: '+name)
 for row in cfg['hidden_replaced_hair']:
  ob=bpy.data.objects[row['name']];ob.hide_render=True;ob.hide_set(True)
 bpy.context.view_layer.update();motion=diagnose_head_follow([bpy.data.objects[n] for n in active],rig) if bind_head else None;after=nonhair_snapshot(mutable);delta=verify_preserved(before,after)
 new_rigs={o.name for o in bpy.data.objects if o.type=='ARMATURE'}-before_rigs
 if new_rigs:delta['imported_rigs']=sorted(new_rigs)
 if delta:raise RuntimeError('Non-hair preservation failure: '+json.dumps(delta,ensure_ascii=False))
 report={'status':'applied','technical_replay_only':True,'art_acceptance':False,'source_native':cfg['source_native'],'source_sha256':cfg['source_sha256'],'library':str(lib),'library_sha256':bundle_sha,'active_hair':sorted(active),'hidden_replaced_hair':[r['name'] for r in cfg['hidden_replaced_hair']],'new_linked_objects':linked,'imported_images':sorted(im.name for im in set(bpy.data.images)-before_images),'imported_materials':sorted(m.name for m in set(bpy.data.materials)-before_mats),'existing_nonhair_objects_and_all_shape_keys_exact':True,'existing_nonhair_material_graphs_exact':True,'existing_images_exact':True,'world_camera_lights_scene_exact':True,'imported_rigs':[],'head_binding_requested':bind_head,'head_binding_rest_world_max_error':max(rest_errors.values(),default=0),'head_motion_consistency':motion,'before':before,'after_preserved_categories':{'object_count':len(before['objects']),'material_count':len(before['materials']),'image_count':len(before['images'])},'limits':'Transport verification only. Source art, UV appearance, rig contact, animation and ALL ART acceptance remain independent.'}
 if report_path:Path(report_path).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
 return report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--target',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output');ap.add_argument('--report',required=True);ap.add_argument('--bind-head',action='store_true');ap.add_argument('--expected-preservation-report');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);target=Path(args.target);target_sha=sha(target)
 if args.output and Path(args.output).exists():raise RuntimeError('Refusing to overwrite output native')
 bpy.ops.wm.open_mainfile(filepath=str(target),use_scripts=False)
 if args.expected_preservation_report:
  expected=json.loads(Path(args.expected_preservation_report).read_text(encoding='utf-8'))['before'];cfg=json.loads(Path(args.manifest).read_text(encoding='utf-8'));mutable={r['name'] for r in cfg['baseline_visible_hair']+cfg['active_hair']};delta=verify_preserved(expected,nonhair_snapshot(mutable))
  if delta:raise RuntimeError('Fresh-reopen preservation failure: '+json.dumps(delta,ensure_ascii=False))
 report=apply_hair_bundle(args.manifest,args.bind_head,args.report)
 if args.expected_preservation_report:
  report['fresh_reopen_original_nonhair_exact']=True;Path(args.report).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
 if args.output:bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.output)),relative_remap=False)
 if sha(target)!=target_sha:raise RuntimeError('Input target native changed on disk')
 print('HAIR_REPLAY',report['status'],len(report['active_hair']))

if __name__=='__main__':main()
