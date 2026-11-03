"""Whole retained correspondence and anatomical ownership for expanded E."""
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from source_branch_ownership import inherited_donor_arm_labels
P=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ah=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
old=np.load(P/'joined-discrete-D3.npz');new=np.load(P/'joined-expanded-E.npz');prev=np.load(P/'surface-v7-discrete-D3.npz');draft=np.load(P/'surface-v8-expanded-E.npz');meta=json.loads((P/'surface-v8-expanded-E.json').read_text());v=new['world'];f=new['triangles'];part=new['source_part'];c=v[f].mean(1);limb=new['vertex_limb_weights'][f].mean(1)
region=np.where(c[:,1]<-.006,1,2).astype(np.int16);donor=part==0
arms=donor&(np.maximum(limb[:,0],limb[:,1])>.45);legs=donor&(np.maximum(limb[:,2],limb[:,3])>.55)&~arms;pelvis=donor&~arms&~legs
region[pelvis]=np.where(c[pelvis,1]<-.006,8,9);region[legs]=np.where(c[legs,0]>=0,10,11)
candidate=np.flatnonzero((part==2)&(abs(c[:,0])>.12)&(c[:,2]<1.34));q=c[candidate].astype(float)
sp=importlib.util.spec_from_file_location('review12_E_field',P.parent/'shoulder11/field.py');field=importlib.util.module_from_spec(sp);sp.loader.exec_module(field);_,reg=field.make(json.loads((P.parent/'shoulder11/parameters.json').read_text()))
av=np.minimum(field.evaluate(reg['upper_arm_R'],q),field.evaluate(reg['upper_arm_L'],q));ov=np.minimum.reduce([field.evaluate(reg[k],q) for k in ['curved_tapered_thorax_neck','breast_pair','anterior_fan_R','anterior_fan_L','posterior_wall_R','posterior_wall_L','shoulder_R','shoulder_L']]);arms[candidate[av<ov]]=True;region[arms]=np.where(c[arms,0]>=0,6,7)
neck=(part==2)&(c[:,2]>1.4)&(abs(c[:,0])<.085);region[neck]=3
shoulder=(part==2)&(c[:,2]>1.34)&(abs(c[:,0])>=.085);region[shoulder]=np.where(c[shoulder,1]<-.006,4,5)
assembly=json.loads((P/'assembly-E.json').read_text())
for name,label in [('neck',12),('waist',13),('armR',14),('armL',15)]:lo,hi=assembly['collar_triangle_ranges'][name];region[lo:hi]=label
inherited=inherited_donor_arm_labels(old,prev,new);region[inherited!=0]=inherited[inherited!=0]
bodyids=draft['meshfaceid'];target=P/'surface-v9-expanded-E-branches.npz'
if target.exists():
    existing=np.load(target)
    for key,val in dict(world=v,triangles=draft['triangles'],loop_uv=draft['loop_uv'],face_region=region[bodyids],meshfaceid=bodyids).items():assert np.array_equal(existing[key],val)
    existing.close()
else:np.savez_compressed(target,world=v,triangles=draft['triangles'],loop_uv=draft['loop_uv'],face_region=region[bodyids],meshfaceid=bodyids)
R=np.array([np.sin(np.deg2rad(25)),0,-np.cos(np.deg2rad(25))]);L=R*np.array([-1,1,1]);armmax=float((np.array([.25,0,1.13])+.045*R-np.array([.236,0,1.17]))@R)
sections=[dict(name='expanded_waist',axis_world=[0,0,1],origin_world=[0,0,0],min_m=1.005,max_m=1.145,allowed_old_face_regions=[1,2,8,9,13],deny_old_face_regions=[6,7,14,15]),dict(name='expanded_arm_positive',axis_world=R.tolist(),origin_world=[.236,0,1.17],min_m=-.020,max_m=armmax,allowed_old_face_regions=[6,14]),dict(name='expanded_arm_negative',axis_world=L.tolist(),origin_world=[-.236,0,1.17],min_m=-.020,max_m=armmax,allowed_old_face_regions=[7,15])]
oldv=old['world'];bits=np.zeros(len(oldv),np.uint32)
for k in range(3):np.bitwise_or.at(bits,prev['triangles'][:,k],np.left_shift(np.uint32(1),prev['face_region'].astype(np.uint32)))
eligible=np.zeros(len(oldv),bool)
for s in sections:
    pos=(oldv.astype(float)-s['origin_world'])@np.array(s['axis_world']);allow=sum(1<<r for r in s['allowed_old_face_regions']);mask=(pos>=s['min_m']-1e-7)&(pos<=s['max_m']+1e-7)&((bits&allow)!=0)
    if s.get('deny_old_face_regions'):mask&=(bits&sum(1<<r for r in s['deny_old_face_regions']))==0
    eligible|=mask
