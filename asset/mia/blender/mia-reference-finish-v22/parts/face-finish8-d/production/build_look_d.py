from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'build_look_a.py').read_text().replace("'look-a'","'look-d'").replace('AuthoredLookA','AuthoredLookD').replace('LOOK_A_DONE','LOOK_D_DONE')
(ROOT/'build_look_d_expanded.py').write_text(code);exec(compile(code,str(ROOT/'build_look_d_expanded.py'),'exec'))
