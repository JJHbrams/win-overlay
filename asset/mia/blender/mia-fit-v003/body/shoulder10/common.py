"""One bounded Z-only map and read-only geometry helpers. No scene access."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
BASE = P.parent / 'posterior-union09'
CAN = Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
SOURCE = CAN / 'references/body-foundation/v06/mia-body-visibility-guide-v06.png'
NATIVE09 = BASE / 'native/Mia_PosteriorUnion09_STATIC_ShapeGuide.blend'
NATIVE10 = P / 'native/Mia_Shoulder10_STATIC_ShapeGuide.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
write = lambda p, d: Path(p).write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8', newline='\n')
spec = importlib.util.spec_from_file_location('shoulder10_readonly_geometry', P.parent / 'posterior-continuity08/geometry.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def S(t):
    t = np.clip(t, 0., 1.)
    return t*t*t*(10. - 15.*t + 6.*t*t)

def dS(t):
    t = np.clip(t, 0., 1.)
    return 30.*t*t*(1.-t)*(1.-t)

def factors(points):
    x = np.abs(points[:, 0]); z = points[:, 2]
    wx = S((x-.025)/.040) * (1.-S((x-.150)/.045))
    low = z <= 1.445
    bz = np.where(low, S((z-1.360)/.085), 1.-S((z-1.445)/.020))
    db = np.where(low, dS((z-1.360)/.085)/.085, -dS((z-1.445)/.020)/.020)
    dw = np.sign(points[:, 0]) * (dS((x-.025)/.040)/.040 * (1.-S((x-.150)/.045)) - S((x-.025)/.040)*dS((x-.150)/.045)/.045)
    return wx, bz, dw, db

def mapping(points, amplitude=.032):
    wx, bz, _, _ = factors(points)
    q = points.copy()
    active = (wx*bz) > 0
    q[active, 2] = points[active, 2] - amplitude*wx[active]*bz[active]
    return q

def jacobians(points, amplitude=.032):
    wx, bz, dw, db = factors(points)
    J = np.broadcast_to(np.eye(3), (len(points), 3, 3)).copy()
    J[:, 2, 0] = -amplitude*dw*bz
    J[:, 2, 2] = 1.-amplitude*wx*db
    return J

def edges(f):
    return np.unique(np.sort(np.concatenate([f[:, [0,1]], f[:, [1,2]], f[:, [2,0]]]), axis=1), axis=0)

def projected_roof(v, e, x):
    """Exact upper envelope of the piecewise-linear front/back projection."""
    a = v[e[:, 0]].astype(float); b = v[e[:, 1]].astype(float)
    take = (np.minimum(a[:, 0], b[:, 0]) <= x) & (np.maximum(a[:, 0], b[:, 0]) >= x) & (abs(b[:, 0]-a[:, 0]) > 1e-12)
    ids = np.flatnonzero(take)
    t = (x-a[ids, 0])/(b[ids, 0]-a[ids, 0])
    q = a[ids] + t[:, None]*(b[ids]-a[ids])
    return q[np.argmax(q[:, 2])]
