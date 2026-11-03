"""One live terminal-module select/apply/restore on retained M2 derived Main.

Requires root's exclusive live token and the existing borrowed hair review.
Original Main and accepted brows/face/body stay exact; projected ink is OFF.
"""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
FOLDER=ROOT/'.mia-cache/face-live/fringe-terminal01-ready'
KEY='MIA_FringeTerminal01'
PREFIX='MIA_Hair_FringeTerminal01'
ns=bpy.app.driver_namespace
phase=globals().get('MIA_EDIT_PHASE','select')
review=ns['MIA_HairReviewState']


def co_sha(ob):
    return hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices],np.float32).tobytes()).hexdigest()


def protected():
    body=bpy.data.objects['MIA_Review12_H_LiveRepair']
    assert co_sha(body)==review['body_sha256']
    m2=ns['MIA_CurvedRear03Base']
    source=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
    assert co_sha(source)==m2['source_raw_sha256']
    derived=next(o for o in m2['objects'] if o.name.endswith('_RemainingMain'))
    assert source.hide_render and not derived.hide_render
    return body,m2,source,derived


body,m2,source,derived=protected()
if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
cfg=json.loads((FOLDER/'candidate.json').read_text())
if phase in ('select','apply'):
    assert not cfg.get('install_forbidden',False), 'This actual trial was rejected; restore remains available'
payload=FOLDER/'geometry.npz'
assert hashlib.sha256(payload.read_bytes()).hexdigest()==cfg['payload_sha256']
data=np.load(payload)
faces=np.array([p.vertices[:] for p in derived.data.polygons],np.int32)
assert np.array_equal(faces[data['hidden_faces']],data['expected_hidden_triangles'])

if phase=='select':
    assert KEY not in ns
    state=dict(objects=[],meshes=[],groups=[],materials=[],attribute=None,modifier=None,
        before_derived_sha=co_sha(derived),derived=derived,
        retained_m2_sha={o.name:co_sha(o) for o in m2['objects']},
        brow_sha={f'V31_SourceBrow_{side}':co_sha(bpy.data.objects[f'V31_SourceBrow_{side}']) for side in (-1,1)},
        overlay=[],frame_strength=None,
        selection={domain:np.array([x.select for x in getattr(derived.data,domain)]) for domain in ('vertices','edges','polygons')})
    ns[KEY]=state
    # Turn the old proxy OFF before the baseline image as well as the candidate.
    # Capture once here so restore returns the actual incoming graphic state.
    for ob in bpy.data.objects:
        if ob.get('mia_role')=='brow_display' or ob.name.startswith('MiaHair_BrowInkProjection_'):
            flag=ob.get('MIA12_source_hair_hide_render')
            state['overlay'].append((ob,ob.hide_get(),ob.hide_render,flag))
            ob.hide_set(True);ob.hide_render=True;ob['MIA12_source_hair_hide_render']=True
    frame=bpy.data.objects.get('MIA_v003_BrowInk_HeadFrame')
    if frame:
        state['frame_strength']=(frame,float(frame['Strength']))
        frame['Strength']=0.;frame.update_tag()
    for ob in bpy.context.selected_objects:ob.select_set(False)
    derived.select_set(True);bpy.context.view_layer.objects.active=derived
    for domain in ('vertices','edges','polygons'):
        for item in getattr(derived.data,domain):item.select=False
    for i in data['hidden_faces']:derived.data.polygons[int(i)].select=True
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=True
    # Object-mode selection is intentional: entering EDIT just for a highlight
    # adds/reorders Blender UV-selection attributes on this textured derived
    # mesh. The scoped ownership image provides the detailed selection view.
    report=dict(phase=phase,selected_faces=len(data['hidden_faces']),selected_vertices=cfg['hidden_vertices'],
        complete_disconnected_shell_islands=len(cfg['hidden_component_roots']),
        original_Main_and_retained_M2_preserved=True,object_mode_scope_selection=True,
        partial_display_overlay_OFF=True,geometry_modified=False,ART=False)
