"""Restore the rejected collar01 actual study; preserve unrelated live work."""
from pathlib import Path
MIA_EDIT_PHASE = 'restore'
path = Path(__file__).with_name('live_collar_sculpt.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