headV=np.unique(old['triangles'][old['source_part']==1]);oldneck=np.load(P/'collar-rows-D3.npz')['neck'];newneck=np.load(P/'collar-rows-E.npz')['neck'];assert np.array_equal(oldv[oldneck],v[newneck]);eligible[headV]=False;eligible[oldneck.ravel()]=False;eligible[(bits&((1<<3)|(1<<12)))!=0]=False
g=old['guide_vertex'];gv=np.zeros_like(oldv);valid=g>=0;guide=np.load(P.parent/'shoulder11/shoulder11-canonical.npz')['world'];gv[valid]=guide[g[valid]]
core=valid&(((abs(gv[:,0])<=.125)&(gv[:,1]<=-.03)&(gv[:,2]>=1.18)&(gv[:,2]<=1.35))|((abs(gv[:,0])>=.13)&(abs(gv[:,0])<=.19)&(gv[:,2]>=1.23)&(gv[:,2]<=1.34))|((abs(gv[:,0])>=.065)&(abs(gv[:,0])<=.195)&(gv[:,2]>=1.34)&(gv[:,2]<=1.43)))
eligible[core]=False
mapping=np.full(len(oldv),-1,np.int32)
for name in ['source_vertex','guide_vertex']:
    lookup={int(x):i for i,x in enumerate(new[name]) if x>=0}
    for i,x in enumerate(old[name]):
        if x>=0 and int(x) in lookup:mapping[i]=lookup[int(x)]
lookup={row.tobytes():i for i,row in enumerate(v)}
for i in np.flatnonzero(mapping<0):mapping[i]=lookup.get(oldv[i].tobytes(),-1)
mapping[oldneck.ravel()]=newneck.ravel()
required=np.flatnonzero(~eligible);missing=required[mapping[required]<0]
# Exactly the obsolete D3 waist-plane subdivision on otherwise unchanged arms.
# These map to their SAME authoritative original donor source triangle, never a
# global nearest point. Original source/head/neck vertices cannot use this path.
assert len(missing)==200 and np.all(old['source_vertex'][missing]==-1)
assert np.all(abs(oldv[missing,2]-1.035)<1e-7) and np.all((bits[missing]&((1<<6)|(1<<7)))!=0)
donorData=np.load(P/'donor.npz');donorWorld=donorData['world'];donorTris=donorData['triangles'];newSourceFace=new['source_face'];newSourceBary=new['source_corner_bary'];oldTris=old['triangles'];oldPart=old['source_part'];oldSourceFace=old['source_face'];oldSourceBary=old['source_corner_bary'];newBySource={}
for i in np.flatnonzero(part==0):newBySource.setdefault(int(newSourceFace[i]),[]).append(int(i))
representation=[]
for i in missing:
    candidates=np.flatnonzero((oldTris==i).any(1)&(oldPart==0));found=None
    for oldfi in candidates:
        oldcorner=int(np.flatnonzero(oldTris[oldfi]==i)[0]);sf=int(oldSourceFace[oldfi]);sourceBary=oldSourceBary[oldfi,oldcorner].astype(float)
        for newfi in newBySource.get(sf,[]):
            if not np.array_equal(newSourceBary[newfi],np.eye(3,dtype=np.float32)):continue
            assert np.array_equal(v[f[newfi]],donorWorld[donorTris[sf]])
            bary=sourceBary/sourceBary.sum()
            if bary.min()>=-1e-7:
                q=(bary[:,None]*v[f[newfi]].astype(float)).sum(0);n=np.cross(v[f[newfi,1]].astype(float)-v[f[newfi,0]],v[f[newfi,2]].astype(float)-v[f[newfi,0]]);n/=np.linalg.norm(n)
                oldq=oldv[oldTris[oldfi]].astype(float);oldn=np.cross(oldq[1]-oldq[0],oldq[2]-oldq[0]);oldn/=np.linalg.norm(oldn)
                found=(int(i),newfi,sf,sourceBary,bary,float(np.linalg.norm(q-oldv[i])),float(abs((oldv[i]-q)@n)),float(np.degrees(np.arccos(np.clip(oldn@n,-1,1)))))
                break
        if found is not None:break
    assert found is not None,('No identical-source triangle representation',int(i))
    representation.append(found)
