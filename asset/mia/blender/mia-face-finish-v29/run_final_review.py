"""One GPU batch at a time; renderer overrides never save the reviewed native."""
import argparse
from pathlib import Path
import subprocess

P = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--native', required=True)
ap.add_argument('--sha256', required=True)
a = ap.parse_args()
blender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
for mode in ['source', 'critical', 'orbit', 'protection']:
    log = P / 'final-review' / (mode + '-runtime.log')
    log.parent.mkdir(exist_ok=True)
    print('START', mode, flush=True)
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([blender, '--background', '--python', str(P/'render_final_review.py'), '--',
            '--native', a.native, '--sha256', a.sha256, '--mode', mode], stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise SystemExit('Failed ' + mode + '; inspect ' + str(log))
    print('DONE', mode, flush=True)
