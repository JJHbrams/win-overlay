"""Body-only prelight continuation from the actual preserved head interface.

No source/head attributes, geometry, UVs, lights or native scenes are changed.
Fading uses distances on the CURRENT neck triangle graph, never old E heights.
"""
from pathlib import Path
import heapq
import numpy as np
from surface_api import sha, array_sha
from pattern_fields import PeriodicCurve, smooth01

COMMON=np.array([.9200000166893005,.6899999976158142,.6000000238418579])
HEAD=np.array([.8199999928474426,.6299999952316284,.550000011920929])


def _load(path):
    with np.load(path,allow_pickle=False) as a:return {k:a[k] for k in a.files}


def _distances(graph, starts):
    result=np.full(len(graph),np.inf)
    queue=[]
    for vertex in starts:result[vertex]=0;heapq.heappush(queue,(0.,int(vertex)))
    while queue:
        value,a=heapq.heappop(queue)
        if value!=result[a]:continue
        for b,length in graph[a]:
            new=value+length
            if new<result[b]:result[b]=new;heapq.heappush(queue,(new,b))
    return result


def prepare(surface, inputs):
    names=['head_source_npz','donor_npz','attributes_npz']
    hashes={name:sha(inputs[name]) for name in names}
    for name,expected in inputs.get('expected_sha256',{}).items():
        if hashes[name]!=expected:raise ValueError('Head pigment source fingerprint differs: '+name)
    source,donor,attributes=map(_load,[inputs[name] for name in names])
    head_faces=source['source_part']==1
    interface=np.intersect1d(np.unique(source['triangles'][head_faces]),np.unique(source['triangles'][~head_faces]))
    if not len(interface):raise ValueError('No actual shared head/body interface')
    if surface['world'].shape!=source['world'].shape or not np.array_equal(surface['world'][interface],source['world'][interface]):
        raise ValueError('Current F head/body interface differs from the preserved source')
    values=np.asarray(attributes['attribute_0']).reshape(-1)
    if len(values)!=len(donor['world']):raise ValueError('Source POINT alpha index namespace differs')
    shared=set(map(int,interface));samples={}
    for fi in np.flatnonzero(head_faces&(source['triangle_materials']==10)):
        for ci,vi in enumerate(source['triangles'][fi]):
            if int(vi) not in shared:continue
            original=source['source_vertex'][vi]
            if original>=0:value=float(values[original])
            else:value=float(source['source_corner_bary'][fi,ci].astype(float)@values[donor['triangles'][source['source_face'][fi]]])
            samples.setdefault(int(vi),[]).append(value)
    if set(samples)!=shared:raise ValueError('Interface is not completely covered by verified slot10')
    spread=max(max(a)-min(a) for a in samples.values())
    if spread>1e-6:raise ValueError('Inconsistent source POINT alpha across physical interface')
    alpha=np.array([np.mean(samples[int(i)]) for i in interface])
    if np.any(alpha<0) or np.any(alpha>1):raise ValueError('Unexpected source alpha')
    centre=surface['world'][interface,:2].mean(0)
    theta=np.arctan2(surface['world'][interface,0]-centre[0],-(surface['world'][interface,1]-centre[1]))
    angular=PeriodicCurve(np.column_stack((theta,alpha)))
    domain_faces=np.isin(surface['face_region'],inputs.get('neck_face_regions',[3,12]))
    f,w=surface['triangles'],surface['world']
    domain=np.unique(f[domain_faces]);outside=np.unique(f[~domain_faces])
    lower=np.setdiff1d(np.intersect1d(domain,outside),interface)
    if not len(lower) or not np.isin(interface,domain).all():raise ValueError('Actual neck topological domain is incomplete')
    edges=np.unique(np.sort(np.concatenate([f[domain_faces][:,[0,1]],f[domain_faces][:,[1,2]],f[domain_faces][:,[2,0]]]),axis=1),axis=0)
    graph=[[] for _ in range(len(w))]
    for a,b in edges:
        length=float(np.linalg.norm(w[a].astype(float)-w[b]))
        graph[a].append((int(b),length));graph[b].append((int(a),length))
    du,dl=_distances(graph,interface),_distances(graph,lower)
    if not np.isfinite(du[domain]).all() or not np.isfinite(dl[domain]).all():raise ValueError('Disconnected neck fade domain')
    fraction=du[domain]/np.maximum(du[domain]+dl[domain],1e-12)
    angle=np.arctan2(w[domain,0]-centre[0],-(w[domain,1]-centre[1]))
    result=np.zeros(len(w),np.float32)
    result[domain]=angular(angle)*(1-smooth01(fraction))
    result[interface]=alpha;result[lower]=0
    report=dict(scope='Actual slot10 PRELIGHT pigment only; no light/specular bake or face edit',
                surface_input_sha256=surface['input_sha256'],surface_guards=surface['guards'],
                inputs={name:dict(path=str(Path(inputs[name]).resolve()),sha256=hashes[name]) for name in names},
                source_native_sha256='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1',
                formula='(1-alpha)*CommonBase + alpha*HeadConstant, then original actual-light ramp',
                common_linear=COMMON.tolist(),head_linear=HEAD.tolist(),
                interface_vertex_ids=interface.tolist(),interface_alpha=alpha.tolist(),
                interface_world=w[interface].tolist(),boundary_corner_alpha_spread=float(spread),
                alpha_min_max=[float(alpha.min()),float(alpha.max())],
                prelight_RGB_min=(COMMON*(1-alpha[:,None])+HEAD*alpha[:,None]).min(0).tolist(),
                prelight_RGB_max=(COMMON*(1-alpha[:,None])+HEAD*alpha[:,None]).max(0).tolist(),
                actual_neck_domain_vertices=len(domain),actual_lower_boundary_vertices=len(lower),
                lower_boundary_world_bounds=[w[lower].min(0).tolist(),w[lower].max(0).tolist()],
                interface_to_lower_surface_distance_m=[float(dl[interface].min()),float(dl[interface].max())],
                fade='C1/quintic endpoint fade using actual current neck-edge distances to top and lower boundaries; no fixed world-height thresholds',
                alpha_field_f32_sha256=array_sha(result),source_head_unchanged=True,
                limits='Piecewise triangle field with C1 authoring fade; native lit normal/specular agreement still requires actual probe.')
    return result,report


def sample_alpha(raster,surface,vertex_alpha):
    output=np.zeros(raster['valid'].shape,np.float32)
    selected=raster['valid']&np.isin(raster['region'],[3,12])
    ids=raster['triangle_id'][selected];v=surface['world'][surface['triangles'][ids]].astype(float)
    p=raster['world'][selected].astype(float);ab,ac=v[:,1]-v[:,0],v[:,2]-v[:,0];ap=p-v[:,0]
    aa=np.einsum('ij,ij->i',ab,ab);bb=np.einsum('ij,ij->i',ab,ac);cc=np.einsum('ij,ij->i',ac,ac)
    pa=np.einsum('ij,ij->i',ap,ab);pc=np.einsum('ij,ij->i',ap,ac);den=aa*cc-bb*bb
    u=np.divide(cc*pa-bb*pc,den,out=np.zeros_like(den),where=abs(den)>1e-28)
    t=np.divide(aa*pc-bb*pa,den,out=np.zeros_like(den),where=abs(den)>1e-28)
    bary=np.column_stack((1-u-t,u,t));bary=np.clip(bary,0,1);bary/=np.maximum(bary.sum(1)[:,None],1e-30)
    output[selected]=np.einsum('ij,ij->i',bary,vertex_alpha[surface['triangles'][ids]])
    return output
