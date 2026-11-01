from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'verify_replay.py').read_text().replace('look-d/handoff/owner-key-replay-from-r28.json','shape-f2/handoff/owner-key-replay-from-d.json').replace('replay_into_r28.py','replay_f2_into_d.py')
exec(compile(code,str(__file__),'exec'))
