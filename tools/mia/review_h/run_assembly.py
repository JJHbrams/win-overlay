"""Root-selected one H assembly and explicit body atlas entry points.

No automatic fitting, variations, scene save, or artistic acceptance.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['assemble', 'atlas'])
    parser.add_argument('--guide')
    parser.add_argument('--cut', type=float)
    parser.add_argument('--medial-limit', type=float, default=.085)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    out = ROOT/'.mia-cache/body-h/shape/assembly'
    if args.mode == 'atlas':
        import atlas_h
        atlas_h.export(out/'geometry.npz', out/'assembly.json', out/'atlas')
        return
    assert args.guide and args.cut is not None, 'Root must explicitly choose actual guide/cut'
    import assemble
    arrays, rows, report = assemble.assemble(
        Path(args.guide),
        cuts=assemble.CutSpec(guide_neck_z=args.cut,
                             medial_neck_halfwidth_limit_m=args.medial_limit),
        neck_guides=assemble.observed_neck_guides(),
    )
    assemble.export_assembly(arrays, rows, report, out)
    print('H_ASSEMBLY_EXPORTED_NOT_ART', json.dumps({
        'vertices': len(arrays['world']), 'triangles': len(arrays['triangles']),
        'output': str(out), 'cut': args.cut,
        'medial_limit': args.medial_limit,
    }), flush=True)


if __name__ == '__main__':
    main()
