"""One distal arm-length proposal with actual upper-arm and torso IDs fixed.

Offline data construction only. Native-style masked longitudinal grab plus
rigid hand rotation, not the retired whole-girdle carrier. Apply only after
actual selection inspection through the scoped data-job route.
"""
from pathlib import Path
import hashlib,json,runpy
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
BASE='695dbbd825ce444fd04f0e390ccd64d31265d7cb14b027a08bf2ced82b4a7215'
sha=lambda a:hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

def smooth(x):
    x=np.clip(x,0.,1.);return x*x*x*(10+x*(-15+6*x))

def rotation(a,b):
    a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=float(a@b)
    k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0.]])
    assert c>-.999;return np.eye(3)+k+k@k/(1+c)

def components(ids,edges,count):
    parent=np.arange(count);rank=np.zeros(count,np.uint8);valid=np.zeros(count,bool);valid[ids]=True
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    for a,b in edges[valid[edges].all(1)].tolist():
        a,b=find(a),find(b)
        if a==b:continue
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
    return np.asarray([find(int(i)) for i in ids])

def prepare(root=ROOT):
    root=Path(root);out=root/'.mia-cache/body-h/live/integrated01/arm-length02'
    assert not out.exists();out.mkdir()
    with np.load(root/'.mia-cache/body-h/live/integrated01/current-geometry.npz') as z:q=z['co'];f=z['faces'].astype(np.int32)
    assert sha(q)==BASE
    with np.load(root/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz') as z:part=z['source_part'];assert np.array_equal(f,z['triangles'])
    with np.load(root/'.mia-cache/migration-to-C/row-ownership.npz') as z:rows={key:z[key] for key in z.files}
    edges=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
    part0=np.unique(f[part==0]);labels=components(part0,edges,len(q))
    nails=[]
    for label in np.unique(labels):
        ids=part0[labels==label]
        if len(ids)<1000 and abs(q[ids,0].mean())>.2 and q[ids,2].max()<1:nails.append(ids)
    assert len(nails)==10 and sum(map(len,nails))==2756
    p=q.astype(float);candidate=p.copy();active=[];transitions=[];hand_proof=[]
    for side,tip,row in [(1,42692,'armR'),(-1,42572,'armL')]:
        eligible=np.flatnonzero((q[:,0]*side>.15)&(q[:,2]<=1.250017))
        labels=components(eligible,edges,len(q))
        skin=eligible[labels==labels[np.flatnonzero(eligible==tip)[0]]]
        nail=np.concatenate([ids for ids in nails if q[ids,0].mean()*side>0])
        envelope=np.unique(np.r_[skin,nail]);e=p[rows[row][12]].mean(0)
        w=np.array([side*.298892,-.026790,1.000017]);target=np.array([side*.294,.012,.895])
        axis=(w-e)/np.linalg.norm(w-e);reach=(p[envelope]-w)@axis
        ids=envelope[reach>-.110];t=reach[reach>-.110]
        weight=smooth((t+.110)/.110);hand_weight=smooth((t+.025)/.025)
        R=rotation(p[tip]-w,np.array([side*.025,-.013,-.155]))
        relative=p[ids]-w
        candidate[ids]+=weight[:,None]*(target-w)+(relative@R.T-relative)*hand_weight[:,None]
        active.append(ids[t>=0]);transitions.append(ids[t<0])
        hand_ids=ids[t>=0];expected=(p[hand_ids]-w)@R.T+target
        hand_proof.append(dict(side=side,vertices=len(hand_ids),rigid_error_m=float(np.linalg.norm(candidate[hand_ids]-expected,axis=1).max()),
            elbow_fixed=bool(np.array_equal(candidate[rows[row][12]],p[rows[row][12]])),wrist_target=target.tolist()))
    editable=np.unique(np.concatenate(active)).astype(np.int32);transition=np.unique(np.concatenate(transitions)).astype(np.int32)
    fixed=np.setdiff1d(np.arange(len(q),dtype=np.int32),np.r_[editable,transition]);head=np.unique(f[part==1])
    candidate=candidate.astype(np.float32)
    guard=runpy.run_path(str(root/'tools/mia/integrated_finish/scoped_mesh_edit.py'))
    proof=guard['validate_delta'](q,candidate,f,editable,transition,dict(head=head,retained_torso_upper_arms_elbows_and_lowerbody=fixed),expected_before_sha256=BASE)
    changed=(q.view(np.uint32)!=candidate.view(np.uint32)).any(1);affected=changed[f].any(1)
    a=q[f[affected]].astype(float);b=candidate[f[affected]].astype(float)
    n0=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);n1=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0])
    cosine=np.sum(n0*n1,axis=1)/(np.linalg.norm(n0,axis=1)*np.linalg.norm(n1,axis=1))
    assert (cosine>0).all() and all(x['elbow_fixed'] and x['rigid_error_m']<1e-7 for x in hand_proof)
    np.savez_compressed(out/'proposal.npz',candidate=candidate,faces=f,editable_ids=editable,transition_ids=transition,
        protected_head=head,protected_retained=fixed)
    report=dict(proof,affected_triangles=int(affected.sum()),min_orientation_cos=float(cosine.min()),hand=hand_proof,
        source='v06 frozen original-aspect source4; wrist interval X.286..301,Y.004..019,Z.878..908',
        method='Topology-selected distal arm only; upper arm/elbow fixed, C2 proportional reach displacement, rigid distal hands+nails',
        limits='No cap/axilla/torso/girth/waist correction. Contact/source/shape quality unverified. No live apply.',ART=False)
    (out/'forecast.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),changed_vertices=proof['changed_vertices'],candidate_sha256=proof['candidate_sha256'],protected=len(fixed))))

if __name__=='__main__':prepare()
