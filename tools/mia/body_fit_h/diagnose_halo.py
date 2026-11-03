"""RAM-only diagnosis of the10 lower VDB-stencil discrepancies.

No mesh generation or repaired NPZ export. Hypothetical exact source-boundary
restoration is explicitly a boundary constraint, NOT float roundoff.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from field_numpy import Model
C=Path('D:/MiaWorkCache/mia-reference-work/win-overlay');A=C/'asset/mia/blender/mia-fit-v003';O=C/'.mia-cache/body-h/shape'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def normals(v,f):
    c=np.cross(v[f[:,1]].astype(float)-v[f[:,0]],v[f[:,2]].astype(float)-v[f[:,0]]);a=np.linalg.norm(c,axis=1);return c/np.maximum(a[:,None],1e-30),c,a
def oriented(row):
    a,b,c=map(int,row);return min((a,b,c),(b,c,a),(c,a,b))
def main():
    cap=load('H_halo_capacity',A/'integration/workspace-storage-20261103/storage_guard.py').inspect(10*1024*1024)
    if cap['violations']:raise RuntimeError(json.dumps(cap))
    source=A/'body/shoulder11/shoulder11-canonical.npz';raw=O/'H-guide-raw.npz';assert sha(source)=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9';assert sha(raw)=='44cea9c517121d2ea09ae4fee652f637a1b7390cbb956b36a4cd450fcaac5b71'
    a=np.load(source);b=np.load(raw);v=a['world'];f=a['triangles'];w=b['world'];g=b['triangles'];ids=np.flatnonzero(v[:,2]<=1.34);lookup={tuple(q):i for i,q in enumerate(w)};mapped=[];dist=[];changed=[]
    for i in ids:
        j=lookup.get(tuple(v[i]))
        if j is None:
            dd=np.linalg.norm(w.astype(float)-v[i],axis=1);j=int(np.argmin(dd));changed.append((int(i),j));dist.append(float(dd[j]))
        mapped.append(j)
    mapped=np.array(mapped,np.int32);assert len(set(mapped))==len(ids);assert len(changed)==10
    fixed=w.copy();newids=np.array([j for i,j in changed]);oldids=np.array([i for i,j in changed]);fixed[newids]=v[oldids];mapping=np.full(len(v),-1,np.int32);mapping[ids]=mapped
    lower_old=f[np.all(v[f,2]<=1.34,axis=1)];lower_new=g[np.all(fixed[g,2]<=1.34,axis=1)];oldkeys={oriented(row) for row in mapping[lower_old]};newkeys={oriented(row) for row in lower_new};lower_exact=oldkeys==newkeys
    incident=np.isin(g,newids).any(1);faceids=np.flatnonzero(incident);nr,cr,ar=normals(w,g);nf,cf,af=normals(fixed,g);angle=np.degrees(np.arccos(np.clip(np.sum(nr*nf,axis=1),-1,1)));orientation=np.einsum('ij,ij->i',cf,cr)/np.einsum('ij,ij->i',cr,cr)
    e=np.concatenate([g[:,[0,1]],g[:,[1,2]],g[:,[2,0]]]);fi=np.tile(np.arange(len(g)),3);e=np.sort(e,axis=1);order=np.lexsort((e[:,1],e[:,0]));e=e[order];fi=fi[order];pairs=np.flatnonzero(np.all(e[:-1]==e[1:],axis=1));edge=e[pairs];fa=fi[pairs];fb=fi[pairs+1];local=incident[fa]|incident[fb];turn0=np.degrees(np.arccos(np.clip(np.sum(nr[fa]*nr[fb],axis=1),-1,1)));turn1=np.degrees(np.arccos(np.clip(np.sum(nf[fa]*nf[fb],axis=1),-1,1)));turnchange=abs(turn1-turn0);length0=np.linalg.norm(w[edge[:,0]].astype(float)-w[edge[:,1]],axis=1);length1=np.linalg.norm(fixed[edge[:,0]].astype(float)-fixed[edge[:,1]],axis=1);touch=np.isin(edge,newids).any(1)
    model=Model();params=np.array(json.loads((O/'roof-fit.json').read_text(encoding='utf-8'))['params'][:5]);q=v[oldids].astype(float);names=list(model._current_reg);scores=np.column_stack([model.frozen.evaluate(model._current_reg[k],q) for k in names]);spec=model.p['mesher'];res=np.ceil((np.array(spec['bounds_max'])-spec['bounds_min'])/spec['voxel_m']).astype(int)+1;step=(np.array(spec['bounds_max'])-spec['bounds_min'])/(res-1);rows=[]
    for k,(old,new) in enumerate(changed):
        adj=np.flatnonzero(np.any(g==new,axis=1));cell=np.floor((v[old].astype(float)-spec['bounds_min'])/step).astype(int);corners=np.array([np.array(spec['bounds_min'])+(cell+np.array([dx,dy,dz]))*step for dx in [0,1] for dy in [0,1] for dz in [0,1]]);fd=model.evaluate(corners,params)-model.baseline(corners,'11');top=np.argsort(scores[k])[:3]
        rows.append(dict(source11_id=old,H_raw_id=new,source_world=v[old].tolist(),raw_world=w[new].tolist(),raw_minus_source_m=(w[new].astype(float)-v[old]).tolist(),displacement_m=float(np.linalg.norm(w[new].astype(float)-v[old])),adjacent_H_triangle_ids=adj.tolist(),adjacent_old_triangle_ids=np.flatnonzero(np.any(f==old,axis=1)).tolist(),adjacent_H_Zrange=[float(w[g[adj],2].min()),float(w[g[adj],2].max())],source_component_scores_not_distance=[dict(component=names[t],field_value=float(scores[k,t])) for t in top],voxel_cell=cell.tolist(),voxel_Zplanes=[float(corners[:,2].min()),float(corners[:,2].max())],corner_max_H_minus11_field=float(fd.max()),corner_field_difference_not_distance=True))
    # Only affected one-ring versus the whole hypothetical mesh, no Blender.
    geom=load('H_halo_intersections',A/'body/posterior-continuity08/geometry.py');tri=fixed[g].astype(float);lo=tri.min(1);hi=tri.max(1);seen=set();crossings=[]
    for i in faceids:
        candidates=np.flatnonzero(np.all(hi>=lo[i]-1e-10,axis=1)&np.all(lo<=hi[i]+1e-10,axis=1))
        for j in candidates:
            i,j=int(i),int(j);key=tuple(sorted((i,j)))
            if i==j or key in seen or np.intersect1d(g[i],g[j]).size:continue
            seen.add(key)
            if geom.triangle_intersects(tri[i],tri[j]):crossings.append(key)
    localix=np.flatnonzero(local);worst=localix[np.argmax(turnchange[local])];outside=np.ones(len(w),bool);outside[newids]=False
    report=dict(status='HYPOTHETICAL_SOURCE_BOUNDARY_RESTORATION_RAM_ONLY_NOT_EXPORTED',raw_mesh_sha256=sha(raw),source11_sha256=sha(source),changed_points=rows,changed_count=len(changed),maximum_raw_displacement_m=max(dist),cause='Native VDB/interpolation stencil crosses above analyticZ1.34 gate. Field atprotectedpoint is identical, but neighbouringvoxel corners abovegate change. This isNOTfloatingpoint roundoff.',protected_field_at_changed_points_byte_exact=bool(np.array_equal(model.evaluate(q,params),model.baseline(q,'11'))),hypothetical=dict(all49658_source_lower_coordinates_byte_exact=bool(np.array_equal(fixed[mapped],v[ids])),only_declared10_vertices_changed=bool(np.array_equal(fixed[outside],w[outside])),lower_oriented_triangle_triplets_exact=lower_exact,source_lower_triangle_count=len(lower_old),H_lower_triangle_count=len(lower_new),missing_lower_oriented_triangles=len(oldkeys-newkeys),extra_lower_oriented_triangles=len(newkeys-oldkeys),incident_triangles=len(faceids),maximum_incident_normal_change_degrees=float(angle[incident].max()),incident_normal_change_percentiles_degrees=np.percentile(angle[incident],[50,95,100]).tolist(),all_triangle_orientations_positive=bool(np.all(orientation>0)),minimum_incident_projected_area_ratio=float(orientation[incident].min()),minimum_incident_area_ratio=float((af[incident]/ar[incident]).min()),maximum_incident_area_ratio=float((af[incident]/ar[incident]).max()),maximum_local_edge_length_change_m=float(abs(length1[touch]-length0[touch]).max()),maximum_local_edge_relative_length_change=float((abs(length1[touch]-length0[touch])/length0[touch]).max()),maximum_local_edge_turn_change_degrees=float(turnchange[local].max()),local_edge_turn_raw_max_degrees=float(turn0[local].max()),local_edge_turn_restored_max_degrees=float(turn1[local].max()),worst_turn_edge=edge[worst].tolist(),worst_turn_edge_faces=[int(fa[worst]),int(fb[worst])],affected_ring_vs_whole_intersections=crossings,intersection_candidate_pairs=len(seen)),final_export_written=False,mesher_run=False,GPU_used=False,capacity=cap)
    path=O/'H-halo-diagnostic.json';assert not path.exists();path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('H_HALO_DIAGNOSTIC',str(path),path.stat().st_size,flush=True);print(json.dumps(report['hypothetical']),flush=True)

if __name__=='__main__':main()
