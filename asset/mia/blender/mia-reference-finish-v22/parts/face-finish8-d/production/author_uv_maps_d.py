"""One line-only contrast refinement. C pigment/fatigue unchanged."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'author_uv_maps_c_expanded.py').read_text().replace("'look-c/maps'","'look-d/maps'").replace('np.maximum(ink,.48*line)','np.maximum(ink,.82*line)')
(ROOT/'author_uv_maps_d_expanded.py').write_text(code);exec(compile(code,str(ROOT/'author_uv_maps_d_expanded.py'),'exec'))
