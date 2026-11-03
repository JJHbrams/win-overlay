"""Build ONE same-topology candidate from09; CPU NumPy only, no native/GPU."""
from common import *
assert not (P/'shoulder10.npz').exists(), 'One candidate; no overwrite or sweep.'
assert sha(BASE/'posterior09.npz') == 'd5bf574ea958923fc70fe6ade4de7e0b64ec970c3cf15156be5f135af3c9cdd2'
assert sha(NATIVE09) == '7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158'
assert sha(SOURCE) == '3cb29ca55df903ec5248e59ff10ac6c5b607e01bb4baf894d6bb41437e46614f'
data = np.load(BASE/'posterior09.npz'); v = data['world']; f = data['triangles']; e = edges(f)
old_review = read(CAN/'blender/mia-fit-v003/body/design-sculpt07/E/review-records.json')
front = next(r for r in old_review['images'] if r['view'] == 'front')
box = front['source_crop']; mpp = .4/(box[2]-box[0]); cx = (box[0]+box[2])/2.; cy = (box[1]+box[3])/2.
# Original-pixel skin/background runs; strap-covered stations deliberately omitted.
left = [[153,231],[158,226],[163,224],[168,223],[173,223],[178,222],[183,221],[188,220],[198,219],[203,215],[208,212],[213,209],[218,205]]
right = [[258,201],[263,206],[268,210],[273,213],[278,216],[293,221],[298,223],[303,223],[308,224],[313,225],[318,227],[323,235],[328,238]]
back = [[840,237],[845,232],[850,229],[855,227],[865,226],[870,224],[875,224],[890,217],[895,214],[900,211],[905,208]]
source = dict(path=str(SOURCE), sha256=sha(SOURCE), original_size=[1536,1024],
    role='User-designated tied-hair shoulder/neck contour; mainv06 remains global body reference.',
    registration=dict(metres_per_pixel=mpp,front_axis_pixel=cx,zero_world_z_pixel=cy+1.275/mpp,
                      source_crop_front=box,method='Exact frozen E/09 wholeheight uniform registration. Same1536x1024 canvas and body panels; no shoulder normalization or aspect warp.'),
    traces_original_pixels=dict(front_left_skin=left,front_right_skin=right,back_left_skin=back),
    uncertainty='Manual visible boundary runs ±2px; strap crossings omitted around frontX190..196,284..290 and backX878..886. Left/right are separately observed; a symmetric map does not claim symmetric source identity. Pose, illustrated camera and source construction differ.',
    source_camera_estimates=dict(front=[0,0],profile=[85,0],back=[180,0],oblique=[40,0]),
    camera_uncertainty_degrees=dict(front_yaw=4,profile_yaw=8,back_yaw=4,oblique_yaw=10,pitch=6))
residuals=[]
for side, trace in [('left',left),('right',right)]:
    for px,py in trace:
        x=(px-cx)*mpp; target=1.275+(cy-py)*mpp; roof=projected_roof(v,e,x)
        residuals.append(dict(side=side,pixel=[px,py],world_x=x,target_z=target,baseline_roof=roof.tolist(),baseline_excess_mm=(roof[2]-target)*1000))
selected=[r['baseline_excess_mm'] for r in residuals if .065<=abs(r['world_x'])<=.150]
assert 40 < np.median(selected) < 65, selected
amplitude=.032
assert amplitude < np.median(selected)/1000, 'Do not force full source residual.'
q=mapping(v,amplitude).astype(np.float32)
protected=(v[:,2]<=1.36)|(v[:,2]>=1.465)|(abs(v[:,0])<=.025)|(abs(v[:,0])>=.195)
assert np.array_equal(q[protected],v[protected]) and np.array_equal(q[:,:2],v[:,:2])
np.savez_compressed(P/'shoulder10.npz',world=q,triangles=f)
for r in residuals:
    roof=projected_roof(q,e,r['world_x']); r['candidate_roof']=roof.tolist();r['candidate_excess_mm']=(roof[2]-r['target_z'])*1000
write(P/'source-rails.json',source)
held=read(BASE/'protected-input-hashes.json')
held.update({str(p):sha(p) for p in BASE.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
held[str(SOURCE)]=sha(SOURCE)
write(P/'protected-input-hashes.json',held)
report=dict(status='ONE CPU design candidate, ART UNVERIFIED',baseline_NPZ_sha256=sha(BASE/'posterior09.npz'),candidate_NPZ_sha256=sha(P/'shoulder10.npz'),
    vertices=len(v),triangles=len(f),triangles_exact=True,X_Y_coordinates_exact=True,
    map=dict(amplitude_m=amplitude,x_ramp_m=[.025,.065],x_plateau_m=[.065,.150],x_fade_m=[.150,.195],z_rise_m=[1.360,1.445],z_fade_m=[1.445,1.465],
             formula='(x,y,z) -> (x,y,z-.032*Wx(abs(x))*B(z)); quinticC2 pieces; samemap allY',
             determinant_global_lower_bound=1-amplitude*1.875/.085,
             proof='X,Yidentity; det=1-A*Wx*Bprime>=1-A*1.875/.085>0. For eachfixedX,Y, Zmap strictly increasing and identity outsidewindow, hence globallyinjective. Discrete straighttriangles still audited separately.'),
    source_core_front_excess_median_mm=float(np.median(selected)),source_rail_residuals=residuals,
    protected_vertices=int(protected.sum()),changed_vertices=int(np.any(q!=v,axis=1).sum()),
    maximum_delta_mm=float(np.linalg.norm(q-v,axis=1).max()*1000),
    fixed_Z_caution='X/Ypointcoords exact does NOT imply unchanged crosssectionwidth/depth atfixedphysicalZ. Measure sections.',
    native_saved=False,GPU_used=False)
write(P/'build-report.json',report)
print('SHOULDER10_ONE_BUILT',json.dumps({k:report[k] for k in ['source_core_front_excess_median_mm','changed_vertices','maximum_delta_mm','protected_vertices']}))
