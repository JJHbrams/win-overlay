"""Rollback the intact-base visibility diagnostic only."""
from pathlib import Path
MIA_CURVED_REAR_KEY='MIA_CurvedRear03Base'
path=Path(__file__).with_name('restore_curved_rear.py')
exec(compile(path.read_text(),str(path),'exec'),globals())
