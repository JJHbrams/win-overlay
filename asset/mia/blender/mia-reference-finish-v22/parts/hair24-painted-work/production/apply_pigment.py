import bpy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).parent/'paint1';S=P.parent/'sculpt2'
source=S/'Mia_HairStructure_v24.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
manifest=json.loads((P/'pigment-manifest.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_native_sha256']
def scope(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(np.array(v.co[:],dtype=np.float32).tobytes())
 for p in o.data.polygons:h.update(np.array(p.vertices[:],dtype=np.uint32).tobytes())
 for uv in o.data.uv_layers:
  for value in uv.data:h.update(np.array(value.uv[:],dtype=np.float32).tobytes())
 return h.hexdigest()
retained=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];retained_scope=scope(retained)
for row in manifest['maps']:
 o=bpy.data.objects[row['owner']];uv=o.data.uv_layers.new(name='V24_GatherPaintUV');old=o.data.uv_layers['MIA_V20_LongitudinalUV']
 for a,b in zip(old.data,uv.data):b.uv=((a.uv.x+.006)/1.012*.94+.03,a.uv.y*.94+.03)
 image=bpy.data.images.load(row['path'],check_existing=False);image.name=o.name+'_Pigment1024';image.colorspace_settings.name='sRGB';image.pack();image.filepath=str(Path(row['path']).resolve())
 m=bpy.data.materials['MIA_V20_AuthoredFold_AshStrata_V22_LightToon'].copy();m.name=o.name+'_PaintedToon';n=m.node_tree.nodes;l=m.node_tree.links
 coord=n.new('ShaderNodeUVMap');coord.name='V24_ConsumedPigmentUV';coord.uv_map='V24_GatherPaintUV'
 tex=n.new('ShaderNodeTexImage');tex.name='V24_GeometryAlignedPigment';tex.image=image;tex.interpolation='Linear';l.new(coord.outputs['UV'],tex.inputs['Vector'])
 edge=n['V22_GRAZING_EDGE_INK'];original=edge.inputs[1].links[0].from_socket
 mix=n.new('ShaderNodeMixRGB');mix.name='V24_VisiblePaint_UnseenAshFallback';l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(original,mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],edge.inputs[1])
 m['paint_provenance']='Generated geometry-aligned plates baked by actual camera projection and BVH visibility; limited to gathered hair. Not recovered Pixal pixels, not pure albedo.'
 m['consumed_route']='V24_GatherPaintUV -> packed sRGB RGBA -> alpha fallback inherited Ash -> grazing edge -> scene Diffuse toon light and bounded sheen -> Emission'
 o.data.materials[0]=m
assert scope(retained)==retained_scope
out=P/'Mia_HairStructurePaint_v24.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
handoff={'status':'WIP / ART UNAPPROVED, partial rear-gathering improvement only','candidate_native':{'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},'source_native':json.loads((S/'manifest.json').read_text())['source'],'geometry_parent':{'path':str(source),'sha256':manifest['source_native_sha256']},'new_owners':[r['owner'] for r in manifest['maps']],'replace_mesh_owners':[],'hidden_retained_owners':['MIA_V20_HalfUp_Fold_Left','MIA_V20_HalfUp_Fold_Right','MIA_V20_HalfUp_Binder'],'unchanged_detailed_hair_scope':retained_scope,'new_owner_descriptors':[{'name':r['owner'],'parent':None,'matrix_world':[list(row) for row in bpy.data.objects[r['owner']].matrix_world],'modifiers':[],'shape_keys':False,'uv':[u.name for u in bpy.data.objects[r['owner']].data.uv_layers],'material':bpy.data.objects[r['owner']].data.materials[0].name} for r in manifest['maps']],'maps':manifest['maps'],'limits':['Main ear/nape extraction failures remain; boundary1 smoothing rejected and excluded','Whole AC5/AC6 remains FAIL/UNVERIFIED','No final rig/physics, no original face/body/hair coordinates changed','Generated maps only add bounded bun pigment, not full-hair high-frequency detail']}
(P/'handoff.json').write_text(json.dumps(handoff,indent=2));print('SAVED',handoff['candidate_native'])
