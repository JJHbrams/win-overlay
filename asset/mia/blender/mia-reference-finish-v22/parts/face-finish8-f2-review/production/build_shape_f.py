"""One meaningful central-buccal support correction on frozen E/D appearance."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'build_shape_e.py').read_text().replace("OUT=ROOT/'shape-e'","OUT=ROOT/'shape-f'").replace("SOURCE=ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend'","SOURCE=ROOT/'shape-e/Mia_FaceFinish8_ConnectedCheekE.blend'").replace('Mia_FaceFinish8_ConnectedCheekE.blend\';assert','Mia_FaceFinish8_CentralBuccalF.blend\';assert')
targets={254:66.5,255:64.2,258:70.0,294:71.0,296:76.2,297:73.5,298:76.8,290:64.5,291:58.2,292:68.5,293:69.0,276:55.5,278:63.0,265:40.0,266:45.5,277:56.0,279:62.0,282:58.0,283:64.0,431:68.5,433:69.0,302:74.0,436:73.0,434:65.5,426:69.0}
start=code.index("rows={'lateral_malar_turn'");end=code.index('\nmapping=',start)
code=code[:start]+"targets_y_mm="+repr(targets)+"\nrows={'connected_central_buccal_final_depth':{i:target-1000*p[i,1] for i,target in targets_y_mm.items()}}"+code[end:]
code=code.replace("delta[abs(p[:,0])<.020]","delta[abs(p[:,0])<.012]").replace('[236,242,247,248,249,250,251,252,253,254,258]','[236,242,247,248,249,250,251,252,253]')
code=code.replace('vertex-deltas-from-d.json','vertex-deltas-from-e.json').replace('ONE BOUNDED E CANDIDATE','ONE CENTRAL BUCCAL F CANDIDATE').replace('SHAPE_E_DONE','SHAPE_F_DONE')
code=code.replace('lateral sheet retreat is reduced by broad connected support.','central buccal retreat from high malar toward mouth/lower-cheek is reduced using explicit final-depth rows. E lateral support retained separately.')
code=code.replace('One connected lateral-cheek/upper-jaw section correction from frozen D.','One connected CENTRAL buccal final-depth correction from frozen E.')
(ROOT/'shape-f/expanded-build-recipe.py').write_text(code);exec(compile(code,str(ROOT/'shape-f/expanded-build-recipe.py'),'exec'))