elif phase=='apply':
    state=ns[KEY]
    assert not state['objects'] and state['modifier'] is None
    for name,expected in state['retained_m2_sha'].items():assert co_sha(bpy.data.objects[name])==expected,name
    attr=derived.data.attributes.new(name=KEY+'_RemoveFace',type='BOOLEAN',domain='FACE');state['attribute']=attr
    mask=np.zeros(len(faces),np.int32);mask[data['hidden_faces']]=1;attr.data.foreach_set('value',mask)
    group=bpy.data.node_groups.new(KEY+'_CombinedFrontUnderlap','GeometryNodeTree');state['groups'].append(group)
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    ni=group.nodes.new('NodeGroupInput');no=group.nodes.new('NodeGroupOutput')
    field=group.nodes.new('GeometryNodeInputNamedAttribute');field.data_type='BOOLEAN';field.inputs['Name'].default_value=attr.name
    delete=group.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE'
    group.links.new(ni.outputs['Geometry'],delete.inputs['Geometry']);group.links.new(field.outputs['Attribute'],delete.inputs['Selection']);group.links.new(delete.outputs['Geometry'],no.inputs['Geometry'])
    mod=derived.modifiers.new(KEY+'_ScopedTerminalUnderlap','NODES');mod.node_group=group;state['modifier']=mod
    material=bpy.data.materials.new(PREFIX+'_GeometryOnly');material.use_nodes=True;state['materials'].append(material)
    material.diffuse_color=(.145,.12,.12,1)
    bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=material.diffuse_color;bs.inputs['Roughness'].default_value=.8
    actors=[]
    for row in cfg['locks']:
        name=row['name'];q=data[name+'_world'];f=data[name+'_triangles'];uv=data[name+'_UV']
        me=bpy.data.meshes.new(PREFIX+'_'+name);me.from_pydata(q.tolist(),[],f.tolist());me.update()
        ob=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(ob)
        state['objects'].append(ob);state['meshes'].append(me);me.materials.append(material)
        for p in me.polygons:p.use_smooth=True
        layer=me.uv_layers.new(name='LockParamUV');layer.data.foreach_set('uv',uv.reshape(-1,2).ravel())
        ob['mia_component']='hair';ob['MIA12_source_hair_hide_render']=False
        ob['MIA_role']='UNACCEPTED local terminal forelock physical-gap probe'
        ob['MIA_rig_status']='Static source-shaped hair probe; expression head required for later actual evaluation'
        actors.append(dict(name=ob.name,vertices=len(q),faces=len(f),raw_sha256=co_sha(ob)))
    bpy.context.view_layer.update()
    ev=derived.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    actual_remaining_faces=len(me.polygons);ev.to_mesh_clear()
    assert actual_remaining_faces==len(faces)-1781-len(data['hidden_faces']), actual_remaining_faces
    for name,expected in state['retained_m2_sha'].items():assert co_sha(bpy.data.objects[name])==expected,name
    for name,expected in state['brow_sha'].items():assert co_sha(bpy.data.objects[name])==expected,name
    protected()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=False
    report=dict(phase=phase,actual_live_install=True,actors=actors,remaining_Main_faces=actual_remaining_faces,
        additional_front_mask_faces=len(data['hidden_faces']),one_active_derived_Main=True,
        original_Main_and_retained_M2_raw_exact=True,true_brow_raw_exact=True,partial_display_overlay_OFF=True,
        body_sha256=co_sha(body),target_shader_finished=False,expression_validated=False,ART=False,native_saved=False)
elif phase=='restore':
    state=ns[KEY]
    for ob in state['objects']:bpy.data.objects.remove(ob,do_unlink=True)
    for mesh in state['meshes']:
        if mesh.users==0:bpy.data.meshes.remove(mesh)
    if state['modifier']:derived.modifiers.remove(state['modifier'])
    if state['attribute']:derived.data.attributes.remove(state['attribute'])
    for group in state['groups']:
        if group.users==0:bpy.data.node_groups.remove(group)
    for material in state['materials']:
        if material.users==0:bpy.data.materials.remove(material)
    for ob,hidden,render,flag in state['overlay']:
        ob.hide_set(hidden);ob.hide_render=render
        if flag is None:ob.pop('MIA12_source_hair_hide_render',None)
        else:ob['MIA12_source_hair_hide_render']=flag
    if state['frame_strength']:
        frame,value=state['frame_strength'];frame['Strength']=value;frame.update_tag()
    for domain,values in state['selection'].items():
        for item,value in zip(getattr(derived.data,domain),values):item.select=bool(value)
    bpy.context.view_layer.update()
    for name,expected in state['retained_m2_sha'].items():assert co_sha(bpy.data.objects[name])==expected,name
    for name,expected in state['brow_sha'].items():assert co_sha(bpy.data.objects[name])==expected,name
    protected();del ns[KEY]
    report=dict(phase=phase,local_terminal_trial_removed=True,retained_M2_exact=True,
        original_Main_and_brows_exact=True,previous_graphic_visibility_returned=True,native_saved=False)
else:
    raise ValueError(phase)
(FOLDER/f'live-{phase}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
