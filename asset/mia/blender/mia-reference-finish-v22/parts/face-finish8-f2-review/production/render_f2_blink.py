from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT.parent/'finish-7/candidate-r25/refinement-r27/render_limited_blink.py').read_text().replace("Path(__file__).resolve().parents[2]/'render_source_motion.py'","Path(__file__).resolve().parent.parent/'finish-7/render_source_motion.py'")
exec(compile(code,str(__file__),'exec'))
