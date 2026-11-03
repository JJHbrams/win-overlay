"""Restore the rejected collar01 actual study; preserve unrelated live work."""
from pathlib import Path
MIA_EDIT_PHASE = 'restore'
path = Path('D:/MiaWorkCache/mia-reference-work/win-overlay/tools/mia/review_h/live_collar_sculpt.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
