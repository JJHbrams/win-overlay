"""One-image numeric Crown fallback recovery on a current scene only."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
def apply(folder,mode='fallback'):
 assert mode in ['fallback','rear_art','combined'];folder=Path(folder);base=json.loads((folder/'current-UV-boundary-report.json').read_text());cfg=json.loads((folder/'baked-report.json').read_text());payload=folder/'fallback-baked-payload.npz';imagefile=folder/'RecoveredStaticCrown_4096_RGBA.png';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(payload)==cfg['payload_sha256']
 if mode=='rear_art':cfg=dict(cfg,**json.loads((folder/'rear-guide-report.json').read_text()));imagefile=folder/'RecoveredRearCrown_4096_RGBA.png'
 assert sha(imagefile)==cfg['texture_sha256'];d=np.load(payload);ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;q=np.array([v.co[:] for v in m.vertices],np.float32);assert hashlib.sha256(q.tobytes()).hexdigest()==base['current_coords_sha256'];assert len(m.polygons)==120915
 for name,digest in base['original_six_UV_hashes'].items():assert hashlib.sha256(np.array([v.uv[:] for v in m.uv_layers[name].data],np.float32).tobytes()).hexdigest()==digest
 ids=d['polygon_indices'];assert np.array_equal(np.array([m.polygons[int(i)].vertices[:] for i in ids]),d['raw_vertices']);assert np.array_equal(np.array([m.attributes['MIA_SOURCE_POLYGON'].data[int(i)].value for i in ids]),d['raw_source_ids']);assert all(m.polygons[int(i)].material_index==0 for i in ids);assert cfg['new_unique_UV_overlap_pairs']==0
 scope=m.attributes['MIA_R_SourceAshAndScope'];assert all(scope.data[int(v)].color[3]==0 for v in np.unique(d['raw_vertices']))
 uvname='MIA_v003_RecoveredCrown_UV';assert uvname not in m.uv_layers;state=[(u.name,bool(u.active_render),bool(u.active_clone)) for u in m.uv_layers];active=m.uv_layers.active_index;allUV=np.zeros((len(m.loops),2),np.float32);loops=np.array([m.polygons[int(i)].loop_indices[:] for i in ids]);allUV[loops.ravel()]=d['loop_uv'].reshape(-1,2);new=m.uv_layers.new(name=uvname);new.data.foreach_set('uv',allUV.ravel());new.active_render=False;new.active_clone=False
 for name,render,clone in state:m.uv_layers[name].active_render=render;m.uv_layers[name].active_clone=clone
 m.uv_layers.active_index=active;old=m.materials[0];assert old.name.startswith('MIA_v002_R_SideNape_');ma=old.copy();ma.name='MIA_v003_Crown_RecoveredV29_'+{'fallback':'StaticBake','rear_art':'RearGuideChallenger','combined':'FallbackAndRearGuide'}[mode];n=ma.node_tree.nodes;l=ma.node_tree.links;mix=n['V002_COHERENT_AUTHORED_PIGMENT'];assert not mix.inputs[1].is_linked;fallback=list(mix.inputs[1].default_value);grade=n['V002_SOURCE_ASH_GRADE_INPUT'];l.new(mix.outputs['Color'],grade.inputs[0]);image=bpy.data.images.load(str(imagefile),check_existing=False);image.name='MIA_v003_RecoveredCrown4096_'+mode;image.colorspace_settings.name='sRGB';image.alpha_mode='CHANNEL_PACKED';image.pack();uv=n.new('ShaderNodeUVMap');uv.name='V003_RECOVERED_CROWN_UNIQUE_UV';uv.uv_map=uvname;tex=n.new('ShaderNodeTexImage');tex.name='V003_STATIC_COLOR_AND_BOUNDARY_GATE';tex.image=image;tex.interpolation='Linear';tex.extension='CLIP';l.new(uv.outputs[0],tex.inputs['Vector']);blend=n.new('ShaderNodeMixRGB');blend.name='V003_EXISTING_PAINT_IN_OLD_FALLBACK_ONLY' if mode in ['fallback','combined'] else 'V003_REAR_OWNED_GUIDE_ART_REPLACEMENT';l.new(tex.outputs['Alpha'],blend.inputs[0]);l.new(tex.outputs['Color'],blend.inputs[2])
 if mode in ['fallback','combined']:blend.inputs[1].default_value=fallback;l.new(blend.outputs[0],mix.inputs[1])
 else:l.new(mix.outputs['Color'],blend.inputs[1]);l.new(blend.outputs[0],grade.inputs[0])
 if mode=='combined':
  rear_cfg=json.loads((folder/'rear-guide-report.json').read_text());rear_file=folder/'RecoveredRearCrown_4096_RGBA.png';assert sha(rear_file)==rear_cfg['texture_sha256'];rear_image=bpy.data.images.load(str(rear_file),check_existing=False);rear_image.name='MIA_v003_RearCrownOverrideGate4096';rear_image.colorspace_settings.name='sRGB';rear_image.alpha_mode='CHANNEL_PACKED';rear_image.pack();gate=n.new('ShaderNodeTexImage');gate.name='V003_REAR_OVERRIDE_GATE';gate.image=rear_image;gate.interpolation='Linear';gate.extension='CLIP';l.new(uv.outputs[0],gate.inputs['Vector']);over=n.new('ShaderNodeMixRGB');over.name='V003_REAR_GUIDE_ART_OVER_FALLBACK_BASE';l.new(gate.outputs['Alpha'],over.inputs[0]);l.new(mix.outputs['Color'],over.inputs[1]);l.new(tex.outputs['Color'],over.inputs[2]);l.new(over.outputs[0],grade.inputs[0])
 out=ma.node_tree.get_output_node('EEVEE');seen=set();stack=[out]
 while stack:
  node=stack.pop()
  if node in seen:continue
  seen.add(node)
  for inp in node.inputs:
   for link in inp.links:stack.append(link.from_node)
 for node in list(n):
  if node not in seen:n.remove(node)
 attrs={x.attribute_name for x in n if x.type=='ATTRIBUTE'};uvs={x.uv_map for x in n if x.type=='UVMAP'};assert len(attrs)==9 and len(uvs)==5;assert not any(x.type=='NORMAL_MAP' for x in n);slot=len(m.materials);m.materials.append(ma)
 for i in ids:m.polygons[int(i)].material_index=slot
 description={'fallback':'NONE; fallback only','rear_art':'Bounded physical rear pure Crown only; original current pigment outside rear mask','combined':'Recovered fallback base across owned Crown; current live guide preserved outside bounded rear override, conservative front-guide hold'}[mode]
 bpy.context.view_layer.update();return dict(mode=mode,material=ma.name,slot=slot,faces=len(ids),original6UV_exact=True,new_UV=uvname,new_generic_attributes=0,active_generic_attributes=len(attrs),active_UV_streams=len(uvs),active_images=sum(x.type=='TEX_IMAGE' for x in n),guide_factor_source=mix.inputs[0].links[0].from_node.name,guide_color_source=mix.inputs[2].links[0].from_node.name,guide_art_replacement=description,actual_normals_K_lights_preserved=True,old_normal_maps_reused=False,native_saved=False,ART=False,shader_compilation='Must be checked by actual one-frame probe; stream count alone is not proof')
