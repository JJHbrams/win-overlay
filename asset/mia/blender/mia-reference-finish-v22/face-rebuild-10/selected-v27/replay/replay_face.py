import bpy,sys,json,hashlib,argparse
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).parent;sys.path.insert(0,str(P));from state import fingerprint
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);source=Path(a.source);out=Path(a.output_dir);meta=json.loads((P/'manifest.json').read_text());assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['source_sha256'],'Immutable baseline SHA mismatch';assert hashlib.sha256((P/'face-owners.blend').read_bytes()).hexdigest()==meta['library_sha256'];out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(source))
with bpy.data.libraries.load(str(P/'face-owners.blend'),link=False) as (src,dst):dst.objects=list(meta['objects'])
for o in dst.objects:bpy.context.scene.collection.objects.link(o)
def restore(v):
 if isinstance(v,dict) and 'id' in v:
  collection={'Object':bpy.data.objects,'GeometryNodeTree':bpy.data.node_groups,'ShaderNodeTree':bpy.data.node_groups,'Material':bpy.data.materials}.get(v['id']);assert collection is not None,v;return collection[v['name']]
 if isinstance(v,dict) and 'set' in v:return set(v['set'])
 return v
for name,r in meta['objects'].items():
 o=bpy.data.objects[name];o.parent=bpy.data.objects.get(r['parent']) if r['parent'] else None;o.matrix_parent_inverse=Matrix(r['matrix_parent_inverse']);o.matrix_basis=Matrix(r['matrix_basis']);o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 for i,mat in r['original_material_slots'].items():o.material_slots[int(i)].material=bpy.data.materials[mat]
 for data in r['modifiers']:
  m=o.modifiers.new(data['name'],data['type'])
  for key,value in data['properties'].items():setattr(m,key,restore(value))
  for key,value in data['custom'].items():m[key]=restore(value)
 for k in o.data.shape_keys.key_blocks:k.value=0
for name,flags in meta['original_visibility'].items():
 o=bpy.data.objects.get(name)
 if o:o.hide_render,o.hide_viewport=flags[:2];o.hide_set(flags[2])
if 'scene' in meta:
 scene=bpy.context.scene;settings=meta['scene'];scene.render.engine=settings['render_engine'];scene.render.use_freestyle=settings['use_freestyle']
 for key in ['view_transform','look','exposure','gamma']:setattr(scene.view_settings,key,settings[key])
bpy.context.view_layer.update();differences={n:{k:[r['fingerprint'][k],v] for k,v in fingerprint(bpy.data.objects[n]).items() if r['fingerprint'][k]!=v} for n,r in meta['objects'].items()};differences={n:d for n,d in differences.items() if d};assert not differences,differences
target=out/'Mia_Foundation_v27_Replayed.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target));(out/'replay-audit.json').write_text(json.dumps({'source_sha256':meta['source_sha256'],'reference_native_sha256':meta['final_sha256'],'replay_native_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'all_six_owner_keys_topology_uv_weights_materials_transforms_exact':True,'fingerprint_differences':differences,'limits':'File byte SHA may differ by save path; owner data fingerprints are the replay equivalence criterion.'},indent=2));print('REPLAY_VERIFIED')
