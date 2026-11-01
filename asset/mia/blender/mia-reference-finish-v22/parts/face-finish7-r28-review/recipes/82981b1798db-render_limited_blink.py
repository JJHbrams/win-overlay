from pathlib import Path
base=Path(__file__).resolve().parent.parent/'candidate-r25/refinement-r27/render_limited_blink.py'
source=base.read_text().replace("Path(__file__).resolve().parents[2]/'render_source_motion.py'","Path(__file__).resolve().parents[1]/'render_source_motion.py'")
exec(compile(source,str(base),'exec'))
