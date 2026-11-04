"""Mia project hooks: short read-only context and nonblocking evidence advice."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mia_pipeline import CACHE, STATE, advisory, context


def respond(event: dict) -> dict:
    # Only this Mia project with a production state, never global chat/user hooks.
    cwd = event.get('cwd')
    if not cwd:
        return {}
    result = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, timeout=3)
    if result.returncode:
        return {}
    root = Path(result.stdout.strip()).resolve()
    if not (root / STATE).is_file() or not (root / '.agents/skills/mia-reference-modeling/SKILL.md').is_file():
        return {}
    # Opt in per worktree with inspect --activate. Other overlay sessions stay quiet.
    if not (root / CACHE / 'active-review.json').is_file():
        return {}
    name = event.get('hook_event_name')
    if name in ('SessionStart', 'PostCompact'):
        data = context(root)
        # Keep a complete short JSON object, not a truncated large state dump.
        brief = {key: data.get(key) for key in (
            'canonical_worktree', 'skill', 'selected_static_wip',
            'character_complete', 'art_approved', 'read_first')}
        brief['face_status'] = str(data.get('face_status', ''))[:300]
        brief['body_status'] = str(data.get('active_body_status', ''))[:650]
        brief['execution_policy'] = (
            'Anatomical/fine shaping: live Blender MCP inspect-edit-image-review loop. '
            'Background: blockout candidates, reviewed deltas, checks, batch renders/bakes/export. '
            'Before local finish read skill references/local-refinement.md: mask/fix retained '
            'anatomical neighbors; explicit editable/interface IDs; scoped delta guard; '
            'actual immediate comparison and keep/restore before another part. '
            'Do not replay retired c9 torso carrier. Verify the actual scene at handoff. '
            'This advisory itself does not enforce tool use or prevent raw bpy bypass.')
        brief['next'] = ('Read the current stage plan linked by CURRENT_STATE; preserve accepted work. '
                         'Plan index includes rejected history. Review actual source/baseline/candidate images.')
        message = 'For Mia work only, resume index (not art approval): ' + json.dumps(brief, ensure_ascii=False)
        return {'hookSpecificOutput': {'hookEventName': name, 'additionalContext': message}}
    if name == 'Stop':
        result = advisory(root)
        if not result:
            return {}
        return {'systemMessage': 'Mia evidence advisory: ' + json.dumps(result, ensure_ascii=False)[:1400]}
    return {}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(json.dumps(respond(json.load(sys.stdin)), ensure_ascii=False))
    except Exception as exc:
        # Never loop, block a turn, change a model, or hide hook failure as a PASS.
        print(json.dumps({'systemMessage': 'Mia advisory hook could not inspect current evidence: '
                          + str(exc)[:350] + '. No acceptance decision was made.'}, ensure_ascii=False))
