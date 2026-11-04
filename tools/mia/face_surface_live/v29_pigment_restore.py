"""Explicit live MCP rollback for v29_pigment_current; import is inert.

runpy.run_path(path, init_globals={'MIA_V29_PIGMENT_PHASE': 'restore'})
Restores the original RemainingMain data/slots only if no later edits occurred.
"""
from pathlib import Path
import json
import runpy


def restore(root=None):
    helper = runpy.run_path(str(Path(__file__).with_name('v29_pigment_current.py')))
    return helper['restore'](root)


if globals().get('MIA_V29_PIGMENT_PHASE') == 'restore':
    print(json.dumps(restore(globals().get('MIA_ROOT'))))
