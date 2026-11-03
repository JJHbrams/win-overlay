"""Transfer validated retained hand/forearm ownership by SAME original source_face."""
import numpy as np
def inherited_donor_arm_labels(previous_joined,previous_surface,new_joined):
    ids=previous_surface['meshfaceid'];parts=previous_joined['source_part'][ids];sf=previous_joined['source_face'][ids];labels=previous_surface['face_region'];table={}
    for source,label in zip(sf[(parts==0)&np.isin(labels,[6,7])],labels[(parts==0)&np.isin(labels,[6,7])]):
        source,label=int(source),int(label)
        if source in table:assert table[source]==label,'Ambiguous original arm source_face'
        table[source]=label
    out=np.zeros(len(new_joined['triangles']),np.int16);newpart=new_joined['source_part'];newsf=new_joined['source_face']
    for i in np.flatnonzero(newpart==0):out[i]=table.get(int(newsf[i]),0)
    return out
