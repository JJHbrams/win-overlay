"""Explicit root-authorized10Z lower boundary constraint; NO second mesher.

33.26micrometre VDB-stencil influence is NOT roundoff. Raw guide and original
STOP report remain frozen. No neck AP/RY adjustment, native, render or bake.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util,time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from build_mesh import section,outer_roof,topology
from field_numpy import Model
C=Path(__file__).resolve().parents[3];A=C/'asset/mia/blender/mia-fit-v003';O=C/'.mia-cache/body-h/shape'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def oriented(x):
    a,b,c=map(int,x);return min((a,b,c),(b,c,a),(c,a,b))
def main():
    cap=load('H_final_capacity',A/'integration/workspace-storage-20261103/storage_guard.py').inspect(128*1024*1024)
    if cap['violations']:raise RuntimeError(json.dumps(cap))
    raw=O/'H-guide-raw.npz';source=A/'body/shoulder11/shoulder11-canonical.npz';diagpath=O/'H-halo-diagnostic.json';final=O/'H-guide.npz';proof=O/'H-guide-final.json';assert not final.exists() and not proof.exists(),'Never overwrite the one finalguide'
    assert sha(raw)=='44cea9c517121d2ea09ae4fee652f637a1b7390cbb956b36a4cd450fcaac5b71';assert sha(source)=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9';diag=json.loads(diagpath.read_text(encoding='utf-8'));a=np.load(raw);old=np.load(source);v=a['world'].copy();f=a['triangles'];oldv=old['world'];oldf=old['triangles'];rows=diag['changed_points'];assert len(rows)==10
    ids=np.array([x['H_raw_id'] for x in rows]);sourceids=np.array([x['source11_id'] for x in rows]);before=v[ids].copy();assert np.array_equal(v[ids,:2],oldv[sourceids,:2]);assert np.array_equal(v[ids],np.array([x['raw_world'] for x in rows],np.float32));v[ids]=oldv[sourceids]
    mask=np.ones(len(v),bool);mask[ids]=False;assert np.array_equal(v[mask],a['world'][mask]);assert np.array_equal(v[ids],oldv[sourceids]);lookup={tuple(q):i for i,q in enumerate(v)};lower=np.flatnonzero(oldv[:,2]<=1.34);mapped=np.array([lookup[tuple(oldv[i])] for i in lower],np.int32);assert len(set(mapped))==len(lower)==49658
    mapping=np.full(len(oldv),-1,np.int32);mapping[lower]=mapped;of=oldf[np.all(oldv[oldf,2]<=1.34,axis=1)];nf=f[np.all(v[f,2]<=1.34,axis=1)];assert len(of)==len(nf)==98928;assert {oriented(x) for x in mapping[of]}=={oriented(x) for x in nf}
    top=topology(v,f);assert top['finite'] and top['zero_area_faces']==0 and top['boundary_edges']==0 and top['nonmanifold_edges']==0 and top['inconsistent_oriented_edges']==0 and top['connected_components']==1 and top['signed_volume_m3']>0
    # Entire final guide, not just changed faces. Adjacency is excluded from
    # nonadjacent intersection tests, and all remaining BVH pairs are tested.
    geom=load('H_final_triangles',A/'body/posterior-continuity08/geometry.py');tree=BVHTree.FromPolygons([Vector(q) for q in v],f.tolist(),all_triangles=True);faces=f.tolist();seen=set();crossings=[];candidate_count=0;t0=time.time()
    for i,j in tree.overlap(tree):
        if i==j or any(k in faces[j] for k in faces[i]):continue
        key=(min(i,j),max(i,j))
        if key in seen:continue
        seen.add(key);candidate_count+=1
        if geom.triangle_intersects(v[f[i]].astype(float),v[f[j]].astype(float)):crossings.append(key)
    assert not crossings,('Wholeguideintersection',crossings[:10])
    model=Model(C);roof=O/'roof-fit.json';params=np.array(json.loads(roof.read_text(encoding='utf-8'))['params'][:5]);Fraw=model.evaluate(before.astype(float),params);Ffixed=model.evaluate(v[ids].astype(float),params);Fsource=model.baseline(v[ids].astype(float),'11');fieldrows=[]
    for k,row in enumerate(rows):fieldrows.append(dict(source_id=row['source11_id'],H_id=row['H_raw_id'],raw_H_field=float(Fraw[k]),restored_H_field=float(Ffixed[k]),restored_source11_field=float(Fsource[k]),raw_to_restored_field_delta=float(Ffixed[k]-Fraw[k]),inside_sign_changed=bool((Fraw[k]<=0)!=(Ffixed[k]<=0))))
    sections={str(z):section(v,f,[0,0,1],z) for z in [1.397,1.4,1.415,1.42,1.434]};outer=outer_roof(v,f);oldvol=geom.volume(oldv.astype(float),oldf)
    np.savez_compressed(final,world=v,triangles=f);corr=O/'H-lower-correspondence.npz';assert not corr.exists();np.savez_compressed(corr,source11_ids=lower.astype(np.int32),H_ids=mapped)
    result=dict(status='ONE_H_GUIDE_CPU_READY_UNSELECTED_NOT_ART',final_path=str(final),final_sha256=sha(final),final_bytes=final.stat().st_size,raw_path=str(raw),raw_sha256=sha(raw),source11_path=str(source),source11_sha256=sha(source),halo_diagnostic_sha256=sha(diagpath),roof_fit_sha256=sha(roof),world_sha256=hashlib.sha256(v.tobytes()).hexdigest(),triangles_sha256=hashlib.sha256(f.tobytes()).hexdigest(),topology=top,lower_boundary_constraint=dict(authorization='Rootexplicitlyapproved10ZsourceboundaryrestoreafterRAMdiagnostic; NOTroundoff',count=10,maximum_Z_restore_m=float(abs(v[ids,2].astype(float)-before[:,2]).max()),all_XY_exact_before_after=True,all_other_vertices_byte_exact=True,all49658_lower_source_vertices_exact=True,all98928_oriented_lower_triangles_exact=True,one_ring_normal_max_delta_degrees=diag['hypothetical']['maximum_incident_normal_change_degrees'],one_ring_edge_turn_max_delta_degrees=diag['hypothetical']['maximum_local_edge_turn_change_degrees'],vertices=rows,field_membership_scope='Field values are not distances; triangulated nativeisosurface isapproximate. Boundaryconstraintmaymovepointsacrosstinyfieldzero; thisisreportednotcallednewfieldfit.',field_membership=fieldrows,field_inside_sign_change_count=int(((Fraw<=0)!=(Ffixed<=0)).sum()),implicit_H_minus_source_field_at_restored_max=float(abs(Ffixed-Fsource).max())),whole_guide_nonadjacent_intersections=crossings,intersection_candidate_pairs=candidate_count,intersection_seconds=time.time()-t0,sections=sections,outer_cap_roof=outer,E_endpoint_coverage_source=str(O/'H-guide-build.json'),E_endpoint_scope='Waistcentral501andarmR166/L156loopsbelowgateareheldbycompletelowerphysicaltrianglecorrespondence; otherloopscrossingthesameplanesarenotthearm/waistowners.',lower_correspondence_path=str(corr),lower_correspondence_sha256=sha(corr),upperguide_volume_delta_m3=top['signed_volume_m3']-oldvol,volume_scope='Closedstaticupperguideincludingtemporaryneckstub, notfullbodyormedicalvolume',neck_AP_map_applied=False,neck_RY_map_applied=False,mesher_runs=1,new_mesher_run_in_finalizer=False,native_saved=False,GPU_used=False,inputs_copied=False,raw_build_STOP_report_preserved=True,capacity=cap)
    proof.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');assert sha(raw)=='44cea9c517121d2ea09ae4fee652f637a1b7390cbb956b36a4cd450fcaac5b71';assert sha(source)=='9382e21638e35ce36e3818cc0eb8e060994cc05227a5c56b262dcea7f4b843e9';print('H_FINAL_GUIDE_READY',str(final),result['final_sha256'],final.stat().st_size,flush=True);print('H_FINAL_PROOF',str(proof),'wholeguideSI',len(crossings),'pairs',candidate_count,flush=True)

if __name__=='__main__':main()
