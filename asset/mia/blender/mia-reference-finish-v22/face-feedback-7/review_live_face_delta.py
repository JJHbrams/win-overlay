"""Replay one declared face delta through MCP, inspect, then restore the checkpoint.

This is a reversible live editing review, not a native promotion. The operation
requires the exact source Basis, returns achieved deltas and real viewport images,
and restores the exact cached mesh/key coordinates. No native is saved.
"""
import argparse, asyncio, base64, hashlib, json, os, shutil
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main(a):
    out = Path(a.output_dir).resolve()
    assert not out.exists(), 'Preserve existing live review'
    out.mkdir(parents=True)
    native, manifest_path, helper = map(lambda p: Path(p).resolve(),
        [a.expected_current, a.manifest, a.apply_helper])
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    delta_path = Path(manifest['exact_delta_file'])
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert sha(delta_path) == manifest['exact_delta_sha256']
    native_sha = sha(native)
    deps = out / 'dependencies'; deps.mkdir()
    for p in [Path(__file__), manifest_path, delta_path, helper]:
        shutil.copyfile(p, deps / p.name)
    focus = Path(__file__).resolve().parents[1] / 'configure_review_scene.py'
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true')
    async with stdio_client(StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)) as (rd, wr):
        async with ClientSession(rd, wr) as session:
            await session.initialize()
            async def execute(code):
                r = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': 'Mia 얼굴의 명시된 소규모 버텍스 보정 전후를 실제 Blender에서 확인하고 원상복구'})
                text = '\n'.join(b.text for b in r.content if b.type == 'text')
                if r.isError or 'Traceback' in text or 'Error executing code' in text:
                    raise RuntimeError(text)
                return text
            setup = f'''
import bpy,json,hashlib,ast,os,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector
assert os.path.normcase(bpy.data.filepath)==os.path.normcase({str(native)!r}), 'Unexpected live document'
assert not bpy.data.is_dirty, 'Unsaved user document'
assert bpy.context.mode=='OBJECT', 'Object mode required'
manifest=json.loads(Path({str(manifest_path)!r}).read_text())
rows=json.loads(Path({str(delta_path)!r}).read_text())
ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse(Path({str(helper)!r}).read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-apply-helper','exec'))
owner=bpy.data.objects[manifest['owner']]
assert not owner.hide_get() and not owner.hide_render, 'Target owner must be visible'
def evaluated_points(obj):
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();return p
assert len(owner.data.vertices)==manifest['vertex_count']
assert ah([tuple(v.co) for v in owner.data.shape_keys.key_blocks[0].data])==manifest['source_basis_sha256_float64']
assert all(abs(k.value)<1e-8 for k in owner.data.shape_keys.key_blocks[1:]), 'Neutral keys required'
assert len({{r['id'] for r in rows}})==len(rows)==manifest['changed_vertex_count']
for r in rows:
 assert r['owner']==owner.name
 assert np.max(np.abs(np.array(owner.data.shape_keys.key_blocks[0].data[r['id']].co)-r['before']))<1e-9
before=snapshots()
cached=np.array([tuple(v.co) for v in owner.data.vertices])
key_cached={{k.name:np.array([tuple(v.co) for v in k.data]) for k in owner.data.shape_keys.key_blocks}}
states={{o.name:o.hide_render for o in bpy.context.scene.objects}}
hide_states={{o.name:o.hide_get() for o in bpy.context.scene.objects}}
slot_states={{name:[s.material for s in bpy.data.objects[name].material_slots] for name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']}}
clay=bpy.data.materials.new('MIA_LIVE_DELTA_TEMP_MATTE');clay.use_nodes=True
n=clay.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfDiffuse');bs.inputs['Color'].default_value=(.18,.18,.18,1);output=n.new('ShaderNodeOutputMaterial');clay.node_tree.links.new(bs.outputs[0],output.inputs[0])
for name in slot_states:
 for slot in bpy.data.objects[name].material_slots:slot.material=clay
hair_members={{o.as_pointer() for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}}
for o in bpy.context.scene.objects:
 if o.as_pointer() in hair_members or any(t in o.name for t in ['Hair','HAIR','PIXAL','UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True;o.hide_set(True)
review=runpy.run_path({str(focus)!r})
bpy.app.driver_namespace['mia_live_delta_review']={{'before':before,'cached':cached,'key_cached':key_cached,'states':states,'hide_states':hide_states,'slots':slot_states,'clay':clay,'owner':owner,'rows':rows,'manifest':manifest,'snapshots':snapshots,'apply':apply,'review':review,'ah':ah,'evaluated_points':evaluated_points,'evaluated_before':evaluated_points(owner)}}
print(json.dumps({{'file':bpy.data.filepath,'mode':bpy.context.mode,'owner':owner.name,'changed_vertices':len(rows),'semantic_groups':manifest['semantic_groups'],'active_keys':{{k.name:k.value for k in owner.data.shape_keys.key_blocks[1:] if k.value}}}}))
'''
            receipt = {'before': await execute(setup), 'captures': []}
            async def captures(stage):
                for angle in ['Front', 'LeftOblique', 'RightOblique', 'Profile']:
                    await execute(f"import bpy;s=bpy.app.driver_namespace['mia_live_delta_review'];s['review']['focus']('head',{angle!r},distance=.42)")
                    r = await session.call_tool('look', {'mode': 'viewport', 'shading': 'rendered', 'max_size': 1000, 'user_prompt': '같은 머리 중심 정투영 시점의 얼굴 표면 확인'})
                    assert not r.isError
                    paths=[]
                    for i,b in enumerate(r.content):
                        if b.type=='image':
                            p=out/f'{stage}-{angle}-{i}.png';p.write_bytes(base64.b64decode(b.data));paths.append({'path':p.name,'sha256':sha(p)})
                    assert paths
                    receipt['captures'].append({'stage':stage,'angle':angle,'images':paths})
            try:
                await captures('before')
                receipt['achieved'] = await execute('''
import bpy,json
import numpy as np
from mathutils import Vector
s=bpy.app.driver_namespace['mia_live_delta_review'];o=s['owner'];ds=[Vector() for v in o.data.vertices]
for r in s['rows']:ds[r['id']]=Vector(r['delta'])
errors=s['apply'](o,ds);o.data.shape_keys.update_tag();o.update_tag(refresh={'DATA'});bpy.context.view_layer.update();bpy.context.scene.frame_set(bpy.context.scene.frame_current)
assert s['ah']([tuple(v.co) for v in o.data.shape_keys.key_blocks[0].data])==s['manifest']['candidate_basis_sha256_float64']
ed=s['evaluated_points'](o)-s['evaluated_before'];evmax=float(np.linalg.norm(ed,axis=1).max());assert evmax>1e-5, 'Evaluated surface did not update'
print(json.dumps({'changed_vertices':len(s['rows']),'achieved_max_delta_m':max(d.length for d in ds),'evaluated_max_delta_m':evmax,'candidate_basis_exact':True,'relative_key_errors':errors}))
''')
                await captures('after')
            finally:
                receipt['rollback'] = await execute('''
import bpy,json
s=bpy.app.driver_namespace['mia_live_delta_review'];o=s['owner']
for v,p in zip(o.data.vertices,s['cached']):v.co=p
for k in o.data.shape_keys.key_blocks:
 for v,p in zip(k.data,s['key_cached'][k.name]):v.co=p
o.data.update();o.data.shape_keys.update_tag();o.update_tag(refresh={'DATA'})
for name,slots in s['slots'].items():
 for slot,mat in zip(bpy.data.objects[name].material_slots,slots):slot.material=mat
for name,value in s['states'].items():bpy.data.objects[name].hide_render=value
for name,value in s['hide_states'].items():bpy.data.objects[name].hide_set(value)
bpy.data.materials.remove(s['clay']);bpy.context.view_layer.update()
assert s['snapshots']()==s['before'], 'Rollback mismatch; preserve live scene for inspection'
s['review']['focus']('head','Front',distance=.63)
print(json.dumps({'exact_geometry_keys_uv_material_slots_restored':True,'file':bpy.data.filepath,'dirty':bpy.data.is_dirty}))
del bpy.app.driver_namespace['mia_live_delta_review']
''')
            assert sha(native)==native_sha
            receipt.update(native=str(native),native_sha256=native_sha,native_unchanged=True,model_promoted=False)
            (out/'live-delta-review.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
            print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['expected-current','manifest','apply-helper','output-dir']:p.add_argument('--'+name,required=True)
    asyncio.run(main(p.parse_args()))
