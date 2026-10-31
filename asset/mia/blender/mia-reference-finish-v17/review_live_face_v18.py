"""Inspect live facial geometry through Blender MCP; restore hair visibility, never save."""
import asyncio
import base64
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROMPT = '''사선으로 봤을 떄 눈-괄대-볼 구간 얼굴윤곽이 좀 부자연스럽지 않나? 또한 뭔가 전체적으로 얼굴이 원화대비 넓대대한거같은데
컨셉뷰 상 사선뷰가 부족하면 상단 사선등 더 다양한 뷰에서의 아트가 필요한가?
그리고 머리 윗부분 두상이 너무 낮지않아? 일반적으로 이정도 메쉬를 사용하나? 
헤어의 경우 대부분의 경우 앞머리/뒷머리/본체 이런식으로 나눠서 클리핑이나 볼륨, 리깅 등을 효율적으로 처리하는 것 같던데.
부가적으로 현재 속옷컨셉아트가 asset 에 없는데, 컨셉아트, 표정 등 원화랑 같이 보관되어야되는거 아니니'''
OUT = Path(__file__).with_name('live-face-v18')
OUT.mkdir(exist_ok=True)

async def main():
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true')
    params = StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            async def execute(code):
                reply = await session.call_tool('execute_blender_code', {'code': code, 'user_prompt': PROMPT})
                text = '\n'.join(b.text for b in reply.content if b.type == 'text')
                if reply.isError or 'Error executing code' in text:
                    raise RuntimeError(text)
                return text
            state = await execute("import bpy,json; o=bpy.data.objects['MIA_V14_SculptedSkin']; print(json.dumps({'file':bpy.data.filepath,'dirty':bpy.data.is_dirty,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'modifiers':[(m.name,m.type) for m in o.modifiers]}))")
            await execute("import bpy; c=bpy.data.collections['MIA_V17_PIXAL_HAIR']; bpy.app.driver_namespace['MIA_V18_REVIEW_HIDDEN']={o.name:o.hide_get() for o in c.all_objects}; [o.hide_set(True) for o in c.all_objects]; print('HAIR_HIDDEN_FOR_REVIEW')")
            images = []
            try:
                for shading in ['solid', 'wireframe']:
                    result = await session.call_tool('look', {
                        'mode': 'angles', 'target': ['MIA_V14_SculptedSkin'],
                        'views': ['front', [1, -1, 0], [1, -1, .55], [1, -1, 1]],
                        'shading': shading, 'max_size': 1600, 'user_prompt': PROMPT
                    })
                    if result.isError:
                        raise RuntimeError(str(result))
                    for i, block in enumerate(result.content):
                        if block.type == 'image':
                            path = OUT / f'live-head-{shading}-{i}.png'
                            path.write_bytes(base64.b64decode(block.data))
                            images.append(str(path))
            finally:
                restored = await execute("import bpy; states=bpy.app.driver_namespace.pop('MIA_V18_REVIEW_HIDDEN',{}); [bpy.data.objects[n].hide_set(v) for n,v in states.items() if n in bpy.data.objects]; print('HAIR_VISIBILITY_RESTORED',len(states))")
            (OUT / 'evidence.json').write_text(json.dumps({'state': state, 'restore': restored, 'images': images, 'native_saved': False}, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({'images': images}, ensure_ascii=False))

asyncio.run(main())
