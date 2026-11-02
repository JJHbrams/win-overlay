"""Three distributed nape-rooted buried volumes; never promoted as visible finish."""
from pathlib import Path
import numpy as np,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;old=np.load(P/'held-first-six/locks.npz');base=json.loads((P/'base-audit.json').read_text());g=np.load(P/'current-geometry.npz');skin=next(r for r in base['objects'] if r['body']);bvh=BVHTree.FromPolygons(g[skin['key']+'_co'].tolist(),g[skin['key']+'_faces'].tolist(),all_triangles=True);out={};rows=[]
for name,source,shift in [('Core_Left','Underlay_Left',.035),('Core_Centre','Central_Cascade',0),('Core_Right','Underlay_Right',-.035)]:
 co=old[source+'_co'].astype(float).copy();centre=old[source+'_center'].astype(float);nr=len(centre);t=np.linspace(0,1,nr);co[:nr*16,0]=(centre[:,0,None]+(co[:nr*16].reshape(nr,16,3)[:,:,0]-centre[:,0,None])*2.15).ravel();long=np.r_[np.repeat(t,16),0,1];co[:,0]+=shift*(1-long)**3;co[:,2]-=.035*(1-long)**3;co[:,1]=.112+(co[:,1]-.120)*.30;faces=old[source+'_faces'];clear=[]
 for p in co[::2]:loc,n,idx,dist=bvh.find_nearest(Vector(p));clear.append(float((Vector(p)-loc).dot(n)))
 assert min(clear)>.003,(name,min(clear));z=np.clip((co[:,2]-1.15)/.38,0,1);z=z*z*(3-2*z);out[name+'_co']=co.astype(np.float32);out[name+'_faces']=faces;out[name+'_head_weight']=(.12+.88*z).astype(np.float32);rows.append(dict(name=name,source='held-first-six/'+source,scope='Buried dark volume only; no engraved lines, no claim of accepted visible surface',skin_min_clearance_mm=min(clear)*1000,bounds=[co.min(0).tolist(),co.max(0).tolist()]))
np.savez_compressed(P/'buried-core.npz',**out);(P/'buried-core.json').write_text(json.dumps(dict(status='BURIED_SUPPORT_ONLY_PENDING_ACTUAL_COVERAGE',payload_sha256=hashlib.sha256((P/'buried-core.npz').read_bytes()).hexdigest(),volumes=rows,ART=False),indent=2)+'\n',encoding='utf-8');print('BURIED_CORE_BUILT',[(r['name'],r['skin_min_clearance_mm']) for r in rows])
