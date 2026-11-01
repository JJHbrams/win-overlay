"""Correct measured backward depth in outer lower-orbital support rows.

Reuse the immutable direct-edit/guard recipe, with explicit final positions
for the identified two support rows. No aperture edge, carrier or lash edit.
"""
import ast
from pathlib import Path
base=Path(__file__).resolve().parent.parent/'refinement-r26/build_transition_r26.py'
source=base.read_text()
source=source.replace("SOURCE=R25/'Mia_FaceFinish7_MalarVolumeR25_v22.blend'","SOURCE=R25/'refinement-r26/Mia_FaceFinish7_MalarTransitionR26_v22.blend'")
source=source.replace("Mia_FaceFinish7_MalarTransitionR26_v22.blend';assert", "Mia_FaceFinish7_OrbitalTransitionR27_v22.blend';assert")
tree=ast.parse(source)
targets={335:[48.30,55.70,1537.70],247:[48.60,56.40,1535.70],243:[51.60,53.30,1537.70],246:[51.20,53.35,1539.30],245:[53.45,51.70,1541.50],244:[54.00,51.20,1540.80],248:[44.80,59.10,1533.80],333:[44.10,58.80,1535.30],232:[54.10,48.00,1536.90],242:[48.10,57.10,1530.90]}
replacement=ast.parse("regions={'continuous_outer_orbital_outflow':{i:(np.array(target)-1000*P[i]).tolist() for i,target in "+repr(targets)+".items()}}").body[0]
for i,node in enumerate(tree.body):
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='regions' for t in node.targets):tree.body[i]=replacement
source=ast.unparse(ast.fix_missing_locations(tree))
# The outer lid is intentionally asymmetric by~0.8mm. Nearest positions
# confuse245/244 and246/243; the correspondence below is verified from
# identical rim-neighbor connectivity, not a nearest-coordinate guess.
correspondence={335:527,247:54,243:52,246:530,245:532,244:53,248:55,333:524,232:43,242:51}
source=source.replace('j = int(negative[np.argmin(np.linalg.norm(P[negative] - reflected, axis=1))])','j = '+repr(correspondence)+'[i]')
source=source.replace('vertex-deltas-from-r25.json','vertex-deltas-from-r26.json')
source=source.replace('Manual bounded R25 refinement, not a new fit or smoothing framework.','Manual final-position correction of measured outer lower-orbital depth backtrack; no fit or smoothing.')
source=source.replace('R25 restored apex depth retained; medial projection reduced by0.2..0.8mm, lateral depth support increased0.5..1.5mm.','R26 broad apex and buccal mass unchanged. Only two outer lower-orbital support rows changed; exact targets are embedded in this recipe.')
expanded=Path(__file__).with_name('expanded-recipe.py');expanded.write_text(source)
exec(compile(source,str(expanded),'exec'))
