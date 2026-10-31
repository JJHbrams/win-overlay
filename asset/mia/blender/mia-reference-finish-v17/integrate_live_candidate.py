"""Integrate frozen face/hair inputs through the installed Blender MCP, then inspect live."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROMPT = """이제 원화에 맞춰서 얼굴/머리/헤어 메쉬 및 텍스쳐, UV 맵등을 수정해야겠네
헤어메쉬의 경우 일단은 pixal 에서 떼온 뭉탱이가 그나마 원화의 디테일을 살리니 그걸 기반으로 원화에 맞도록 머리쪽 모양을 두상과 같이 조정하고, 나중에 땋은머리/머리끝/헝클어진 부분 등에 본을 추가해서 부분적 모핑을 주는게 좋겠어
참고로 블렌더 열려있으니까 mcp 잘 써보렴
지금 열린거 상태보관안해도될건데? 테스트로 띄워준거 내가 그냥 뷰포인트 바꿔본정도야
원화대비 얼굴 너비는 너무 넓고, 눈동자는 너무 좁지않나?"""

p = argparse.ArgumentParser()
p.add_argument('--face-native', required=True)
p.add_argument('--face-sha', required=True)
p.add_argument('--hair-native', required=True)
p.add_argument('--hair-sha', required=True)
p.add_argument('--output-dir', required=True)
p.add_argument('--native-name', required=True)
p.add_argument('--expected-current-file', required=True)
a = p.parse_args()
out = Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
recipe = Path(__file__).with_name('integrate_hair_collection_v17.py').resolve()
argv = ['blender', '--', '--face-native', str(Path(a.face_native).resolve()),
        '--face-sha', a.face_sha, '--hair-native', str(Path(a.hair_native).resolve()),
        '--hair-sha', a.hair_sha, '--output-dir', str(out), '--native-name', a.native_name]

def text_of(result):
    return '\n'.join(b.text for b in result.content if b.type == 'text')

async def main():
    params = StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[],
        env=dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true'))
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            code = (
                "import bpy, sys, os\nfrom pathlib import Path\n"
                f"assert os.path.normcase(bpy.data.filepath) == os.path.normcase({str(Path(a.expected_current_file).resolve())!r}), 'Unexpected live scene; not replaced'\n"
                "previous_argv = sys.argv[:]\n"
                "try:\n"
                f"    sys.argv = {argv!r}\n"
                f"    exec(compile(Path({str(recipe)!r}).read_text(encoding='utf-8'), {str(recipe)!r}, 'exec'), {{'__name__': '__main__', '__file__': {str(recipe)!r}}})\n"
                "finally:\n    sys.argv = previous_argv\n"
                "for screen in bpy.data.screens:\n"
                "    for area in screen.areas:\n"
                "        if area.type == 'VIEW_3D':\n"
                "            area.spaces.active.region_3d.view_perspective = 'CAMERA'\n"
                "            area.spaces.active.shading.type = 'RENDERED'\n"
                "            area.spaces.active.overlay.show_overlays = False\n"
                "print('MCP_INTEGRATION_COMPLETE', bpy.data.filepath)\n"
            )
            result = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': PROMPT})
            response = text_of(result)
            (out / 'mcp-integration-response.json').write_text(json.dumps(result.model_dump(mode='json'), ensure_ascii=False, indent=2), encoding='utf-8')
            if result.isError or 'MCP_INTEGRATION_COMPLETE' not in response or 'Error executing code' in response:
                raise RuntimeError(response)
            native = out / a.native_name
            digest = hashlib.sha256(native.read_bytes()).hexdigest()
            capture = await session.call_tool('look', {'mode': 'angles',
                'target': ['MIA_V14_SculptedSkin', 'MIA_V17_PIXAL_DetailedHair'],
                'views': ['front', 'right', 'three_quarter'], 'shading': 'rendered',
                'max_size': 1600, 'user_prompt': PROMPT})
            if capture.isError or 'Error' in text_of(capture):
                raise RuntimeError(text_of(capture))
            pictures = []
            for index, block in enumerate(capture.content):
                if block.type == 'image':
                    path = out / f'live-integrated-{index}.png'
                    path.write_bytes(base64.b64decode(block.data))
                    pictures.append(str(path))
            assert pictures, 'MCP returned no preview image'
            assert hashlib.sha256(native.read_bytes()).hexdigest() == digest
            evidence = {'native': str(native), 'sha256': digest, 'pictures': pictures,
                        'transport': 'Installed mcp-for-blender via MCP Python SDK',
                        'saved_new_native': True, 'discard_test_view_authorized': True,
                        'expected_previous_scene': a.expected_current_file,
                        'source_validation': 'integration-manifest.json',
                        'art_approval': False}
            (out / 'live-integration-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(evidence, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