assert max(x[5] for x in representation)<1e-7,'Old float32 clipping/bary rounding exceeds recorded bound'
known=np.flatnonzero(mapping>=0);assert np.array_equal(oldv[known],v[mapping[known]])
oldHead=np.flatnonzero(oldPart==1);newHead=np.flatnonzero(part==1);faceLookup={v[f[i]].tobytes():int(i) for i in newHead};headMap=np.array([faceLookup[oldv[oldTris[i]].tobytes()] for i in oldHead],np.int32)
for key in ['old_loop_uv','source_corner_normals','source_corner_bary','source_face','triangle_materials']:assert np.array_equal(old[key][oldHead],new[key][headMap]),key
corr=P/'retained-correspondence-E.npz';np.savez_compressed(corr,old_vertex_id=known.astype(np.int32),new_vertex_id=mapping[known],expected_retained_old_ids=required.astype(np.int32),excluded_old_vertex_ids=np.flatnonzero(eligible).astype(np.int32),protected_core_old_ids=np.flatnonzero(core).astype(np.int32),old_neck_row_ids=oldneck,new_neck_row_ids=newneck,old_head_triangle_id=oldHead.astype(np.int32),new_head_triangle_id=headMap,interpolated_old_vertex_id=np.array([x[0] for x in representation],np.int32),interpolated_new_triangle_id=np.array([x[1] for x in representation],np.int32),interpolated_source_face=np.array([x[2] for x in representation],np.int32),interpolated_old_source_corner_bary=np.array([x[3] for x in representation]),interpolated_new_barycentric=np.array([x[4] for x in representation]),interpolated_world_residual_m=np.array([x[5] for x in representation]),interpolated_plane_residual_m=np.array([x[6] for x in representation]),old_subdivision_normal_vs_source_degrees=np.array([x[7] for x in representation]))
previousMeta=json.loads((P/'surface-v7-discrete-D3.json').read_text());assert meta['source_context']==previousMeta['source_context']
version=dict(meta,payload_version='v9-expanded-E-branches',surface_npz_path=str(target),surface_npz_sha256=sha(target),region_counts={str(i):int((region[bodyids]==i).sum()) for i in range(1,16)},region_policy='Donor limb branch weights, actual guide component ownership, and exact construction collar face ancestry; no worldheight underwear mask',expanded_collar_sections=sections,retained_correspondence_path=str(corr),retained_correspondence_sha256=sha(corr),mixed_axilla_field_tie_faces=int((abs(av-ov)<.004).sum()))
target.with_suffix('.json').write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n')
proof=dict(previous_joined_path=str(P/'joined-discrete-D3.npz'),previous_joined_sha256=sha(P/'joined-discrete-D3.npz'),new_joined_path=str(P/'joined-expanded-E.npz'),new_joined_sha256=sha(P/'joined-expanded-E.npz'),previous_surface_path=str(P/'surface-v7-discrete-D3.npz'),previous_surface_sha256=sha(P/'surface-v7-discrete-D3.npz'),new_surface_path=str(target),new_surface_sha256=sha(target),section_predicates=sections,correspondence_path=str(corr),correspondence_sha256=sha(corr),all_required_outside_band_vertices_covered=len(required),mapped_old_vertices_exact=len(known),allowed_replacement_old_vertices=int(eligible.sum()),all_old_head_triangles_UV3_normals_attributes_source_corner_exact=len(oldHead),D3_neck_rows_exact=int(oldneck.size),source_cameras_held=True,protected_core_ids_path=str(corr)+':protected_core_old_ids',obsolete_forearm_subdivision_representation=dict(count=len(representation),namespace='interpolated_new_triangle_id indexes joined-expanded-E.npz triangles, NOT body-only payload triangles',same_original_source_face_and_source_triangle_vertices_exact=True,maximum_old_rounded_point_residual_m=max(x[5] for x in representation),maximum_old_rounded_point_plane_residual_m=max(x[6] for x in representation),maximum_old_subdivision_facet_normal_difference_deg=max(x[7] for x in representation),new_original_source_triangle_normal_difference_deg=0.,scope='Root-authorized representation-only change of200 old source_vertex=-1 forearm split points atZ1.035; not geometry displacement/exemption of original donor/head/core vertices'),native_saved=False,ART_status='UNVERIFIED until Egray actuals')
(P/'expanded-E-protection-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('REVIEW12_E_PUBLISHED',sha(target),'retained',len(required),'excluded',int(eligible.sum()),'headfaces',len(oldHead),'neckrows',oldneck.size)
