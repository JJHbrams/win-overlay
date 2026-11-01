from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'compose_e_source.py').read_text().replace('shape-e','shape-f2').replace('BOUNDED E / WORKING CANDIDATE','CONNECTED F2 / REVIEW ONLY').replace('One connected lateral-cheek/upper-jaw support change, no chin or eye edit. Anterior high malar mass and D pigment retained; lateral retreat reduced without changing X/Z or outer boundary. Continuous surface and source silhouette remain independently unapproved.','Central/anterior buccal volume recovered and connected to lateral cheek support; D high malar, chin, eye aperture and pigment retained. Upper under-eye diagonal band persists. Local volume recovery accepted for review only; AC-SURFACE and whole character remain unapproved.')
exec(compile(code,str(__file__),'exec'))
