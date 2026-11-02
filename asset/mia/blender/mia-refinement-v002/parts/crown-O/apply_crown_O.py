"""Standalone portable shape/normal-weight delta; requires actual MN hair."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent
def apply(folder=None):
 O=Path(folder) if folder else (P if (P/'report.json').exists() else P/'crown-O');r=json.loads((O/'report.json').read_text());d=np.load(O/'main-coordinate-delta.npz');ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=ob.data;before=np.array([v.co[:] for v in m.vertices],'<f4');assert len(m.polygons)==120913 and hashlib.sha256(before.tobytes()).hexdigest()==r['source_main_coords_sha256'],'Crown O requires the exact MN base; no stale-shape replay';oldUV={u.name:np.array([v.uv[:] for v in u.data],np.float32) for u in m.uv_layers}
 for v,p in zip(m.vertices,d['target']):v.co=p
 attr=m.attributes.get('MIA_V002_RimNormalWeight');assert attr is not None;old=np.array([v.value for v in attr.data],np.float32);attr.data.foreach_set('value',np.maximum(old,d['true_normal_weight']));ob['mia_component']='hair';m.update();after=np.array([v.co[:] for v in m.vertices],'<f4');assert hashlib.sha256(after.tobytes()).hexdigest()==r['target_main_coords_sha256'];assert all(np.array_equal(np.array([v.uv[:] for v in m.uv_layers[name].data],np.float32),uv) for name,uv in oldUV.items());return {'variant':'crown-O','report':r,'source_and_target_hash_guards':True,'static_shader_rule':'Changed crown uses existing geometric-normal blend attribute only; skinned L already uses deformed geometry normals. Original maps/UVs are unedited.','ART':'UNVERIFIED'}
