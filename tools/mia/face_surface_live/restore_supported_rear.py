"""Rollback the intact-base visibility diagnostic only."""
from pathlib import Path
MIA_CURVED_REAR_KEY='MIA_CurvedRear03Base'
path=Path('D:/MiaWorkCache/mia-reference-work/face-live-author/tools/mia/face_surface_live/restore_curved_rear.py')
exec(compile(path.read_text(),str(path),'exec'),globals())
