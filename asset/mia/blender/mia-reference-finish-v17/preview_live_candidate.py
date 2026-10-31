"""Open an explicitly selected Mia copy in live Blender and capture actual MCP views; never save."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from inspect_live_blender import PROMPT

parser = argparse.ArgumentParser()
parser.add_argument('--native', required=True)
parser.add_argument('--output-dir', required=True)
parser.add_argument('--expected-current-file', default='')
parser.add_argument('--discard-authorized-test-view', action='store_true')
args = parser.parse_args()
native = Path(args.native).resolve()
out = Path(args.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
before = hashlib.sha256(native.read_bytes()).hexdigest()

async def preview():
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true')
    params = StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            code = (
                "import bpy, os\n"
                f"expected={args.expected_current_file!r}\n"
                f"assert not bpy.data.is_dirty or {args.discard_authorized_test_view!r}, 'Live Blender contains unsaved changes'\n"
                "assert os.path.normcase(bpy.data.filepath)==os.path.normcase(expected), 'Live Blender file changed'\n"
                f"bpy.ops.wm.open_mainfile(filepath={str(native)!r}, load_ui=False, use_scripts=False)\n"
                "for screen in bpy.data.screens:\n"
                "    for area in screen.areas:\n"
                "        if area.type == 'VIEW_3D':\n"
                "            space = area.spaces.active\n"
                "            space.region_3d.view_perspective = 'CAMERA'\n"
                "            space.region_3d.view_camera_zoom = 0\n"
                "            space.shading.type = 'RENDERED'\n"
                "            space.overlay.show_overlays = False\n"
                "print('OPENED_FOR_REVIEW', bpy.data.filepath)\n"
            )
            opened = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': PROMPT})
            open_text = '\n'.join(block.text for block in opened.content if block.type == 'text')
            if opened.isError or 'OPENED_FOR_REVIEW' not in open_text or 'Error executing code' in open_text:
                (out / 'open-rejected.json').write_text(json.dumps({
                    'requested_native': str(native), 'requested_sha': before,
                    'status': 'OPEN_REJECTED', 'response': opened.model_dump(mode='json'),
                    'note': 'No look call made; existing live scene retained. Tool may encode execution failure as text with isError=false.'
                }, ensure_ascii=False, indent=2), encoding='utf-8')
                raise RuntimeError(str(opened))
            state = await session.call_tool('get_scene_info', {'fields': ['settings', 'hidden'], 'query': 'MIA_V17', 'limit': 8, 'user_prompt': PROMPT})
            result = await session.call_tool('look', {
                'mode': 'angles', 'target': ['MIA_V14_SculptedSkin', 'MIA_V17_PIXAL_DetailedHair'],
                'views': ['front', 'right', 'three_quarter'], 'shading': 'rendered',
                'max_size': 1600, 'user_prompt': PROMPT
            })
            if result.isError:
                raise RuntimeError(str(result))
            pictures = []
            for i, block in enumerate(result.content):
                if block.type == 'image':
                    path = out / f'live-blender-views-{i}.png'
                    path.write_bytes(base64.b64decode(block.data))
                    pictures.append(str(path))
            report = {'native': str(native), 'sha_before': before,
                      'sha_after': hashlib.sha256(native.read_bytes()).hexdigest(),
                      'opened': opened.model_dump(mode='json'), 'scene': state.model_dump(mode='json'),
                      'pictures': pictures, 'native_saved': False,
                      'transport': 'Installed local MCP server via SDK; native Codex tool catalog not yet refreshed'}
            assert report['sha_before'] == report['sha_after']
            (out / 'live-preview-evidence.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({'sha': before, 'pictures': pictures}, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(preview())
