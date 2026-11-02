"""Current evaluated hair/body first-hit mask with original donor removed and clone sole replacement."""
from pathlib import Path
import numpy as np,json
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';data=np.load(P/'current-geometry.npz');base=json.loads((P/'base-audit.json').read_text());source=np.load(R/'source-mesh-input.npz');family=np.load(P/'identity-assembly.npz')['source_faces'];selected=set(family.tolist());mapping={tuple(sorted(map(int,t))):i for i,t in enumerate(source['faces'])};vertices=[];faces=[];owners=[];mc=None
for row in base['objects']:
 co=data[row['key']+'_co'];tri=data[row['key']+'_faces'];keep=np.ones(len(tri),bool)
 if row['name']=='MIA_V17_PIXAL_DetailedHair':
  mc=co;raw=np.array([mapping[tuple(sorted(map(int,t)))] for t in tri]);keep=~np.isin(raw,family)
 off=len(vertices);vertices.extend(co.tolist());faces.extend((tri[keep]+off).tolist());owners.extend([False]*int(keep.sum()))
assert mc is not None;off=len(vertices);vertices.extend(mc.tolist());faces.extend((source['faces'][family]+off).tolist());owners.extend([True]*len(family));bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True);arrays={};reports=[]
for record in json.loads((P/'actual-identity/records.json').read_text()):
 name=record['view'];cam=Matrix(record['camera']['matrix']);size=record['resolution'][0];scale=record['camera']['ortho_scale'];direction=cam.to_3x3()@Vector((0,0,-1));mask=np.zeros((size,size),bool)
 for y in range(size):
  for x in range(size):
   origin=cam@Vector((((x+.5)/size-.5)*scale,(.5-(y+.5)/size)*scale,0));hit,n,face,dist=bvh.ray_cast(origin,direction)
   if face is not None:mask[y,x]=owners[face]
 arrays[name]=mask;reports.append(dict(view=name,firsthit_owned_pixels=int(mask.sum()),image_pixels=size*size,source_original_owned_triangles_present_in_retained_BVH=0,clone_replacement_triangles=len(family),geometry_inventory='Current evaluated14hair+sharedbody; selected region lies below facial detail objects. U faces already excluded; all selected Main faces use opaque source material0.',resolution=[size,size]))
np.savez_compressed(P/'identity-owned-firsthit.npz',**arrays);(P/'identity-owned-firsthit.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8');print('IDENTITY_OWNED_COVERAGE',reports,flush=True)
