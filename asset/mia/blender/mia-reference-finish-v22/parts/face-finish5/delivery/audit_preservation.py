"""Read-only saved-native material/light/image preservation audit."""
import bpy,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def value(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def tree(t):
 if not t:return None
 return {'nodes':{n.name:{'type':n.bl_idname,'image':getattr(getattr(n,'image',None),'name',None),'inputs':[(i.name,value(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],'outputs':[(i.name,value(i.default_value)) for i in n.outputs if hasattr(i,'default_value')],'uv_map':getattr(n,'uv_map',None),'operation':getattr(n,'operation',None),'blend_type':getattr(n,'blend_type',None),'ramp':[(e.position,list(e.color)) for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in t.nodes},'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links)}
def snapshot(p):
 bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene
 return {'materials':{m.name:tree(m.node_tree) for m in bpy.data.materials},'packed':{i.name:{'sha256':hashlib.sha256(i.packed_file.data).hexdigest(),'fake_user':i.use_fake_user} for i in bpy.data.images if i.packed_file},'lights':{o.name:{'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color),'type':o.data.type,'size':getattr(o.data,'size',None),'tree':tree(o.data.node_tree)} for o in bpy.data.objects if o.type=='LIGHT'},'world':tree(s.world.node_tree),'display':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma,s.display_settings.display_device],'skin_slot':bpy.data.objects['MIA_V14_SculptedSkin'].material_slots[7].material.name}
a=H.parent/'finish-4/Mia_FaceFinish_v22.blend';b=H/'Mia_FaceFinish5_v22.blend';ah,bh=sha(a),sha(b);old,new=snapshot(a),snapshot(b)
assert old['packed']==new['packed'];assert len(new['packed'])==69;assert all(v['fake_user'] for v in new['packed'].values())
for k in ['lights','world','display']:assert old[k]==new[k],k
for n,t in old['materials'].items():
 if n!=old['skin_slot']:assert new['materials'][n]==t,n
assert sha(a)==ah and sha(b)==bh
r={'source_sha256':ah,'candidate_sha256':bh,'all_69_packed_image_bytes_and_fake_users_exact':True,'all_nonreplaced_material_node_graphs_and_socket_defaults_exact':True,'only_added_materials':sorted(set(new['materials'])-set(old['materials'])),'removed_zero_user_materials':sorted(set(old['materials'])-set(new['materials'])),'skin_material_assignment':[old['skin_slot'],new['skin_slot']],'native_lights_world_display_exact':True,'new_material_route':new['materials'][new['skin_slot']],'geometry_uv_keys_weights_audit':'manifest.json saved-native reopened snapshots, exact except skin slot7 material assignment','native_files_unchanged':True}
(H/'preservation-audit.json').write_text(json.dumps(r,indent=2));print('PRESERVATION_AUDIT_OK')
