"""Only the newly requested smile pair; does not rerender previous eight."""
from pathlib import Path
MIA_BROW_DIAGNOSTIC_TAG = 'brow-smile1'
MIA_BROW_DIAGNOSTIC_STATES = [('smile', 'P16_gentle_smile')]
path = Path(__file__).with_name('capture_brow_expressions.py')
exec(compile(path.read_text(encoding='utf8'), str(path), 'exec'))
