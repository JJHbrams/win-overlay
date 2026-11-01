"""Native UV edge coverage only; no painted bitmap or geometry edit."""
import sys, json, hashlib
from pathlib import Path
import bpy
P=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-lash-v29')
from audit_mesh_helpers import snapshot
source=P/'Mia_SourceBrows_v31_B.blend'; dest=P/'Mia_SourceBrows_v31_C.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source)=='2327f358aeb271fde90b9c20baa82c04e233cec226d1f7de13749c5e12784f9f'
assert not dest.exists()
before,_,bm,bi=snapshot(source)
mat=bpy.data.materials['V31_SourceBrow_CharcoalInk'].copy();mat.name='V31_SourceBrow_Ink_EdgeCoverage'
nt=mat.node_tree;n=nt.nodes;l=nt.links
out=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output)
emit=out.inputs['Surface'].links[0].from_node
uv=n.new('ShaderNodeUVMap');uv.uv_map='BrowParamUV'
sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0])
inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1.;l.new(sep.outputs['Y'],inv.inputs[1])
edge=n.new('ShaderNodeMath');edge.operation='MINIMUM';l.new(sep.outputs['Y'],edge.inputs[0]);l.new(inv.outputs[0],edge.inputs[1])
fade=n.new('ShaderNodeMapRange');fade.name='V31_Brow_EdgeCoverage';fade.interpolation_type='SMOOTHSTEP';fade.clamp=True
fade.inputs['From Min'].default_value=0.;fade.inputs['From Max'].default_value=.15;fade.inputs['To Min'].default_value=0.;fade.inputs['To Max'].default_value=1.;l.new(edge.outputs[0],fade.inputs['Value'])
transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
l.new(fade.outputs[0],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(emit.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
owners=['V31_SourceBrow_-1','V31_SourceBrow_1']
for name in owners:
 ob=bpy.data.objects[name];ob.data.materials[0].use_fake_user=True;ob.data.materials[0]=mat
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
after,_,am,ai=snapshot(dest)
checks={'all_original_nonbrow_records_exact':all(before[n]==after[n] for n in before if n not in owners),
        'brow_only_material_slots_changed':all(all(before[n][k]==after[n][k] for k in before[n] if k!='materials') for n in owners),
        'old_material_graphs_exact':all(bm[n]==am[n] for n in bm),'old_images_exact':bi==ai}
assert all(checks.values()),checks
report={'input':str(source),'input_sha256':sha(source),'output':str(dest),'sha256':sha(dest),'checks':checks,
        'scope':'Only2brow materialslots. Cross-strip UV edge coverage15percent per side, native SmoothStep; central ink unchanged. All B geometry/contact results identical. No new bitmap.',
        'pending':'Actual normal-scale source/render comparison. Not facial ART acceptance.'}
dest.with_suffix('.edge-coverage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('BROW_EDGE_C',report['sha256'],checks)
