"""Read-only physical sections and current F neck-domain publication."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path(__file__).resolve().parent;O=P/'proportion-F-lattice';old=np.load(P/'joined-expanded-E.npz');new=np.load(O/'geometry.npz');surface=np.load(O/'surface.npz');v=new['world'];e=old['world'];f=new['triangles'];part=new['source_part'];body=part!=1
edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1);owners=np.tile(np.arange(len(f)),3);order=np.lexsort((edges[:,1],edges[:,0]));edges=edges[order];owners=owners[order];ii=np.flatnonzero((edges[1:]==edges[:-1]).all(1));a,b=owners[ii],owners[ii+1];paired=edges[ii]
lo,hi=json.loads((P/'assembly-E.json').read_text())['collar_triangle_ranges']['neck'];neckFaces=(np.arange(len(f))>=lo)&(np.arange(len(f))<hi)
interface=np.unique(paired[((part[a]==1)&neckFaces[b])|((part[b]==1)&neckFaces[a])]);guideRing=np.unique(paired[((part[a]==2)&neckFaces[b])|((part[b]==2)&neckFaces[a])])
globalRegion=np.zeros(len(f),np.int16);globalRegion[surface['meshfaceid']]=surface['face_region'];domain=np.isin(globalRegion,[3,12]);neckDomain=np.unique(f[domain]);lower=np.unique(paired[(domain[a]!=domain[b])&(part[a]!=1)&(part[b]!=1)])
assert len(interface)==123 and np.array_equal(v[interface],e[interface])
np.savez_compressed(O/'neck-domain.npz',head_body_interface_vertex_ids=interface.astype(np.int32),neck_domain_vertex_ids=neckDomain.astype(np.int32),neck_domain_lower_boundary_vertex_ids=lower.astype(np.int32),old_guide_collar_ring_vertex_ids=guideRing.astype(np.int32))
def plane_points(coords,axis,value):
    t=coords[f[body]].astype(float);out=[]
    for i,j in [(0,1),(1,2),(2,0)]:
        u,w=t[:,i],t[:,j];du=u[:,axis]-value;dw=w[:,axis]-value;hit=du*dw<0
        alpha=du[hit]/(du[hit]-dw[hit]);out.append(u[hit]+alpha[:,None]*(w[hit]-u[hit]))
    return np.concatenate(out)
sections={}
for label,coords in [('E',e),('F',v)]:
    sec=[]
    for z in [1.34,1.36,1.38,1.40,1.42,1.44,1.455]:
        q=plane_points(coords,2,z);sec.append(dict(z_m=z,x_bounds_m=[float(q[:,0].min()),float(q[:,0].max())],y_bounds_m=[float(q[:,1].min()),float(q[:,1].max())]))
    roof=[]
    for x in [.04,.06,.08,.10,.12,.14,.16,.18]:
        q=plane_points(coords,0,x);q=q[q[:,2]>1.30]
        roof.append(dict(x_m=x,maximum_z_over_Y_m=float(q[:,2].max()) if len(q) else None))
    sections[label]=dict(physical_Z_sections=sec,front_projected_upper_envelope=roof)
# Actual F surface supporting the registered source graphic notch, not a guessed
# offset from the old construction cut and not a recovered skeletal landmark.
z=1.37778;tri=surface['triangles'];t=v[tri].astype(float);u=t[:,1]-t[:,0];w=t[:,2]-t[:,0];det=u[:,0]*w[:,2]-u[:,2]*w[:,0];ok=abs(det)>1e-14;A=np.zeros(len(t));B=A.copy();dx=-t[:,0,0];dz=z-t[:,0,2];A[ok]=(dx[ok]*w[ok,2]-dz[ok]*w[ok,0])/det[ok];B[ok]=(u[ok,0]*dz[ok]-u[ok,2]*dx[ok])/det[ok]
hits=np.flatnonzero(ok&(A>=-1e-7)&(B>=-1e-7)&(A+B<=1+1e-7)&np.isin(surface['face_region'],[1,3,4,12]));q=t[hits,0]+A[hits,None]*u[hits]+B[hits,None]*w[hits];j=int(np.argmin(q[:,1]));i=int(hits[j]);root=dict(world=q[j].tolist(),body_triangle_id=i,joined_triangle_id=int(surface['meshfaceid'][i]),barycentric=[float(1-A[i]-B[i]),float(A[i]),float(B[i])],face_region=int(surface['face_region'][i]),source_registered_world_Z_estimate=z,interpretation='Actual front F surface hit at registered source graphic notch estimate; not a recovered bone notch or guide-ring offset',source_projection_scope='Frozen wholeheight source SRT; source-camera uncertainty unchanged')
def volume(coords):
    t=coords[f].astype(float);return float(np.einsum('ij,ij->i',t[:,0],np.cross(t[:,1],t[:,2])).sum()/6)
report=dict(scope='Actual mesh-plane sections, projected maximumZ acrossY and source-registered graphic support hit. No ART pass.',sections=sections,head_body_interface_count=len(interface),head_body_interface_exact=True,neck_domain_regions=[3,12],neck_domain_actual_bounds=[v[neckDomain].min(0).tolist(),v[neckDomain].max(0).tolist()],neck_lower_boundary_actual_bounds=[v[lower].min(0).tolist(),v[lower].max(0).tolist()],old_guide_collar_ring_actual_mean=v[guideRing].mean(0).tolist(),old_guide_ring_not_anatomical_notch=True,clavicle_source_graphic_root_support=root,signed_surface_volume_delta_m3=volume(v)-volume(e),volume_scope='Differential signed surface integral; inherited fixed open boundaries cancel. Not a medical body-volume measurement.')
(O/'physical-sections.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
meta=json.loads((O/'surface.json').read_text());meta['previous_E_collar_bounds_reference_only']=meta.pop('collar_bounds',{});meta['previous_E_landmarks_reference_only']=meta.pop('landmarks',{});meta['neck_domain_path']=str(O/'neck-domain.npz');meta['neck_domain_regions']=[3,12];meta['actual_neck_domain_bounds']=report['neck_domain_actual_bounds'];meta['clavicle_source_graphic_root_support']=root;meta['landmarks']=dict(head_body_interface_center=v[interface].mean(0).tolist(),neck_lower_domain_boundary_center=v[lower].mean(0).tolist(),clavicle_source_graphic_support_world=root['world'],front_direction=[0,-1,0],up=[0,0,1],head_scale_applied=1.);meta['physical_sections_path']=str(O/'physical-sections.json')
(O/'surface.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n');print('F_ACTUAL_DOMAIN',len(interface),len(neckDomain),'graphicroot',root['world'],'region',root['face_region']);print('F_SIGNED_VOLUME_DELTA_ML',(volume(v)-volume(e))*1e6)
