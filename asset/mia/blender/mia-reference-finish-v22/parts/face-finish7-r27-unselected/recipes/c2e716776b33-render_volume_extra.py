"""Read-only upper/lower-angle continuity check after initial volume views."""
from pathlib import Path
p=Path(__file__).with_name('render_volume.py')
recipe=p.read_text().replace("[(0,0),(0,-10),(30,0),(-30,0),(30,-10),(-30,-10),(60,0),(-60,0),(90,0)]","[(60,-10),(-60,-10),(30,10),(-30,10),(60,10),(-60,10)]")
exec(compile(recipe,str(p),'exec'))
