"""One semantic visibility diagnostic: unchanged03 curves over the intact base."""
from pathlib import Path
MIA_CURVED_REAR_FOLDER='D:/MiaWorkCache/mia-reference-work/win-overlay/.mia-cache/face-live/curved-rear03'
MIA_CURVED_REAR_KEY='MIA_CurvedRear03Base'
MIA_CURVED_REAR_ACTOR_PREFIX='MIA_Hair_CurvedRear03Base'
MIA_CURVED_REAR_KEEP_BASE=True
path=Path('D:/MiaWorkCache/mia-reference-work/face-live-author/tools/mia/face_surface_live/curved_rear_live.py')
exec(compile(path.read_text(),str(path),'exec'),globals())
