"""One explicit connected medial-cheek support edit on frozen R27.

Actual high-angle cage joins informed these final positions. Outer malar
apex, aperture, lash, nose center, jaw and chin are not edited. No smoothing.
"""
import ast
from pathlib import Path
H=Path(__file__).resolve().parent.parent;base=H/'candidate-r25/refinement-r26/build_transition_r26.py';source=base.read_text()
source=source.replace("R25=OUT.parent;H=R25.parent;SOURCE=R25/'Mia_FaceFinish7_MalarVolumeR25_v22.blend'","H=OUT.parent;R25=H/'candidate-r25';SOURCE=R25/'refinement-r27/Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'")
source=source.replace("Mia_FaceFinish7_MalarTransitionR26_v22.blend';assert","Mia_FaceFinish7_MedialTransitionR28_v22.blend';assert")
targets={307:[8.12,74.0,1531.0],310:[18.7,70.5,1531.9],309:[15.06,70.45,1535.4],319:[20.65,68.15,1535.0],322:[25.5,67.25,1533.7],323:[24.6,69.1,1530.9],324:[19.2,72.3,1526.1],253:[30.3,67.4,1530.8],252:[28.7,68.7,1525.1],258:[26.9,69.35,1519.7],295:[17.6,73.0,1521.5],294:[24.5,69.35,1512.3],254:[34.65,64.8,1518.8],292:[30.5,63.9,1510.0],296:[15.1,74.7,1516.1],301:[7.8,76.4,1523.2]}
mapping={307:137,310:138,309:136,319:515,322:516,323:154,324:153,253:60,252:59,258:147,295:146,294:144,254:148,292:31,296:141,301:139}
tree=ast.parse(source);replacement=ast.parse("regions={'medial_connected_tangent_support':{i:(np.array(target)-1000*P[i]).tolist() for i,target in "+repr(targets)+".items()}}").body[0]
for i,n in enumerate(tree.body):
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='regions' for t in n.targets):tree.body[i]=replacement
source=ast.unparse(ast.fix_missing_locations(tree));source=source.replace('j = int(negative[np.argmin(np.linalg.norm(P[negative] - reflected, axis=1))])','j = '+repr(mapping)+'[i]')
source=source.replace('edge_counts = Counter(',"assert np.max(abs(delta[[249,236,233,234,242,247,248,250,251]]))==0\nassert np.linalg.norm(delta,axis=1).max()<.0026\nedge_counts = Counter(")
source=source.replace('vertex-deltas-from-r25.json','vertex-deltas-from-r27.json').replace('Manual bounded R25 refinement, not a new fit or smoothing framework.','One manual connected medial-cheek support iteration from R27; no fitting or smoothing operation.').replace('R25 restored apex depth retained; medial projection reduced by0.2..0.8mm, lateral depth support increased0.5..1.5mm.','R27 outer apex positions are exact. Compressed medial rows redistributed by maximum2.6mm; full-face/continuity acceptance is not guaranteed.')
expanded=Path(__file__).with_name('expanded-recipe.py');expanded.write_text(source);exec(compile(source,str(expanded),'exec'))
