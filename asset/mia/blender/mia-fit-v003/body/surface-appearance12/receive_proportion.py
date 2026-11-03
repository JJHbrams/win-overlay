"""Independent same-topology F array receipt, before anatomical metadata/ART gate."""
from pathlib import Path
import numpy as np
from surface_api import load_surface,sha,write_json


def arrays(path):
    with np.load(path,allow_pickle=False) as a:return {k:a[k] for k in a.files}


def exact(a,b):
    return a.shape==b.shape and a.dtype==b.dtype and np.array_equal(np.ascontiguousarray(a).view(np.uint8),np.ascontiguousarray(b).view(np.uint8))


def receive(previous_surface,incoming_surface,previous_geometry,incoming_geometry,support_path,output):
    paths=[Path(p).resolve() for p in [previous_surface,incoming_surface,previous_geometry,incoming_geometry,support_path]]
    before={str(p):sha(p) for p in paths}
    previous=load_surface(paths[0]);current=load_surface(paths[1]);old,new,support=map(arrays,paths[2:])
    for key in ['triangles','triangle_uv','face_region','meshfaceid']:
        if not exact(previous[key],current[key]):raise ValueError('F changed protected body '+key)
    if previous['meta']['source_context']!=current['meta']['source_context']:raise ValueError('Frozen source camera/registration changed')
    if set(old)!=set(new):raise ValueError('Full joined array namespaces differ')
    for key in old:
        if key!='world' and not exact(old[key],new[key]):raise ValueError('Full joined source/UV/topology field changed: '+key)
    if not exact(previous['world'],old['world']) or not exact(current['world'],new['world']):raise ValueError('Full joined and body surface world arrays disagree')
    w0,w1=old['world'],new['world'];count=len(w0)
    free,protected=[np.asarray(support[k],int) for k in ['editable_vertex_ids','protected_vertex_ids']]
    if len(np.unique(np.r_[free,protected]))!=count or len(free)+len(protected)!=count:raise ValueError('Support does not partition EVERY physical vertex')
    if not exact(w0[protected],w1[protected]):raise ValueError('Protected F vertices moved')
    changed=np.any(w0.view(np.uint32)!=w1.view(np.uint32),axis=1)
    forbidden=np.setdiff1d(np.flatnonzero(changed),free)
    if len(forbidden):raise ValueError('F movement outside declared physical support')
    if not exact(w0[:,1],w1[:,1]):raise ValueError('F changed protected Y component')
    head=np.unique(old['triangles'][old['source_part']==1])
    if not exact(w0[head],w1[head]):raise ValueError('Actual retained head/interface moved')
    for key in ['compression_pin_ids','head_pin_ids','lower_pin_ids']:
        if not exact(w0[support[key]],w1[support[key]]):raise ValueError('Named protected domain moved: '+key)
    f=old['triangles'];n0=np.cross(w0[f[:,1]].astype(float)-w0[f[:,0]],w0[f[:,2]].astype(float)-w0[f[:,0]])
    n1=np.cross(w1[f[:,1]].astype(float)-w1[f[:,0]],w1[f[:,2]].astype(float)-w1[f[:,0]])
    area=np.einsum('ij,ij->i',n0,n0);valid=area>1e-30
    projected=np.einsum('ij,ij->i',n0[valid],n1[valid])/area[valid]
    if np.any(projected<=0):raise ValueError('F reversed an actual triangle projected oriented area')
    if any(sha(p)!=before[str(p)] for p in paths):raise ValueError('Producer arrays changed during independent receipt')
    delta=w1.astype(float)-w0
    result=dict(status='PASS independent ARRAY receipt only; anatomical metadata and actual gray/material/source review still required',
                inputs=[dict(path=str(p),sha256=before[str(p)]) for p in paths],
                source_camera_registration_held=True,full_nonworld_arrays_byte_exact=True,
                vertices=count,changed_vertices=int(changed.sum()),declared_editable_vertices=len(free),protected_vertices=len(protected),forbidden_changed_vertices=0,
                retained_actual_head_interface_vertices=len(head),retained_actual_head_interface_byte_exact=True,Y_byte_exact=True,
                protected_named_domains=['compression_pin_ids','head_pin_ids','lower_pin_ids'],
                maximum_delta_m=float(np.linalg.norm(delta,axis=1).max()),
                changed_old_world_bounds=[w0[changed].min(0).tolist(),w0[changed].max(0).tolist()],
                minimum_projected_oriented_area_ratio=float(projected.min()),
                ratio_limit='Actual triangle affine projected area check; not an interior-volume diffeomorphism claim.',
                producer_data_changed=False,GPU_used=False,ART_pass=False)
    write_json(output,result);return result
