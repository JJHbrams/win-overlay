from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'compose_e_pairs.py').read_text().replace("parent/'shape-e'","parent/'shape-f2'").replace("ROOT/'baseline-d/render-records.json'","ROOT.parent/'shape-e/baseline-d/render-records.json'").replace('BOUNDED E / ART UNAPPROVED','CONNECTED F2 / ART UNAPPROVED').replace("+'-d-e.png'","+'-d-f2.png'").replace('E_PAIRS_DONE','F2_PAIRS_DONE')
exec(compile(code,str(__file__),'exec'))
