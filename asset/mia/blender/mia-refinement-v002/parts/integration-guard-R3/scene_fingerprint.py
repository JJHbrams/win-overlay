"""Deterministic R3 data fingerprints. Never opens/saves or edits a scene."""
import hashlib,json,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix,Color,Euler,Quaternion

FINGERPRINT_VERSION='mia.scene-fingerprint.r3.2'

def id_reference(value):
    return None if value is None else dict(type=value.bl_rna.identifier,name=value.name_full,library=value.library.filepath if value.library else None)

def json_value(value):
    if isinstance(value,bpy.types.ID):return id_reference(value)
    if value is None or isinstance(value,(str,bool,int)):return value
    if isinstance(value,(float,np.floating)):
        value=float(value)
        return value if math.isfinite(value) else {'nonfinite':str(value)}
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,dict):return {str(k):json_value(v) for k,v in sorted(value.items(),key=lambda p:str(p[0]))}
    if isinstance(value,(Vector,Matrix,Color,Euler,Quaternion)):return [json_value(v) for v in value]
    if hasattr(value,'to_dict'):return json_value(value.to_dict())
    if hasattr(value,'to_list'):return json_value(value.to_list())
    if hasattr(value,'tolist'):return json_value(value.tolist())
    if isinstance(value,set):
        return sorted([json_value(v) for v in value],key=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')))
    if isinstance(value,(list,tuple)):return [json_value(v) for v in value]
    if hasattr(value,'__iter__') and not isinstance(value,bpy.types.bpy_struct):return [json_value(v) for v in value]
    raise TypeError('No deterministic JSON serializer for '+type(value).__name__)

def canonical_json(value):return json.dumps(json_value(value),sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def json_digest(value):return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def custom_properties(block):
    if block is None:return {}
    try:keys=sorted(block.keys())
    except TypeError:return {}  # Some conventional modifiers have no IDProps.
    return {k:json_value(block[k]) for k in keys}
def custom_property_ui(block):
    """Authored ID-property limits/defaults, not editor selection/layout state."""
    if block is None:return {}
    try:keys=sorted(block.keys())
    except (TypeError,KeyError):return {}
    result={}
    for key in keys:
        try:metadata=block.id_properties_ui(key).as_dict()
        except (TypeError,KeyError):continue  # Unsupported property UI types only.
        result[key]=json_value(metadata)  # Serialization failures must propagate.
    return result
def _properties(block,names):return {n:json_value(getattr(block,n)) for n in names if hasattr(block,n)}
def digest(data,field,width,dtype=np.float32):
    arr=np.empty(len(data)*width,dtype=dtype);data.foreach_get(field,arr)
    return hashlib.sha256(arr.tobytes()).hexdigest()

def driver_signature(block):
    ad=getattr(block,'animation_data',None) if block is not None else None
    rows=[]
    for curve in ad.drivers if ad else []:
        d=curve.driver;variables=[]
        for v in d.variables:
            targets=[]
            for t in v.targets:
                target=_properties(t,['id_type','data_path','bone_target','transform_type','transform_space','rotation_mode','use_fallback_value','fallback_value'])
                target['id']=id_reference(t.id);targets.append(target)
            variables.append(dict(name=v.name,type=v.type,targets=targets))
        modifiers=[]
        for m in curve.modifiers:
            modifiers.append(dict(type=m.type,settings=_properties(m,['mute','use_restricted_range','frame_start','frame_end','blend_in','blend_out','use_influence','influence','mode','poly_order','coefficients','function_type','amplitude','phase_multiplier','phase_offset','value_offset','use_additive','scale','strength','phase','offset','depth','blend_type'])))
        rows.append(dict(data_path=curve.data_path,array_index=curve.array_index,mute=curve.mute,extrapolation=curve.extrapolation,type=d.type,expression=d.expression,use_self=d.use_self,
            variables=sorted(variables,key=lambda v:v['name']),modifiers=modifiers,
            keyframes=[dict(co=list(k.co),interpolation=k.interpolation,handle_left=list(k.handle_left),handle_right=list(k.handle_right),handle_left_type=k.handle_left_type,handle_right_type=k.handle_right_type) for k in curve.keyframe_points]))
    return sorted(rows,key=lambda r:(r['data_path'],r['array_index']))

def _cache_key(block):
    # INTERNAL only: embedded material trees can share their RNA name. Pointers
    # never enter the authored signature or JSON output.
    return str(block.as_pointer())
def image_signature(image,cache=None):
    cache={} if cache is None else cache;key='image:'+_cache_key(image)
    if key in cache:return cache[key]
    row=dict(id=id_reference(image),properties=_properties(image,['source','filepath','file_format','alpha_mode','use_half_precision','use_view_as_render']),size=list(image.size),channels=image.channels,colorspace=image.colorspace_settings.name,
        packed_sha256=hashlib.sha256(bytes(image.packed_file.data)).hexdigest() if image.packed_file else None)
    cache[key]=row;return row

_NODE_SETTINGS=['operation','blend_type','use_clamp','clamp','interpolation','interpolation_type','extension','projection','projection_blend','uv_map','attribute_name','attribute_type','vector_type','convert_from','convert_to','space','distribution','component','target','is_active_output','normalize','normalize_normal','noise_dimensions','gradient_type','wave_type','wave_profile','rings_direction','bands_direction','voronoi_dimensions','feature','distance','axis','direction_type','invert','clamp_factor','clamp_result','data_type','mode','domain']
def node_tree_signature(tree,cache=None,stack=None):
    if tree is None:return None
    cache={} if cache is None else cache;stack=set() if stack is None else stack;key='tree:'+_cache_key(tree)
    if key in cache:return cache[key]
    if key in stack:return dict(cyclic_reference=id_reference(tree))
    stack=stack|{key};nodes=[]
    for n in sorted(tree.nodes,key=lambda n:n.name):
        sockets=lambda ss:[dict(identifier=s.identifier,name=s.name,type=s.bl_idname,default=json_value(s.default_value) if hasattr(s,'default_value') else None) for s in ss]
        row=dict(name=n.name,type=n.bl_idname,mute=n.mute,properties=_properties(n,_NODE_SETTINGS),custom_properties=custom_properties(n),custom_property_ui=custom_property_ui(n),inputs=sockets(n.inputs),outputs=sockets(n.outputs))
        for field in ['object','texture']:
            if hasattr(n,field):row[field]=id_reference(getattr(n,field))
        if getattr(n,'image',None):row['image']=image_signature(n.image,cache)
        if hasattr(n,'image_user'):row['image_user']=_properties(n.image_user,['frame_duration','frame_start','frame_offset','use_cyclic','use_auto_refresh','multilayer_layer','multilayer_pass','multilayer_view','tile'])
        if getattr(n,'node_tree',None):row['group']=node_tree_signature(n.node_tree,cache,stack)
        if hasattr(n,'color_ramp'):
            ramp=n.color_ramp;row['color_ramp']=dict(properties=_properties(ramp,['interpolation','color_mode','hue_interpolation']),elements=[dict(position=e.position,color=list(e.color)) for e in ramp.elements])
        if hasattr(n,'mapping') and not isinstance(n.mapping,(str,int,float,bool)):
            mapping=n.mapping
            if hasattr(mapping,'curves'):
                row['mapping']=dict(properties=_properties(mapping,['use_clip','clip_min_x','clip_min_y','clip_max_x','clip_max_y','extend','tone','black_level','white_level']),curves=[[dict(location=list(p.location),handle_type=p.handle_type) for p in c.points] for c in mapping.curves])
        nodes.append(row)
    outputs={}
    if hasattr(tree,'get_output_node'):
        for engine in ['ALL','EEVEE','CYCLES']:
            node=tree.get_output_node(engine);outputs[engine]=node.name if node else None
    interface=[]
    if hasattr(tree,'interface'):
        for item in tree.interface.items_tree:
            interface.append(dict(name=item.name,item_type=item.item_type,properties=_properties(item,['identifier','in_out','socket_type','default_value','min_value','max_value','attribute_domain','default_attribute_name','hide_value','force_non_field'])))
    row=dict(id=id_reference(tree),nodes=nodes,links=sorted([list((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier)) for l in tree.links]),active_outputs=outputs,interface=interface,drivers=driver_signature(tree),custom_properties=custom_properties(tree),custom_property_ui=custom_property_ui(tree))
    cache[key]=row;return row

def material_signature(material,cache=None):
    if material is None:return None
    cache={} if cache is None else cache;key='material:'+_cache_key(material)
    if key in cache:return cache[key]
    row=dict(id=id_reference(material),properties=_properties(material,['use_nodes','diffuse_color','metallic','roughness','surface_render_method','use_backface_culling','use_backface_culling_shadow','use_backface_culling_lightprobe_volume','use_transparency_overlap','displacement_method','max_vertex_displacement','alpha_threshold']),drivers=driver_signature(material),custom_properties=custom_properties(material),custom_property_ui=custom_property_ui(material),node_tree=node_tree_signature(material.node_tree,cache) if material.use_nodes else None)
    result=dict(id=id_reference(material),sha256=json_digest(row));cache[key]=result;return result

_ATTR_TYPES={'FLOAT':('value',1,np.float32),'FLOAT_VECTOR':('vector',3,np.float32),'FLOAT2':('vector',2,np.float32),'FLOAT_COLOR':('color',4,np.float32),'BYTE_COLOR':('color',4,np.float32),'INT':('value',1,np.int32),'INT8':('value',1,np.int8),'INT32_2D':('value',2,np.int32),'BOOLEAN':('value',1,np.bool_),'QUATERNION':('value',4,np.float32),'FLOAT4X4':('value',16,np.float32)}
def point_attribute_signatures(mesh):
    rows={}
    for attr in sorted(mesh.attributes,key=lambda a:a.name):
        if attr.domain!='POINT' or attr.name.startswith(('.select_','.hide_')):continue
        row=dict(domain=attr.domain,data_type=attr.data_type,length=len(attr.data))
        if attr.data_type in _ATTR_TYPES:
            field,width,dtype=_ATTR_TYPES[attr.data_type];row['sha256']=digest(attr.data,field,width,dtype)
        else:row['numeric_hash']='NOT_NUMERIC'
        rows[attr.name]=row
    return rows

_MOD_SETTINGS=['show_viewport','show_render','object','target','auxiliary_target','node_group','vertex_group','invert_vertex_group','levels','render_levels','subdivision_type','quality','boundary_smooth','uv_smooth','use_creases','use_limit_surface','thickness','offset','project_limit','subsurf_levels','wrap_method','wrap_mode','use_project_x','use_project_y','use_project_z','use_positive_direction','use_negative_direction','cull_face','use_invert_cull','use_deform_preserve_volume','use_vertex_groups','use_bone_envelopes','use_multi_modifier','use_x','use_y','use_z','factor','iterations','merge_threshold','mode','loose_edges']
def modifier_signature(modifier,cache=None):
    row=dict(name=modifier.name,type=modifier.type,properties=_properties(modifier,_MOD_SETTINGS),custom_properties=custom_properties(modifier),custom_property_ui=custom_property_ui(modifier))
    if getattr(modifier,'node_group',None):row['node_group_sha256']=json_digest(node_tree_signature(modifier.node_group,cache))
    return row

def object_fingerprint(ob,cache=None):
    cache={} if cache is None else cache;data=getattr(ob,'data',None);keys=getattr(data,'shape_keys',None)
    row=dict(type=ob.type,matrix_world=[list(r) for r in ob.matrix_world],parent=ob.parent.name if ob.parent else None,parent_bone=ob.parent_bone,hidden=ob.hide_render,
        matrix_basis=[list(r) for r in ob.matrix_basis],matrix_parent_inverse=[list(r) for r in ob.matrix_parent_inverse],parent_type=ob.parent_type,hide_viewport=ob.hide_viewport,
        drivers=dict(object=driver_signature(ob),data=driver_signature(data),shape_keys=driver_signature(keys)),
        custom_properties=dict(object=custom_properties(ob),data=custom_properties(data),shape_keys=custom_properties(keys)),
        custom_property_ui=dict(object=custom_property_ui(ob),data=custom_property_ui(data),shape_keys=custom_property_ui(keys)))
    if ob.type=='MESH':
        m=ob.data
        row.update(vertices=digest(m.vertices,'co',3),loop_vertices=digest(m.loops,'vertex_index',1,np.int32),polygon_sizes=digest(m.polygons,'loop_total',1,np.int32),uv={u.name:digest(u.data,'uv',2) for u in m.uv_layers},materials=[q.name if q else None for q in m.materials],keys={k.name:digest(k.data,'co',3) for k in keys.key_blocks} if keys else {},weight_hash=hashlib.sha256(json.dumps([[(ob.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices],separators=(',',':')).encode()).hexdigest(),modifiers=[[q.name,q.type] for q in ob.modifiers],
            key_state={k.name:dict(value=k.value,mute=k.mute,relative_key=k.relative_key.name,slider_min=k.slider_min,slider_max=k.slider_max,vertex_group=k.vertex_group) for k in keys.key_blocks} if keys else {},point_attributes=point_attribute_signatures(m),material_signatures=[material_signature(q,cache) for q in m.materials],modifier_settings=[modifier_signature(q,cache) for q in ob.modifiers])
    elif ob.type=='ARMATURE':
        row['pose_basis']={b.name:[list(r) for r in b.matrix_basis] for b in ob.pose.bones}
        row['rest_bones']={b.name:dict(matrix_local=[list(r) for r in b.matrix_local],parent=b.parent.name if b.parent else None,use_deform=b.use_deform,custom_properties=custom_properties(b),custom_property_ui=custom_property_ui(b)) for b in data.bones}
    elif ob.type=='CAMERA':
        row['camera_spec']=_properties(data,['type','lens','lens_unit','ortho_scale','shift_x','shift_y','clip_start','clip_end','sensor_width','sensor_height','sensor_fit','panorama_type'])
        row['camera_spec']['dof']=_properties(data.dof,['use_dof','focus_object','focus_distance','aperture_fstop','aperture_blades','aperture_rotation','aperture_ratio'])
    elif ob.type=='LIGHT':
        row['light_spec']=_properties(data,['type','energy','color','shape','size','size_y','shadow_soft_size','use_shadow','diffuse_factor','specular_factor','volume_factor'])
        if getattr(data,'use_nodes',False):row['light_spec']['node_tree']=node_tree_signature(data.node_tree,cache)
    return row

def scene_envelope(scene=None,cache=None):
    s=bpy.context.scene if scene is None else scene;cache={} if cache is None else cache
    world=None if s.world is None else dict(id=id_reference(s.world),color=list(s.world.color),use_nodes=s.world.use_nodes,node_tree=node_tree_signature(s.world.node_tree,cache) if s.world.use_nodes else None,drivers=driver_signature(s.world),custom_properties=custom_properties(s.world),custom_property_ui=custom_property_ui(s.world))
    return dict(active_camera=s.camera.name if s.camera else None,frame=s.frame_current,subframe=s.frame_subframe,world=world,
        render=_properties(s.render,['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','use_freestyle','fps','fps_base','use_motion_blur','motion_blur_shutter']),
        image_settings=_properties(s.render.image_settings,['file_format','color_mode','color_depth','compression']),
        color=_properties(s.view_settings,['view_transform','look','exposure','gamma','use_curve_mapping']),display_device=s.display_settings.display_device,
        custom_properties=custom_properties(s),custom_property_ui=custom_property_ui(s),drivers=driver_signature(s))

def snapshot_scene(scene=None):
    bpy.context.view_layer.update();scene=bpy.context.scene if scene is None else scene;cache={}
    return dict(fingerprint_version=FINGERPRINT_VERSION,objects={o.name:object_fingerprint(o,cache) for o in sorted(scene.objects,key=lambda o:o.name)},scene=scene_envelope(scene,cache))

def _driver_map(row,scope):return {(r['data_path'],r['array_index']):r for r in row.get('drivers',{}).get(scope,[])}
def assert_existing_driver_preservation(before,after,stage):
    """Original curves may only change at explicitly declared path/index IDs."""
    allowed={(x['owner'],x['scope'],x['data_path'],x['array_index']) for x in stage.get('allowed_driver_changes',[])}
    changes=[]
    for name in sorted(set(before)&set(after)):
        for scope in ['object','data','shape_keys']:
            old=_driver_map(before[name],scope);new=_driver_map(after[name],scope)
            for key,record in old.items():
                if record!=new.get(key):
                    token=(name,scope,*key)
                    assert key in new,('Original driver removed',token)
                    assert token in allowed,('Undeclared original driver change',token)
                    changes.append(dict(owner=name,scope=scope,data_path=key[0],array_index=key[1]))
    return changes

def assert_scene_pose_owners_protected(before,after,stage):
    """Only a narrowly declared rig object driver may differ; pose stays exact."""
    allowed={(x['owner'],x['scope'],x['data_path'],x['array_index']) for x in stage.get('allowed_driver_changes',[])}
    for name,row in before.items():
        if row['type'] in ['CAMERA','LIGHT']:
            assert row==after.get(name),('Component changed camera/light owner',stage['id'],name)
        elif row['type']=='ARMATURE':
            now=after[name]
            assert {k:v for k,v in row.items() if k!='drivers'}=={k:v for k,v in now.items() if k!='drivers'},('Component changed rig pose/transform/data',stage['id'],name)
            assert row['drivers']['data']==now['drivers']['data'] and row['drivers']['shape_keys']==now['drivers']['shape_keys'],('Component changed rig data drivers',name)
            old=_driver_map(row,'object');new=_driver_map(now,'object')
            for key in set(old)|set(new):
                if old.get(key)!=new.get(key):
                    assert (name,'object',*key) in allowed,('Undeclared rig driver change',name,key)
                    assert key in new,('Rig driver removed',name,key)
