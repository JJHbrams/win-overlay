"""One source-shaped terminal module, using the complete co-located shell scope.

CPU preparation only. Source XY uses one disclosed similarity transform fit to
four existing true-brow anchors. Depth and root attachment are explicit inferred
3D hypotheses; whole-width initial ramps follow actual retained Main triangles.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT = ROOT / '.mia-cache/face-live/fringe-terminal01-ready'


def catmull(points, t):
    p = np.asarray(points, float)
    v = t*(len(p)-1)
    i = min(int(v), len(p)-2)
    f = v-i
    a,b,c,d = p[max(i-1,0)],p[i],p[i+1],p[min(i+2,len(p)-1)]
    return .5*(2*b+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)


def front_hit(vertices, faces, x, z):
    p = vertices[faces]
    a = p[:,0][:,[0,2]]
    e1, e2 = p[:,1][:,[0,2]]-a, p[:,2][:,[0,2]]-a
    d = np.array([x,z])-a
    det = e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0]
    b = np.divide(d[:,0]*e2[:,1]-d[:,1]*e2[:,0],det,out=np.zeros(len(p)),where=abs(det)>1e-12)
    c = np.divide(e1[:,0]*d[:,1]-e1[:,1]*d[:,0],det,out=np.zeros(len(p)),where=abs(det)>1e-12)
    hit = np.flatnonzero((abs(det)>1e-12)&(b>=0)&(c>=0)&(b+c<=1))
    if not len(hit):
        return None
    yy = p[hit,0,1]+b[hit]*(p[hit,1,1]-p[hit,0,1])+c[hit]*(p[hit,2,1]-p[hit,0,1])
    i = int(np.argmin(yy))
    return float(yy[i]),int(hit[i])


def local_fringe_depth(vertices, faces, x, z):
    """Use only the declared front shells; never a rear-head ray fallback."""
    hit=front_hit(vertices,faces,x,z)
    if hit is not None:
        return hit[0],0.
    p=vertices[faces]
    target=np.array([x,z])
    choices=[]
    for j,k in [(0,1),(1,2),(2,0)]:
        edge=p[:,k][:,[0,2]]-p[:,j][:,[0,2]]
        base=p[:,j][:,[0,2]]
        den=np.sum(edge*edge,axis=1)
        t=np.clip(np.divide(np.sum((target-base)*edge,axis=1),den,
                            out=np.zeros(len(p)),where=den>1e-14),0,1)
        distance=np.linalg.norm(base+edge*t[:,None]-target,axis=1)
        yy=p[:,j,1]+t*(p[:,k,1]-p[:,j,1])
        choices.append(np.column_stack((distance,yy)))
    choices=np.concatenate(choices)
    nearest=float(choices[:,0].min())
    # Keep the frontmost of near-coincident laminate edges rather than jumping
    # to an interior/back sheet when a new source-directed XZ path leaves it.
    return float(choices[choices[:,0]<=nearest+.0002,1].min()),nearest


def main():
    assert not OUT.exists(), 'Keep the first physical hypothesis immutable'
    cfg = json.loads(Path(__file__).with_name('fringe_terminal_goal.json').read_text())
    source = ROOT / cfg['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==cfg['source_sha256']
    a = np.load(ROOT / '.mia-cache/face-live/source-audit/analysis.npz')
    roots = np.load(ROOT / '.mia-cache/face-live/source-audit/components.npz')['face_root']
    v, faces = a['main_world'],a['main_triangles']
    hidden = np.flatnonzero(np.isin(roots,cfg['hidden_component_roots']))
    assert len(hidden)==498 and len(np.unique(faces[hidden]))==389
    # The existing rear module retains only the traced U omission. Neither its
    # geometry nor its own modifier is edited by this frontal preparation.
    rear = np.load(ROOT / 'asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup/loop-mask.npz')['polygon_indices']
    assert not np.intersect1d(hidden,rear).size
    retained = faces[~np.isin(np.arange(len(faces)),np.union1d(hidden,rear))]
    # Rays only need the frontal parent band; rear-facing cape triangles remain
    # available but min-Y selects the actual exterior toward the front camera.
    parent = retained[np.any(v[retained][:,:,2] > 1.57,axis=1)]
    right = np.array([.9933727979660034,0.,-.11493712663650513])
    up = np.array([.11493712663650513,0.,.9933727979660034])
    origin = np.array([0.,0.,1.58])
    pp, qq = [],[]
    for row in cfg['source_brow_anchors']:
        b = a[f"V31_SourceBrow_{row['side']}_world"].reshape(65,3,3)[:,1]
        point = np.array([np.interp(row['u']*64,np.arange(65),b[:,i]) for i in range(3)])-origin
        pp.append([row['pixel'][0],-row['pixel'][1]])
        qq.append([point@right,point@up])
    pp,qq = np.array(pp),np.array(qq)
    p0,q0 = pp.mean(0),qq.mean(0)
    zz = pp[:,0]-p0[0]+1j*(pp[:,1]-p0[1])
    ww = qq[:,0]-q0[0]+1j*(qq[:,1]-q0[1])
    similarity = np.vdot(zz,ww)/np.vdot(zz,zz)

    def source_xz(pixels):
        px = np.asarray(pixels,float)
        z = (px[:,0]-p0[0])+1j*(-px[:,1]-p0[1])
        w = z*similarity+(q0[0]+1j*q0[1])
        # Camera's XZ axes form an orthonormal rotation, so its inverse is a
        # transpose. One scale/rotation/translation; no local feature warp.
        world = origin+np.outer(w.real,right)+np.outer(w.imag,up)
        return world[:,[0,2]]

    pred = zz*similarity+(q0[0]+1j*q0[1])
    residual = abs(pred-(qq[:,0]+1j*qq[:,1]))
    payload = dict(hidden_faces=hidden.astype(np.int32),expected_hidden_triangles=faces[hidden])
    records = []
    for row in cfg['leaves']:
        ts = np.linspace(0,1,65)
        pixel_path = np.array([catmull(row['pixels'],t) for t in ts])
        xz = source_xz(pixel_path)
        widths = np.array([max(0.,float(catmull(row['full_width_pixels'],t))) for t in ts])*abs(similarity)/2
        # Original frontal depth provides a modest local curve, not a flat card.
        yy = [];depth_distances=[]
        for x,z in xz:
            y,distance=local_fringe_depth(v,faces[hidden],x,z)
            yy.append(y-.0007);depth_distances.append(distance)
        # A fitted smooth depth avoids inheriting layered donor discontinuities.
        yy = np.polyval(np.polyfit(ts,yy,3),ts)
        known=v[np.unique(faces[hidden]),1]
        assert yy.min()>known.min()-.005 and yy.max()<known.max()+.005, ('Depth extrapolation escaped frontal scope',row['name'])
        center = np.column_stack((xz[:,0],yy,xz[:,1]))
        tangent = np.gradient(center,axis=0)
        tangent /= np.linalg.norm(tangent,axis=1)[:,None]
        normal = np.tile([0.,-1.,0.],(len(ts),1))
        normal -= tangent*np.sum(normal*tangent,axis=1)[:,None]
        normal /= np.linalg.norm(normal,axis=1)[:,None]
        across = np.cross(tangent,normal)
        across /= np.linalg.norm(across,axis=1)[:,None]
        thickness = row['maximum_half_depth_m']*np.sin(np.pi*ts)**.7
        theta = np.arange(20)*2*np.pi/20
        cx,cy = np.cos(theta),np.sign(np.sin(theta))*abs(np.sin(theta))**.5
        rings = center[:,None,:]+across[:,None,:]*(widths[:,None]*cx)[...,None]+normal[:,None,:]*(thickness[:,None]*cy)[...,None]
        # The entire widening initial section sits just outside the ACTUAL
        # retained parent surface. Merely burying a cap caused past square starts.
        bounds=np.full(31,-np.inf)
        for i in range(0,23):
            seats=[]
            for point in rings[i]:
                h = front_hit(v,parent,point[0],point[2])
                if h is not None:
                    seats.append(point[1]-(h[0]-.00025))
            if not seats:
                assert i>0, ('No parent at point-like origin',row['name'])
                continue
            bounds[i]=max(seats)
        assert np.isfinite(bounds[0])
        # Only the point-like root seats backward into its parent. Wider stems
        # use the nonpenetration bound and retain their inferred front drape;
        # snapping every section to a newly exposed rear plane produces a kink.
        correction=np.maximum(bounds,0.)
        root_value=float(bounds[0]);correction[0]=root_value
        for _ in range(24):
            smooth=correction.copy()
            smooth[1:-1]=(correction[:-2]+4*correction[1:-1]+correction[2:])/6
            correction=np.maximum(smooth,bounds)
            correction[0]=root_value;correction[-1]=0.
        center[:31,1]-=correction
        rings[:31,:,1]-=correction[:,None]
        q = np.vstack((center[0],rings[1:-1].reshape(-1,3),center[-1]))
        n,s = 63,20
        triangles=[];uv=[]
        for i in range(n-1):
            for j in range(s):
                k=(j+1)%s
                a0,b0,c0,d0 = 1+i*s+j,1+i*s+k,1+(i+1)*s+k,1+(i+1)*s+j
                triangles.extend(((a0,b0,c0),(a0,c0,d0)))
                uv.extend((((j/s,(i+1)/64),((j+1)/s,(i+1)/64),((j+1)/s,(i+2)/64)),
                           ((j/s,(i+1)/64),((j+1)/s,(i+2)/64),(j/s,(i+2)/64))))
        for j in range(s):
            k=(j+1)%s
            triangles.extend(((0,1+k,1+j),(len(q)-1,1+(n-1)*s+j,1+(n-1)*s+k)))
            uv.extend((((.5,0),((j+1)/s,1/64),(j/s,1/64)),
                       ((.5,1),(j/s,63/64),((j+1)/s,63/64))))
        f=np.asarray(triangles,np.int32);uv=np.asarray(uv,np.float32)
        p=q[f]
        volume=float(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6)
        if volume<0:
            f=f[:,[0,2,1]];uv=uv[:,[0,2,1]];volume=-volume
        edges=Counter(tuple(sorted((int(a),int(b)))) for face in f for a,b in zip(face,np.roll(face,-1)))
        assert set(edges.values())=={2} and volume>0
        name=row['name']
        payload[name+'_world']=q.astype(np.float32)
        payload[name+'_triangles']=f
        payload[name+'_UV']=uv
        payload[name+'_guide']=center.astype(np.float32)
        records.append(dict(name=name,vertices=len(q),faces=len(f),closed=True,
            volume_m3=volume,source_pixels=row['pixels'],source_full_width_pixels=row['full_width_pixels'],
            attachment_initial_rings=23,maximum_parent_contact_correction_mm=float(max(abs(correction))*1000),
            minimum_attachment_bound_margin_m=float(np.min((correction-bounds)[np.isfinite(bounds)])),
            maximum_local_frontal_depth_extrapolation_distance_mm=float(max(depth_distances)*1000),
            source_depth_inferred=True,source_XZ_unwarped=True))
    OUT.mkdir(parents=True)
    np.savez_compressed(OUT/'geometry.npz',**payload)
    report=dict(candidate=OUT.name,scope=cfg['scope'],source=cfg['source'],
        source_sha256=cfg['source_sha256'],hidden_component_roots=cfg['hidden_component_roots'],
        hidden_faces=len(hidden),hidden_vertices=len(np.unique(faces[hidden])),rear_mask_disjoint=True,
        similarity_meters_per_pixel=float(abs(similarity)),similarity_rotation_degrees=float(np.degrees(np.angle(similarity))),
        brow_anchor_residual_mm=(residual*1000).tolist(),source_interpretation=cfg['source_interpretation'],
        locks=records,partial_display_overlay_REQUIRED_OFF=True,
        actual_live_installed=False,CPU_geometry_only=True,native_saved=False,ART=False,
        payload_sha256=hashlib.sha256((OUT/'geometry.npz').read_bytes()).hexdigest())
    (OUT/'candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    # Source goal only, with no reference rescale or feature distortion.
    image=Image.open(source).convert('RGB')
    d=ImageDraw.Draw(image)
    for row,color in zip(cfg['leaves'],[(60,180,220),(235,175,60),(220,95,160)]):
        p=np.array([catmull(row['pixels'],t) for t in np.linspace(0,1,65)])
        tangent=np.gradient(p,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        across=np.column_stack((-tangent[:,1],tangent[:,0]))
        widths=np.array([max(0.,float(catmull(row['full_width_pixels'],t))) for t in np.linspace(0,1,65)])/2
        for edge in [-1,1]:d.line([tuple(x) for x in p+edge*across*widths[:,None]],fill=color,width=2)
        d.line([tuple(x) for x in p],fill=color,width=1)
    image.crop((340,150,650,370)).resize((930,660)).save(OUT/'source-curve-goal.png')
    print(json.dumps({k:v for k,v in report.items() if k not in ('locks','source_interpretation')}))


if __name__=='__main__':
    main()
