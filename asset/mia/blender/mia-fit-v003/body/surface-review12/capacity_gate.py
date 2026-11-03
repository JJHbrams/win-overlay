"""Read-only capacity preflight; distinct from geometry and art acceptance."""
from pathlib import Path
import os, importlib.util, json

DEFAULT = Path(__file__).resolve().parents[6] / 'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py'

def check(reserve_mib):
    path = Path(os.environ.get('MIA_STORAGE_GUARD_PATH', str(DEFAULT)))
    if not path.is_file():
        raise RuntimeError('Required storage guard is missing: ' + str(path))
    spec = importlib.util.spec_from_file_location('mia12_capacity_guard', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.inspect(int(reserve_mib * 1024 * 1024))
    if result['violations']:
        raise RuntimeError('Storage capacity gate: ' + json.dumps(result))
    print('MIA12_CAPACITY_PREFLIGHT', json.dumps(result), flush=True)
    return result
