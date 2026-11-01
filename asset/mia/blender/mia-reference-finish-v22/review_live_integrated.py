"""Open a reviewed WIP via the actual Blender MCP and capture its navigation.

No native is saved and no geometry, material, origin or user preference is edited.
An expected-current-file guard prevents replacing an unrelated live document.
"""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent
PROMPT = 'Mia 원화 비교용 통합 WIP를 실제 Blender에서 head/body 중심 정투영 카메라와 조명으로 확인'


async def main(args):
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876',
               BLENDER_MCP_DISABLE_TELEMETRY='true')
    async with stdio_client(StdioServerParameters(
            command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)) as (rd, wr):
        async with ClientSession(rd, wr) as session:
            await session.initialize()

            async def execute(code):
                result = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': PROMPT})
                value = '\n'.join(b.text for b in result.content if b.type == 'text')
                if result.isError or 'Traceback' in value or 'Error executing code' in value:
                    raise RuntimeError(value)
                return value

            state = await execute("import bpy,json; print(json.dumps({'path':bpy.data.filepath,'dirty':bpy.data.is_dirty,'scene':bpy.context.scene.name}))")
            if args.inspect:
                print(state)
                return
            assert args.candidate and args.expected_current and args.output_dir
            native = Path(args.candidate).resolve()
            original_hash = hashlib.sha256(native.read_bytes()).hexdigest()
            output = Path(args.output_dir).resolve()
            output.mkdir(parents=True, exist_ok=True)
            assert not (output/'live-review.json').exists(), 'Preserve previous review'
            expected = str(Path(args.expected_current).resolve())
            await execute(f"import bpy,os; assert os.path.normcase(os.path.normpath(bpy.data.filepath)) == os.path.normcase(os.path.normpath({expected!r})), 'Unexpected live file'; assert not bpy.data.is_dirty, 'Unsaved live document'; bpy.ops.wm.open_mainfile(filepath={str(native)!r},use_scripts=False)")
            prefix = f"import runpy; review=runpy.run_path({str(HERE/'configure_review_scene.py')!r})\n"
            captures = []
            for name, region, angle, distance in [
                ('head-front', 'head', 'Front', .63),
                ('head-left-oblique', 'head', 'LeftOblique', .63),
                ('head-right-oblique', 'head', 'RightOblique', .63),
                ('head-profile', 'head', 'Profile', .63),
                ('head-zoom', 'head', 'Front', .4),
                ('body-front', 'body', 'Front', 2.7)]:
                owner = args.face_owner if region == 'head' else args.body_owner
                await execute(prefix+f"review['focus']({region!r},{angle!r},distance={distance!r},owner_name={owner!r})")
                result = await session.call_tool('look', {'mode': 'viewport', 'shading': 'rendered', 'max_size': 1200, 'user_prompt': PROMPT})
                if result.isError:
                    raise RuntimeError(str(result))
                paths = []
                for i, block in enumerate(result.content):
                    if block.type == 'image':
                        path = output/f'{name}-{i}.png'
                        path.write_bytes(base64.b64decode(block.data))
                        paths.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
                assert paths, 'MCP returned no actual viewport image'
                captures.append({'name':name,'focus':region,'angle':angle,'distance':distance,'images':paths})
            await execute(prefix+f"review['focus']('head','Front',distance=.63,owner_name={args.face_owner!r})")
            audit = await execute("import bpy,json; print(json.dumps({'path':bpy.data.filepath,'camera':bpy.context.scene.camera.name,'projection':bpy.context.scene.camera.data.type,'viewports':[{'center':list(s.region_3d.view_location),'distance':s.region_3d.view_distance,'projection':s.region_3d.view_perspective} for a in bpy.context.screen.areas if a.type=='VIEW_3D' for s in a.spaces if s.type=='VIEW_3D']}))")
            assert hashlib.sha256(native.read_bytes()).hexdigest() == original_hash
            report={'native':str(native),'sha256':original_hash,'native_unchanged':True,
                    'before':state,'after':audit,'captures':captures,'face_owner':args.face_owner,'body_owner':args.body_owner,
                    'focus_helper_sha256':hashlib.sha256((HERE/'configure_review_scene.py').read_bytes()).hexdigest(),
                    'scope':'Actual MCP viewport navigation only; no native saved. Freestyle render ink is not visible here.'}
            (output/'live-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(json.dumps(report,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inspect',action='store_true')
    p.add_argument('--candidate')
    p.add_argument('--expected-current')
    p.add_argument('--output-dir')
    p.add_argument('--face-owner',help='Explicit visible replacement face owner; omit for historical v14 files')
    p.add_argument('--body-owner',help='Explicit visible replacement body owner; omit for historical v06 files')
    asyncio.run(main(p.parse_args()))
