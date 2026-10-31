"""Read-only live Blender MCP state, using the side task's installed local server."""
import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROMPT = '이제 원화에 맞춰서 얼굴/머리/헤어 메쉬 및 텍스쳐, UV 맵등을 수정해야겠네\n헤어메쉬의 경우 일단은 pixal 에서 떼온 뭉탱이가 그나마 원화의 디테일을 살리니 그걸 기반으로 원화에 맞도록 머리쪽 모양을 두상과 같이 조정하고, 나중에 땋은머리/머리끝/헝클어진 부분 등에 본을 추가해서 부분적 모핑을 주는게 좋겠어'

async def main():
    env = dict(os.environ, BLENDER_HOST='127.0.0.1', BLENDER_PORT='9876', BLENDER_MCP_DISABLE_TELEMETRY='true')
    params = StdioServerParameters(command='C:/Users/antio/.local/bin/mcp-for-blender.exe', args=[], env=env)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = {}
            for name, args in [
                ('get_addon_status', {}),
                ('get_scene_info', {'fields': ['settings', 'hidden', 'details'], 'limit': 6, 'user_prompt': PROMPT}),
                ('execute_blender_code', {'code': "import bpy, json; print(json.dumps({'file':bpy.data.filepath,'dirty':bpy.data.is_dirty,'objects':[o.name for o in bpy.context.scene.objects]}))", 'user_prompt': PROMPT})
            ]:
                reply = await session.call_tool(name, args)
                result[name] = reply.model_dump(mode='json')
                if reply.isError:
                    raise RuntimeError(str(reply))
            path = Path(__file__).with_name('live-mcp-state.json')
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
