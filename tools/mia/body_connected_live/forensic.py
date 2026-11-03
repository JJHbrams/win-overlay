"""CPU diagnosis of the already rejected immutable charted proposal; no new case."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');CACHE=ROOT/'.mia-cache/body-connected'
path=CACHE/'charted-design.npz'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='615278e7e1f8549558cc702c6fd656e42220e60d26748f785acc0edd2a54d0d7'
d=dict(np.load(path));q=d['world'];old=d['original_control_id'];mapping={int(v):i for i,v in enumerate(old)if v>=0}
def center(j):
 if j==0:return mapping[979]
 if j==28:return mapping[26]
 if j<3:return 3799+(j-1)*13+6
 return 3825+(j-3)*15+7
def row(j):return dict(row=j,control=center(j),world=q[center(j)].tolist())
def step(a,b):return dict(rows=[a,b],delta_mm=((q[center(b)]-q[center(a)])*1000).tolist(),length_mm=float(np.linalg.norm(q[center(b)]-q[center(a)])*1000))
offset=np.r_[0,np.cumsum(d['polygon_sizes'])];edges={}
for fi in np.flatnonzero(d['original_face_id']<0):
 ids=d['loop_vertices'][offset[fi]:offset[fi+1]]
 for a,b in zip(ids,np.roll(ids,-1)):
  key=tuple(sorted((int(a),int(b))));edges.setdefault(key,[]).append(int(fi))
longest=sorted(edges,key=lambda e:np.linalg.norm(q[e[0]]-q[e[1]]),reverse=True)[:6]
def face_metrics(fi):
 ids=d['loop_vertices'][offset[fi]:offset[fi+1]];p=q[ids].astype(float)
 n1=np.cross(p[1]-p[0],p[2]-p[0]);result=dict(face=fi,controls=ids.tolist(),world=p.tolist(),triangle1_cross=n1.tolist(),
  triangle1_projected_XZ_jacobian=float(-n1[1]))
 if len(ids)==4:
  n2=np.cross(p[2]-p[0],p[3]-p[0]);result.update(triangle2_cross=n2.tolist(),triangle2_projected_XZ_jacobian=float(-n2[1]),
   within_quad_triangle_normal_cosine=float(n1@n2/max(np.linalg.norm(n1)*np.linalg.norm(n2),1e-30)))
 return result
quad_bow=[]
for fi in np.flatnonzero(d['original_face_id']<0):
 if d['polygon_sizes'][fi]!=4:continue
 metric=face_metrics(int(fi))
 if metric['within_quad_triangle_normal_cosine']<0:quad_bow.append(metric)
report=dict(scope='CPU code-level forensic of rejected same immutable charted candidate; no new coordinates or parameter case',
 payload_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
 actual_evidence=str(CACHE/'live/charted-front-0.png'),
 causes=[
  dict(id='boundary_parameter_mismatch',code='design.py sample(top,u)/sample(bottom,u) versus direct top/bottom row indices',
   mechanism='Interior Coons samples boundary by arc length, but terminal rows use original discrete index at i/n. These parameterizations differ greatly on the nonuniform neck+shoulder rail.',
   example=dict(interior_control=4197,interior_world=q[4197].tolist(),terminal_control=mapping[10],terminal_world=q[mapping[10]].tolist(),
                real_shared_edge=True,edge_length_mm=float(np.linalg.norm(q[4197]-q[mapping[10]]))*1000),
   required_correction='One identical indexed boundary parameterization at every row; certify exact Coons boundary reproduction before any sculpt/live review.'),
  dict(id='upper_front_chart_C0_jump',code='design.py if 6<=j<=20, then unconditional return to Coons at j21',
   mechanism='Supported breast target reaches Z1.335 at row20, then switches to unrelated shoulder Coons position at row21. No upper transition/tangent join exists.',
   rows=[row(20),row(21),row(22)],actual_jump=step(20,21),
   required_correction='Explicit upper-root/sternum/clavicle interface rail with shared positions and tangent rows, not an upper row cutoff.'),
  dict(id='sternum_misclassified_as_bowl',code='design.py front_target is applied through X0, plus lower j6/7/8 blend',
   mechanism='The breast pole/return sampling also warps central sternum. Its lower blend makes the central row go backwards in height; a real underbowl turn is incorrectly imposed outside either breast bowl.',
   rows=[row(6),row(7),row(8)],actual_jump=step(7,8),
   required_correction='A separate sternum/thorax chart with monotonic anatomical height, joined to each bowl along explicit root rails.'),
  dict(id='lateral_sheet_span',code='design.py Cartesian target weight by X blended directly against lateral Coons sheet',
   mechanism='Adjacent controls near the X confidence boundary span from a lateral sheet near Y−.012 to front bowl near Y−.126 in one cell. No independent anterior fold/root chart bridges them.',
   example=dict(controls=[4006,4007],world=q[[4006,4007]].tolist(),edge_length_mm=float(np.linalg.norm(q[4006]-q[4007]))*1000),
   required_correction='Explicit anterior fold/root interface distinct from floor/posterior sheet, not a compact scalar weight between unrelated sheets.'),
  dict(id='clavicle_feature_wrong_row_semantics',code='design.py j23/j24 as clavicle ridge/fossa',
   mechanism='Row numbers do not identify a source anatomical landmark after chart warp. At center the ridge/fossa rows lie Z1.414/1.424, and are not a measured clavicle/suprasternal placement.',
   rows=[row(23),row(24)],required_correction='Locate skeletal-plane landmarks in physical source-matched space; shallow forms come after valid connected embedding, not row-index offsets.')],
 longest_real_edges=[dict(controls=e,length_mm=float(np.linalg.norm(q[e[0]]-q[e[1]]))*1000,incident_faces=edges[e])for e in longest],
 local_oriented_faces=[face_metrics(i)for i in [4795,4796,4912,4913,4694,4710]],
 folded_quad_diagonals=dict(count=len(quad_bow),examples=quad_bow[:8],
  interpretation='Opposed triangle normals inside one quad identify a folded/concave or badly twisted embedding; this test is stronger than merely having reversed frontal projection on a legitimate underbowl.'),
 conclusion='Boundary graph/manifold test was insufficient. This is a concrete embedding and semantic-interface implementation failure, not evidence that retopology or original source cage is impossible.',
 live_restored=True,new_geometry_generated=False,ART=False)
(CACHE/'charted-forensic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2),flush=True)
