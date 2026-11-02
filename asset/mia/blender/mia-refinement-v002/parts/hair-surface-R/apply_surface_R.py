"""Portable Side_Nape-only numeric pigment envelope; no native replay/save."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
def apply(folder):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text());payload=folder/'pigment-envelope.npz'
 assert hashlib.sha256(payload.read_bytes()).hexdigest()==manifest['payload_sha256']
 ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];me=ob.data;co=np.array([v.co[:] for v in me.vertices],np.float32)
 assert len(me.polygons)==120915 and len(me.vertices)==100383
 assert hashlib.sha256(co.tobytes()).hexdigest()==manifest['expected_coords_sha256']
 assert 'MIA_R_SourceAshAndScope' not in me.attributes,'Apply R once to exact integrated MN+L+O+P state.'
 data=np.load(payload);old=ob.material_slots[0].material
 assert old.name.startswith('MIA_V002_DeformNormals_')
 oldMix=old.node_tree.nodes['V002_COHERENT_AUTHORED_PIGMENT']
 assert not oldMix.inputs[1].is_linked and np.allclose(oldMix.inputs[1].default_value[:3],[.12,.115,.12])
 # Existing EEVEE projective shader uses13 vertex attributes. A single extra
 # float4 leaves its position/normal inputs within the16 hardware-slot limit.
 # Only1 raw point passed weak0.1 alignment and none passed0.5, so the proposed
 # fine residual has no defensible continuous support and is withheld entirely.
 color=data['low_frequency_source_ash'].copy();color[:,3]=data['side_nape'];name='MIA_R_SourceAshAndScope';attr=me.attributes.new(name,'FLOAT_COLOR','POINT');attr.data.foreach_set('color',color.ravel())
 ma=old.copy();ma.name='MIA_v002_R_SideNape_SourceAshEnvelope';n=ma.node_tree.nodes;l=ma.node_tree.links;oldMix=n['V002_COHERENT_AUTHORED_PIGMENT'];grade=n['V002_SOURCE_ASH_GRADE_INPUT'];oldPigment=grade.inputs[0].links[0].from_socket
 assert oldPigment.node==oldMix
 def attr(name):
  node=n.new('ShaderNodeAttribute');node.attribute_name=name;node.name=name;return node
 base=attr('MIA_R_SourceAshAndScope');mix=n.new('ShaderNodeMixRGB');mix.name='MIA_R_SemanticPigmentOnly';l.new(base.outputs['Alpha'],mix.inputs[0]);l.new(oldPigment,mix.inputs[1]);l.new(base.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],grade.inputs[0]);ob.material_slots[0].material=ma
 return {'variant':'R Side_Nape source-ash low-frequency envelope','old_material':old.name,'new_material':ma.name,'payload_sha256':manifest['payload_sha256'],'scope':'Main Side_Nape weight only in COLOR alpha; factor0 sends exact original pigment through unchanged K/light/normal output.','new_POINT_attributes':['MIA_R_SourceAshAndScope'],'geometry_UV_rig_original_maps_unchanged':True,'fine_ink_constraint':'No sufficiently supported continuous geometric/guide-correspondent fine marks were found (1weakpoint>0.1,none>0.5); all unsupported projected ink withheld. Existing physical strand geometry and all outside-scope ink remain. Fine authored strand paint is explicitly OPEN.','limits':manifest['limits'],'ART':'CHALLENGER_UNVERIFIED'}
