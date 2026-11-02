"""Exterior-first whole loose-side assembly for UNMORPHED identity proof, not a fit."""
from pathlib import Path
import numpy as np,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';d=np.load(R/'source-mesh-input.npz');co=d['co'];T=d['faces'];lab=np.load(R/'global-components.npz')['face_component'];branches=np.load(P/'detailed-branch-inventory-DATA.npz');backbone=branches['h144_part15'];hidden=np.load(R/'loop-mask.npz')['polygon_indices'];bvh=BVHTree.FromPolygons(co.tolist(),T[backbone].tolist(),all_triangles=True);components=[];extra=[]
for k in np.unique(lab):
 if k==488:continue
 ids=np.flatnonzero(lab==k);points=co[np.unique(T[ids])];lo=points.min(0);hi=points.max(0)
 if lo[0]<.018 or hi[0]>.235 or lo[2]<1.23 or hi[2]>1.47:continue
 ds=np.array([bvh.find_nearest(Vector(p))[3] for p in points]);quant=np.quantile(ds,[0,.5,.8,1])
 if quant[2]>.012 or quant[3]>.04:continue
 if np.isin(ids,hidden).any():continue
 extra.extend(ids.tolist());components.append(dict(component=int(k),faces=len(ids),bounds=[lo.tolist(),hi.tolist()],nearest_backbone_m=quant.tolist()))
ids=np.union1d(backbone,extra).astype(np.int32);assert not np.isin(ids,hidden).any();np.savez_compressed(P/'identity-assembly.npz',source_faces=ids,source_vertices=np.unique(T[ids]).astype(np.int32),source_raw_faces=d['raw_ids'][ids],source_triangles=T[ids]);maps=np.load(R/'fullscene-family-ownership-DATA.npz');exposure=[]
for view in ['000','003','021','018','back_full']:
 f=maps[view+'_source_polygon'];mask=np.isin(f,ids);exposure.append(dict(view=view,firsthit_pixels=int(mask.sum()),firsthit_source_faces=int(len(np.unique(f[mask])))))
out=dict(status='WHOLE_EXTERIOR_IDENTITY_BENCHMARK_ONLY_NO_NEW_FIT',backbone='h144_part15 complete loose-side backing/root branch',backbone_faces=len(backbone),complete_co_located_exterior_skin_components=components,total_source_faces=len(ids),payload_sha256=hashlib.sha256((P/'identity-assembly.npz').read_bytes()).hexdigest(),source_main_co_sha256='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c',original_firsthit_exposure=exposure,limits='Topology/root branch plus complete co-located skins are a provisional whole loose-side assembly for SAME-WORLD identity test, not an accepted donor shape or camera ROI mask. Original remains untouched until one offline temporary visibility replacement during the proof.',ART=False);(P/'identity-assembly.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('EXTERIOR_IDENTITY_ASSEMBLY',len(ids),'skins',len(components),'exposure',exposure,flush=True)
