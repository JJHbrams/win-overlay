"""Only construct/inspect the new shader in background factory Blender; no render."""
from pathlib import Path
import importlib.util
import json
import bpy
path=Path(__file__).with_name('hair_tone_prototype.py')
spec=importlib.util.spec_from_file_location('mia_tone',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ma,report=m.build()
nodes=ma.node_tree.nodes
assert sum(n.type=='UVMAP' for n in nodes)==1
assert next(n for n in nodes if n.type=='UVMAP').uv_map=='LockParamUV'
assert not any(n.type=='TEX_IMAGE' for n in nodes)
assert len([n for n in nodes if n.bl_idname=='ShaderNodeShaderToRGB'])==1
assert any(n.type=='BSDF_DIFFUSE' for n in nodes)
assert next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'].is_linked
report.update(test='CPU node/API construction only; actual EEVEE and light response UNVERIFIED',nodes=len(nodes),links=len(ma.node_tree.links),GPU_used=False,native_saved=False)
report['shader_to_RGB_runtime_type']=next(n.type for n in nodes if n.bl_idname=='ShaderNodeShaderToRGB')
out=(Path(__file__).resolve().parents[3]/'.mia-cache/face-live/curved-rear03/tone-prototype');out.mkdir(parents=True,exist_ok=True)
(out/'cpu-nodes.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
