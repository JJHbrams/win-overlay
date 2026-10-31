import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent/'mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend'
PROMPT = 'blender mcp 로 제어할 적에 카메라랑 광원도 같이 설정해서 보여주면 좋겠네.. 아니 근데 이거 좌표 축이 캐릭터 헤드 내지는 중심이나 발밑등이 중심 축이어야하는거 아니야???? 확대해보니까 모델이 이상하게 왜곡되는데 설마 지금까지 검증캡쳐할 떄 다 그런식으로 왜곡된걸 본건 아니지?'


async def main():
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true')
    records = []
    async with stdio_client(StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)) as (rd, wr):
        async with ClientSession(rd, wr) as session:
            await session.initialize()

            async def execute(code):
                result = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': PROMPT})
                text = '\n'.join(x.text for x in result.content if x.type == 'text')
                if result.isError or 'Error executing code' in text or 'Traceback' in text:
                    raise RuntimeError(text)
                return text

            async def capture(name, mode='viewport'):
                result = await session.call_tool('look', {'mode': mode, 'shading': 'rendered', 'max_size': 1200, 'user_prompt': PROMPT})
                if result.isError: raise RuntimeError(str(result))
                files = []
                for index, block in enumerate(result.content):
                    if block.type == 'image':
                        target = ROOT/(name+f'-{index}.png'); target.write_bytes(base64.b64decode(block.data)); files.append(str(target))
                if not files: raise RuntimeError('No actual MCP image returned')
                records.append({'name': name, 'mode': mode, 'files': files})

            await execute(f"import bpy,os; assert os.path.normcase(bpy.data.filepath)==os.path.normcase({str(SOURCE)!r}), 'Unexpected live file'")
            if not list(ROOT.glob('live-before-*.png')):
                await capture('live-before')
            await execute(f"exec(compile(open({str(ROOT/'configure_review_scene.py')!r}, encoding='utf-8').read(), 'configure_review_scene.py', 'exec'), {{'__name__':'__main__'}})")
            await capture('live-head-centred')
            module = f"import runpy; review=runpy.run_path({str(ROOT/'configure_review_scene.py')!r})\n"
            await execute(module + "review['focus']('head', distance=.4)")
            await capture('live-head-zoom')
            await execute(module + "review['focus']('head', 'LeftOblique', distance=.5)")
            await capture('live-head-oblique')
            await execute(module + "review['focus']('body')")
            await capture('live-body-centred')
            await execute(module + "review['focus']('head')")
            await capture('live-head-camera', 'camera')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha
    target = ROOT/'Mia_ReviewSetup_v22.blend'
    report = {'source': str(SOURCE), 'source_sha256_unchanged': source_sha, 'native': str(target),
              'native_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'captures': records,
              'no_geometry_or_origin_changes': True, 'global_preferences_changed': False}
    (ROOT/'live-mcp-evidence.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


asyncio.run(main())
