"""Rollback entry for the source-guided rooted rear correction."""
from pathlib import Path
MIA_CURVED_REAR_KEY='MIA_CurvedRear03'
path=Path(__file__).with_name('restore_curved_rear.py')
exec(compile(path.read_text(),str(path),'exec'),globals())
