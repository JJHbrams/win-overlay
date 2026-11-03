"""Small standard MCP client for the configured official Blender Lab server.

The host's tool catalogue can retain a previous server's schema. This client
lists the live server schemas and calls those exact tools; bpy runs in the
user's live Blender, never in a background Blender process.
"""
from pathlib import Path
import argparse
import asyncio
import base64
from datetime import timedelta
import json
import os
import sys
import tomllib

sys.dont_write_bytecode = True
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[3]


def code_arguments(args):
    """MCP exec has no filename; make scoped scripts relocate like CLI scripts."""
    path = args.code_file.resolve()
    prefix = '__file__ = '+repr(str(path))+'\n'
    if args.view:
        prefix += 'MIA_VIEW_REQUEST = '+repr(args.view)+'\n'
    if args.phase:
        prefix += 'MIA_EDIT_PHASE = '+repr(args.phase)+'\n'
    return {'code': prefix+path.read_text(encoding='utf8')}


async def run(args):
    arguments = json.loads(args.arguments.read_text(encoding='utf8')) if args.arguments else {}
    if args.code_file:
        assert args.command == 'call' and args.tool == 'execute_blender_code'
        assert not args.arguments
        arguments = code_arguments(args)
    configured = tomllib.loads(Path('C:/Users/antio/.codex/config.toml').read_text(encoding='utf8'))['mcp_servers']['blender']
    expected = Path('C:/Users/antio/.codex/tools/blender-lab-mcp-venv/Scripts/python.exe')
    expected_args = ['-m', 'blmcp', '--transport', 'stdio']
    assert Path(configured['command']) == expected and configured.get('enabled', True)
    assert configured.get('args') == expected_args
    runtime_temp = Path('C:/Users/antio/.codex/tmp/mia-runtime')
    runtime_temp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, **configured.get('env', {}), PYTHONDONTWRITEBYTECODE='1',
               TEMP=str(runtime_temp), TMP=str(runtime_temp))
    params = StdioServerParameters(command=configured['command'], args=configured.get('args', []), env=env)
    report = args.report.resolve()
    allowed = [(ROOT/p).resolve() for p in ['.mia-cache/body-h/live', '.mia-cache/face-live/live', '.mia-cache/body-connected/live', '.mia-cache/eye-roi/live']]
    assert any(p == report.parent or p in report.parents for p in allowed)
    report.parent.mkdir(parents=True, exist_ok=True)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(seconds=args.timeout)) as session:
            init = await session.initialize()
            listing = await session.list_tools()
            schemas = {t.name: t.inputSchema for t in listing.tools}
            if args.command == 'list':
                result = dict(server_info=init.serverInfo.model_dump(mode='json'), tools=schemas)
            else:
                assert args.tool in schemas, ('Tool is not in official live server', args.tool)
                raw = await session.call_tool(args.tool, arguments)
                content = []
                for index, block in enumerate(raw.content):
                    if block.type == 'image':
                        extension = '.png' if block.mimeType == 'image/png' else '.jpg'
                        path = report.with_name(report.stem+'-'+str(index)+extension)
                        path.write_bytes(base64.b64decode(block.data))
                        content.append(dict(type='image', path=str(path), mime_type=block.mimeType))
                    else:
                        content.append(block.model_dump(mode='json'))
                result = dict(tool=args.tool, is_error=raw.isError,
                              structured=raw.structuredContent, content=content)
            report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
            if args.command == 'list':
                print(json.dumps(result, ensure_ascii=False), flush=True)
            else:
                summary = dict(tool=args.tool, is_error=result['is_error'], report=str(report),
                               structured_status=(result['structured'] or {}).get('status'),
                               stdout_preview=(result['structured'] or {}).get('stdout', '')[:1800],
                               images=[b['path'] for b in content if b.get('type') == 'image'])
                if result['is_error'] or summary['structured_status'] not in (None, 'ok'):
                    summary['error_content'] = content
                print(json.dumps(summary, ensure_ascii=False)[:7000], flush=True)
                if result['is_error'] or summary['structured_status'] not in (None, 'ok'):
                    raise RuntimeError('Official MCP call failed; inspect '+str(report))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['list', 'call'])
    parser.add_argument('--tool')
    parser.add_argument('--arguments', type=Path)
    parser.add_argument('--code-file', type=Path)
    parser.add_argument('--view', choices=['front', 'profile', 'back', 'oblique', 'high', 'low', 'mask_before', 'profile_after'])
    parser.add_argument('--phase', choices=['select', 'apply'])
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=120)
    asyncio.run(run(parser.parse_args()))


if __name__ == '__main__': main()
