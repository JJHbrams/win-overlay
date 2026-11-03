"""One charted connected upperbody DESIGN cage, sharing certified real boundaries.

Front/back panels meet at explicit rib/floor/arm and shoulder/clavicle rails.
Supported front bowl positions are sampled directly in Cartesian sections;
the rejected old-cage radial correspondence and offsets are not reused.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from scope import load_scope,ROOT,BODY,CACHE
from meridians import Sections

def smooth(t):
 t=np.clip(t,0.,1.);return t*t*t*(10-15*t+6*t*t)

def sample(points,t):
 p=np.asarray(points,float);s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
 return np.array([np.interp(np.asarray(t)*s[-1],s,p[:,k])for k in range(3)]).T

def main():
 s=load_scope();q=s['q'];d=dict(np.load(CACHE/'design-boundaries.npz'))
 oldfaces=s['faces'];removed=set(d['domain_faces'].tolist());inside=set(d['interior'].tolist())
 keep=np.array([i for i in range(len(q))if i not in inside],np.int32)
 remap={int(old):i for i,old in enumerate(keep)}
 vertices=q[keep].tolist();original_ids=keep.tolist();vertex_charts=[0]*len(keep);uv=[]
 faces=[];face_source=[];face_charts=[];materials=[]
 for i,f in enumerate(oldfaces):
  if i in removed:continue
  faces.append([remap[j]for j in f]);face_source.append(i);face_charts.append(0);materials.append(int(s['topology']['polygon_materials'][i]))
 named={}
 def point(key,xyz,chart):
  if key not in named:
   named[key]=len(vertices);vertices.append(np.asarray(xyz).tolist());original_ids.append(-1);vertex_charts.append(chart)
  else:assert np.linalg.norm(np.array(vertices[named[key]])-xyz)<1e-8
  return named[key]
 def original(i):return remap[int(i)]
 def face(v,chart,reverse=False):
  assert len(set(v))==len(v)
  faces.append(list(reversed(v))if reverse else v);face_source.append(-1);face_charts.append(chart);materials.append(1)
 # The side rail rises through lateral ribs to a real axillary floor and
 # then travels outward/down the inner arm to the held distal loop. Its
 # nonmonotonic height is deliberate, not a cap or a global heightfield.
 right_floor=501;left_floor=774;right_outer=459;left_outer=732
 rails={};sideids={}
 for side,waist,floor,outer,sign in [('L',906,left_floor,left_outer,-1),('R',941,right_floor,right_outer,1)]:
  floorpath=np.array([q[waist],[sign*.111,0.,1.255],[sign*.102,.002,1.320],q[floor]])
  # Separate anterior/posterior arm arcs, sharing the floor and outermost
  # endpoint. All twelve actual original arm points are held exactly.
  arm=(d['left_arm']if side=='L'else d['right_arm']).tolist()
  assert arm[0]==outer and arm[6]==floor
  sideids[side]=[original(waist)]
  xyz=sample(floorpath,np.linspace(0,1,23))
  for j in range(1,22):sideids[side].append(point(('side',side,j),xyz[j],5))
  sideids[side].append(original(floor))
  rails[side]=dict(front=sideids[side]+[original(i)for i in arm[5::-1]],
                   back=sideids[side]+[original(i)for i in arm[7:]+[arm[0]]])
  assert len(rails[side]['front'])==len(rails[side]['back'])==29
 # Source roof construction is a neck/trapezius plane, acromion shoulder
 # turn, then deltoid descent. No old conical/scalloped cap coordinates.
 roof={}
 for side,neck,outer,sign in [('L',226,left_outer,-1),('R',10,right_outer,1)]:
  a=point(('roof',side,'acromion'),[sign*.165,.003,1.379],6)
  b=point(('roof',side,'neckplane'),[sign*.075,.014,1.408],6)
  roof[side]=[original(outer),a,b,original(neck)]
 neckfront=[226,227,225,224,239,26,27,12,9,8,10]
 neckback=[226,346,351,127,126,122,10]
 waistfront=[906,915,914,916,987,986,988,979,978,967,966,938,940,961,941]
 waistback=[906,905,892,893,895,912,913,962,953,954,955,943,941]
 tops={name:roof['L'][:-1]+[original(i)for i in neck]+list(reversed(roof['R']))[1:]
       for name,neck in [('front',neckfront),('back',neckback)]}
 bottoms=dict(front=[original(i)for i in waistfront],back=[original(i)for i in waistback])
 guide_path=ROOT/'.mia-cache/body-h/shape/H-guide.npz';g=dict(np.load(guide_path));section=Sections(g['world'],g['triangles'])
 xs=np.linspace(-.110,.110,45)+1e-5;curves=np.array([section.front_x(x,1.195,1.335)for x in xs])
 print('DESIGN_CARTESIAN_FRONT_SECTIONS',len(curves),flush=True)
 def front_target(x,j):
  i=int(np.clip(np.searchsorted(xs,x)-1,0,len(xs)-2));u=np.clip((x-xs[i])/(xs[i+1]-xs[i]),0,1)
  curve=(1-u)*curves[i]+u*curves[i+1]
  # Direct target sample: lower attachment -> bowl underside -> pole ->
  # upper root. No correspondence to old pole/fan/return points exists.
  if j<=14:h=128-(j-8)/6*64
  else:h=64-(j-14)/6*64
  h=np.clip(h,0,128);lo=int(np.floor(h));hi=min(lo+1,128)
  return (1-(h-lo))*curve[lo]+(h-lo)*curve[hi]
 allrows={}
 for panel in ['front','back']:
  bottom=np.array([vertices[i]for i in bottoms[panel]]);top=np.array([vertices[i]for i in tops[panel]])
  left=np.array([vertices[i]for i in rails['L'][panel]]);right=np.array([vertices[i]for i in rails['R'][panel]])
  rows=[]
  for j in range(29):
   n=(14 if j<=2 else 16)if panel=='front'else 12
   ids=[];v=j/28
   for i in range(n+1):
    u=i/n
    if j==0:idx=bottoms[panel][i]
    elif j==28:idx=tops[panel][i]
    elif i==0:idx=rails['L'][panel][j]
    elif i==n:idx=rails['R'][panel][j]
    else:
     B=sample(bottom,u);T=sample(top,u)
     xyz=(1-u)*left[j]+u*right[j]+(1-v)*B+v*T-((1-u)*(1-v)*bottom[0]+u*(1-v)*bottom[-1]+(1-u)*v*top[0]+u*v*top[-1])
     if panel=='front':
      if 6<=j<=20:
       goal=front_target(xyz[0],j)
       weight=smooth((j-6)/2)*smooth((.110-abs(xyz[0]))/.025)
       xyz[1:]=(1-weight)*xyz[1:]+weight*goal[1:]
      # Explicit broad clavicle ridge/fossa/notch at upper-front rows;
      # construction strengths are millimetres, not etched ink or SCM tubes.
      if 20<j<28:
       wx=smooth((.14-abs(xyz[0]))/.035)
       if j==23:xyz[1]-=.002*wx
       if j==24:xyz[1]+=.002*wx
       if j==24 and abs(xyz[0])<.025:xyz[1]+=.002*smooth((.025-abs(xyz[0]))/.025)
     else:
      # Broad posterior volume; scapular/lat sheet remains separate from
      # the anterior fold. No failed posterior-leaf/cap mesh is sampled.
      wx=max(0.,1-(2*u-1)**2)
      xyz[1]+=.014*np.sin(np.pi*v)*wx
     chart=(1 if panel=='front' and j<20 else 6 if panel=='front' else 4)
     idx=point((panel,j,i),xyz,chart)
    ids.append(idx)
   rows.append(ids)
  for j,(a,b)in enumerate(zip(rows,rows[1:])):
   reverse=panel=='back';chart=(1 if panel=='front' and j<20 else 6 if panel=='front'else 4)
   if len(a)==len(b):
    for i in range(len(a)-1):face([a[i],a[i+1],b[i+1],b[i]],chart,reverse)
   else:
    assert panel=='front'and len(a)==15 and len(b)==17
    shift=0
    for i in range(14):
     if i in (6,8):
      face([a[i],b[i+shift+1],b[i+shift]],2,reverse);shift+=1
     face([a[i],a[i+1],b[i+shift+1],b[i+shift]],2,reverse)
    assert shift==2
  allrows[panel]=rows
 # Exact original retained control ownership is explicit; no consumer can
 # treat the new compact index as a raw old4647 ID.
 v=np.array(vertices,float);offset=np.r_[0,np.cumsum(list(map(len,faces)))];loops=np.array([i for f in faces for i in f],np.int32)
 edgecount={}
 for f in faces:
  for a,b in zip(f,f[1:]+f[:1]):e=tuple(sorted((a,b)));edgecount[e]=edgecount.get(e,0)+1
 assert all(n<=2 for n in edgecount.values()),'New nonmanifold edge'
 oldedgecount={}
 for f in oldfaces:
  for a,b in zip(f,f[1:]+f[:1]):e=tuple(sorted((a,b)));oldedgecount[e]=oldedgecount.get(e,0)+1
 assert sum(n==1 for n in edgecount.values())==sum(n==1 for n in oldedgecount.values()),'New boundary gap'
 oldid=np.array(original_ids,np.int32);held=oldid>=0
 assert np.array_equal(v[held],q[oldid[held]])
 out=CACHE/'charted-design.npz';assert not out.exists()
 local=(v-s['mapping']['matrix_world'][:3,3])@np.linalg.inv(s['mapping']['matrix_world'][:3,:3]).T
 local[held]=s['mapping']['q0_local'][oldid[held]]
 np.savez_compressed(out,world=v.astype(np.float32),posed_local=local.astype(np.float32),loop_vertices=loops,
  polygon_sizes=np.diff(offset).astype(np.int32),polygon_materials=np.array(materials,np.int32),original_control_id=oldid,
  original_face_id=np.array(face_source,np.int32),vertex_chart=np.array(vertex_charts,np.int32),face_chart=np.array(face_charts,np.int32),
  front_sections_x=xs,front_sections=curves)
 report=dict(scope='ONE new connected upperbody DESIGN quad flow, not production or UV migration',
  retained_controls=int(held.sum()),new_controls=int((~held).sum()),total_controls=len(v),new_faces=int(np.sum(np.array(face_source)<0)),
  new_quads=int(sum(len(f)==4 for f,old in zip(faces,face_source)if old<0)),new_triangles=int(sum(len(f)==3 for f,old in zip(faces,face_source)if old<0)),
  boundaries='Certified neck16/waist26/both arms12, no added boundary gaps',all_original_retained_controls_exact=True,
  intended_charts_not_validated='sternum/cartesian supported breast bowl+return; lateral rib->axillary floor->arm rail; anterior/posterior sheets; lat/back; shared neck/clavicle/acromion/deltoid roof. Current implementation is two coarse panel sheets; anatomic interface continuity is not proven.',
  guide='Direct45CartesianX sections of supported front envelope Z1.195..1.335 only, not old radial correspondence or failed cap/leaf',
  original_control_id_attribute=True,original_face_id_attribute=True,UV_weights_keys_migration='UNVERIFIED; outside charts intended exact, new body UV/key/weight unassigned static design only',
  proposal_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),ART=False,native_saved=False)
 (CACHE/'charted-design.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
