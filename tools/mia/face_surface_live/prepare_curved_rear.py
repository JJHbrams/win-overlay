"""Source-guided distributed, layered curve sweeps for an initial two-view trial.

Creates no Blender scene. Unlike failed six long ribbons, primary/secondary
locks have distributed roots, short/mid/long endings, unequal turn rhythms,
upturned tips, non-coplanar depth and a thick softly ridged cross section.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT=ROOT/'.mia-cache/face-live/curved-rear02'
OLD=ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-central-fill'


def catmull(p,t):
    p=np.asarray(p,float);u=t*(len(p)-1);i=min(int(u),len(p)-2);f=u-i
    a,b,c,d=p[max(i-1,0)],p[i],p[i+1],p[min(i+2,len(p)-1)]
    return .5*(2*b+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)


def posterior_hit(vertices,triangles,x,z):
    q=vertices[triangles]
    ax,az=q[:,0,0],q[:,0,2];bx,bz=q[:,1,0],q[:,1,2];cx,cz=q[:,2,0],q[:,2,2]
    den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz)
    good=abs(den)>1e-14;u=np.zeros(len(q));v=u.copy()
    u[good]=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))[good]/den[good]
    v[good]=((cz-az)*(x-cx)+(ax-cx)*(z-cz))[good]/den[good]
    good&=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)
    ids=np.flatnonzero(good)
    if not len(ids):return None
    yy=u[ids]*q[ids,0,1]+v[ids]*q[ids,1,1]+(1-u[ids]-v[ids])*q[ids,2,1]
    chosen=int(np.argmax(yy));return float(yy[chosen]),int(ids[chosen])


def main(output=None,rooted=False):
    out=Path(output) if output else OUT
    assert not out.exists()
    spec=importlib.util.spec_from_file_location('mia_curve_capacity',ROOT/'asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    capacity=guard.inspect(12*1024**2);assert not capacity['violations'],capacity
    m=json.loads((OLD/'source_paths_v06.json').read_text())['uniform_local_guide_mapping']
    px=m['metres_per_source_pixel']
    # Visible source control points, not regularly spaced generated sine waves.
    # Depth and the first buried extension are inferred, not observed source facts.
    rows=[
      ('DeepLeft','under',(.067,.108,1.548),[(900,170),(890,207),(881,245),(884,278),(873,310),(878,342),(867,361)],.011,.0048,0),
      ('DeepRight','under',(-.064,.110,1.541),[(966,175),(978,208),(980,241),(993,267),(984,300),(994,328),(987,350)],.012,.0050,1),
      ('DeepCenter','under',(.006,.116,1.535),[(935,173),(928,210),(942,248),(931,279),(944,312),(936,345),(947,365)],.014,.0060,2),
      ('LongLeft','long',(.040,.128,1.531),[(905,184),(909,213),(898,247),(905,276),(898,310),(909,342),(902,365),(891,374),(884,369)],.012,.0054,3),
      ('LongCenter','long',(-.006,.132,1.525),[(933,187),(935,218),(927,251),(938,278),(931,310),(942,337),(935,365),(920,388),(916,383)],.013,.0058,4),
      ('LongRight','long',(-.041,.126,1.533),[(957,184),(955,216),(967,245),(960,279),(971,305),(960,335),(968,360),(978,370),(989,365)],.011,.0052,5),
      ('MidLeftOuter','mid',(.078,.112,1.520),[(894,184),(885,215),(896,244),(882,267),(879,292),(866,305),(858,299)],.013,.0055,6),
      ('MidRightOuter','mid',(-.075,.114,1.518),[(971,183),(985,215),(979,244),(994,265),(992,289),(1004,300),(1012,293)],.012,.0055,7),
      ('MidLeftInner','mid',(.024,.144,1.514),[(923,179),(925,210),(915,235),(924,255),(919,277),(907,288),(902,282)],.010,.0050,8),
      ('MidRightInner','mid',(-.026,.143,1.516),[(947,181),(943,207),(952,233),(945,258),(955,277),(965,284),(969,278)],.010,.0047,9),
      ('UpperLeftSweep','short',(.060,.139,1.542),[(903,174),(912,197),(900,221),(887,237),(878,234)],.010,.0045,10),
      ('UpperRightSweep','short',(-.057,.141,1.538),[(963,174),(957,198),(967,220),(980,235),(987,231)],.009,.0042,11),
      ('CenterTurnLeft','short',(.013,.154,1.528),[(931,176),(924,196),(936,219),(944,227),(951,222)],.009,.0045,12),
      ('CenterTurnRight','short',(-.013,.156,1.520),[(941,184),(949,206),(937,230),(926,242),(917,239)],.009,.0043,13),
      ('LowerLeftSplit','accent',(.068,.147,1.385),[(906,238),(898,263),(909,286),(898,309),(884,322),(878,317)],.0065,.0033,14),
      ('LowerRightSplit','accent',(-.064,.150,1.383),[(963,240),(973,263),(964,287),(978,308),(992,316),(1000,310)],.0065,.0033,15),
      ('FineLeftCurl','accent',(.084,.131,1.467),[(891,204),(878,226),(884,248),(873,261),(862,258)],.0045,.0025,16),
      ('FineRightCurl','accent',(-.086,.133,1.470),[(981,204),(994,228),(987,251),(1000,266),(1010,260)],.0045,.0025,17),
    ]
    original=np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz')
    source_q,source_f=original['main_world'],original['main_triangles']
    payload={};records=[];parents_v=[];parents_f=[]
    for name,layer,root,uv,width,depth,phase in rows:
        requested_root=list(root);root=np.array(root,float)
        uv=np.asarray(uv,float)
        zz=m['native_camera_target_z']+m['native_camera_ortho_height']/2-(uv[:,1]-m['source_vertical_translation'])*px
        xx=(m['source_center_u']-uv[:,0])*px
        layer_y=.116 if layer=='under' else .158 if layer in ('short','accent') else .148
        yy=layer_y+.010*np.sin(np.linspace(0,2.6,len(uv))+phase*.7)
        visible=np.column_stack((xx,yy,zz))
        # Two distributed buried controls sit behind the retained upper cape.
        seating=None
        if rooted:
            # Primary roots go inside the actual retained cape, while secondary
            # accents attach inside an existing primary lock rather than a fin
            # that the declared underlap will remove.
            parent_vertices=source_q if layer!='accent' else np.concatenate(parents_v)
            parent_triangles=source_f if layer!='accent' else np.concatenate(parents_f)
            hit=posterior_hit(parent_vertices,parent_triangles,root[0],root[2])
            if hit is None:
                near=parent_vertices[abs(parent_vertices[:,2]-root[2])<.006]
                assert len(near),('No parent near secondary root',name)
                near=near[np.argmin(abs(near[:,0]-root[0]))]
                root[0],root[2]=near[0],near[2]
                hit=posterior_hit(parent_vertices,parent_triangles,root[0],root[2])
            assert hit is not None,(name,root)
            root[1]=hit[0]-.006
            seating=dict(parent='retained source cape' if layer!='accent' else 'previous primary lock geometry',
                         posterior_surface_y=hit[0],triangle=hit[1],root_burial_m=.006)
        transition=(root+visible[0])*.5;transition[1]=max(root[1],visible[0,1])
        if rooted:
            middle=posterior_hit(parent_vertices,parent_triangles,transition[0],transition[2])
            if middle is not None:transition[1]=middle[0]-.004
        control=np.vstack((root,transition,visible))
        ts=np.linspace(0,1,97 if layer in ('under','long') else 73)
        center=np.array([catmull(control,t) for t in ts]);tangent=np.gradient(center,axis=0)
        tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        normal=np.tile([0.,1.,0.],(len(ts),1));normal-=tangent*np.sum(normal*tangent,axis=1)[:,None]
        normal/=np.linalg.norm(normal,axis=1)[:,None];across=np.cross(normal,tangent)
        across/=np.linalg.norm(across,axis=1)[:,None]
        twist=np.radians(18*np.sin(ts*4.8+phase*.8)+7*np.sin(ts*9+phase))
        ax=across*np.cos(twist)[:,None]+normal*np.sin(twist)[:,None]
        normal=normal*np.cos(twist)[:,None]-across*np.sin(twist)[:,None];across=ax
        # Broad buried roots, staggered main mass, and a finite curved taper.
        w=width*(.72+.28*np.sin(np.pi*np.minimum(ts/.65,1)))*(1-np.clip((ts-.68)/.32,0,1)**1.65)
        if rooted:
            w=width*np.sin(np.pi*ts)**.72
        w=np.maximum(w,.00012)
        thick=depth*(.80+.20*np.sin(ts*np.pi))*(1-np.clip((ts-.72)/.28,0,1)**1.5)
        if rooted:
            thick=depth*.42*np.sin(np.pi*ts)**.78
        thick=np.maximum(thick,.00010)
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(center,axis=0),axis=1))]
        curvature=np.linalg.norm(np.gradient(tangent,axis=0),axis=1)/np.maximum(np.gradient(arc),1e-7)
        w=np.minimum(w,.68/np.maximum(curvature,1e-6))
        theta=np.arange(32)*2*np.pi/32;cx=np.cos(theta);cy=np.sin(theta)
        if rooted:cy=np.sign(cy)*abs(cy)**.34
        ridge=.00035*np.cos(6*np.pi*cx+phase*.45)*np.maximum(cy,0)**3
        profile_y=thick[:,None]*cy[None,:]+ridge[None,:]*np.minimum(1,w/.004)[:,None]
        verts=(center[:,None,:]+across[:,None,:]*(w[:,None]*cx)[...,None]+normal[:,None,:]*profile_y[...,None]).reshape(-1,3)
        triangles=[];UV=[];n=len(ts);s=32;vparam=arc/arc[-1]
        for i in range(n-1):
            for j in range(s):
                h=(j+1)%s;a=i*s+j;b=i*s+h;c=(i+1)*s+h;d=(i+1)*s+j
                triangles.extend(((a,b,c),(a,c,d)))
                UV.extend((((j/s,vparam[i]),((j+1)/s,vparam[i]),((j+1)/s,vparam[i+1])),
                           ((j/s,vparam[i]),((j+1)/s,vparam[i+1]),(j/s,vparam[i+1]))))
        vi=len(verts);verts=np.vstack((verts,center[0],center[-1]))
        for j in range(s):
            h=(j+1)%s;triangles.extend(((vi,h,j),(vi+1,(n-1)*s+j,(n-1)*s+h)))
            UV.extend((((.5,0),((j+1)/s,.001),(j/s,.001)),((.5,1),(j/s,.999),((j+1)/s,.999))))
        triangles=np.asarray(triangles,np.int32);UV=np.asarray(UV,np.float32)
        q=verts[triangles];volume=float(np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2])).sum()/6)
        if volume<0:triangles=triangles[:,[0,2,1]];UV=UV[:,[0,2,1]];volume=-volume
        edges=collections.Counter(tuple(sorted((int(a),int(b)))) for f in triangles for a,b in zip(f,np.roll(f,-1)))
        assert set(edges.values())=={2} and volume>0
        offset=sum(len(v) for v in parents_v);parents_v.append(verts.copy());parents_f.append(triangles+offset)
        payload[name+'_world']=verts.astype(np.float32);payload[name+'_triangles']=triangles
        payload[name+'_UV']=UV;payload[name+'_guide']=center.astype(np.float32)
        if rooted:
            samples=[]
            for point in verts[:32]:
                h=posterior_hit(parent_vertices,parent_triangles,point[0],point[2])
                if h is not None:samples.append(point[1]-h[0])
            assert samples and max(samples)<-.001,(name,'Root cap is exposed',samples)
            seating['root_cap_max_posterior_exposure_m']=float(max(samples))
        records.append(dict(name=name,layer=layer,source_uv=uv.tolist(),buried_root=root.tolist(),requested_buried_root=requested_root,seating=seating,
                            bounds=[verts.min(0).tolist(),verts.max(0).tolist()],vertices=len(verts),faces=len(triangles),
                            closed=True,volume_m3=volume,depth_inferred=True))
    original=np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz');f=original['main_triangles'];q=original['main_world'][f].mean(1)
    # Original upper cape stays to Z1.49. New roots start at1.52..1.55 and overlap
    # it over several cm, unlike the failed candidate's exposed horizontal cut.
    fin=np.flatnonzero((abs(q[:,0])<.068)&(q[:,1]>.055)&(q[:,2]<1.49)&(q[:,2]>1.31))
    loop=np.load(ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup/loop-mask.npz')['polygon_indices']
    payload['hidden_faces']=np.union1d(fin,loop).astype(np.int32)
    payload['expected_hidden_triangles']=f[payload['hidden_faces']]
    out.mkdir(parents=True);np.savez_compressed(out/'curves.npz',**payload)
    report=dict(candidate=out.name,adopted=False,ART=False,locks=records,
                mapping=m,source_path='asset/mia/references/received/mia-body-v06-confirmed-20261102.png',
                source_sha256='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1',
                grooming_source='asset/mia/references/mia-clean-master-v22.png',
                hidden_faces=len(payload['hidden_faces']),retained_upper_cape_below_z=1.49,
                representation='18 actual-parent-seated rounded flattened lancet curve sweeps, tiny buried origins, distributed short/mid/long leaves, actual local ridges and upturned tips.' if rooted else '18 asymmetric distributed-root short/mid/long closed curve sweeps, rounded thickness, local ridges and upturned tips.',
                source_path_interpretation='Manual candidate centerlines guided by the visible v06 silhouette/overlaps and v22 grooming. These are not recovered artist splines or CT-like measured strands; exact individual strand identity remains uncertain. One unchanged uniform source SRT.',
                depth_and_buried_roots_inferred=True,
                scope='First actual back/oblique shape trial only; no production rig or final target shader acceptance.',
                payload_sha256=hashlib.sha256((out/'curves.npz').read_bytes()).hexdigest(),capacity=capacity)
    (out/'candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(candidate=report['candidate'],locks=len(rows),bytes=(out/'curves.npz').stat().st_size,hidden=report['hidden_faces'])))


if __name__=='__main__': main()
