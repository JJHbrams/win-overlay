"""Use the cap height chart, not individual rays, in the shared live helper."""
from pathlib import Path
MIA_CAP_DIRECTION = 'chart'
path = Path('D:/MiaWorkCache/mia-reference-work/win-overlay/tools/mia/review_h/live_cap_form.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
