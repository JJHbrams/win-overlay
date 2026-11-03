"""Read-only neck dihedrals shared by live operations."""
import numpy as np


def neck_angles(world,faces):
    q=world[faces].astype(float)
    n=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
    e=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
    owners=np.tile(np.arange(len(faces)),3);order=np.lexsort(e.T[::-1]);e=e[order];owners=owners[order]
    ids=np.flatnonzero(np.all(e[1:]==e[:-1],axis=1));pairs=np.column_stack([owners[ids],owners[ids+1]])
    use=((pairs>=209484)&(pairs<221750)).all(1);pairs=pairs[use]
    angles=np.degrees(np.arccos(np.clip((n[pairs[:,0]]*n[pairs[:,1]]).sum(1),-1,1)))
    return dict(median=float(np.median(angles)),p95=float(np.percentile(angles,95)),maximum=float(angles.max()),over45=int((angles>45).sum()))
