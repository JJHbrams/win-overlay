"""Actual implicit branch ownership for inner-upper-arm paintscope; no shape/UV edit."""
from pathlib import Path
import sys,json,hashlib,importlib.util,os
import numpy as np
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();meta=json.loads((P/'surface.json').read_text());old=np.load(P/'surface.npz');joined=np.load(P/'joined-static.npz');v=old['world'];f=old['triangles'];ids=old['meshfaceid'];c=v[f].mean(1);regions=old['face_region'].copy();part=joined['source_part'][ids]
sp=importlib.util.spec_from_file_location('review12_originalfield',P.parent/'shoulder11/field.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);params=json.loads((P.parent/'shoulder11/parameters.json').read_text());_,reg=m.make(params)
candidate=np.flatnonzero((part==2)&(abs(c[:,0])>.12)&(c[:,2]<1.34))
q=c[candidate].astype(float);arm=np.minimum(m.evaluate(reg['upper_arm_R'],q),m.evaluate(reg['upper_arm_L'],q))
other=np.minimum.reduce([m.evaluate(reg[k],q) for k in ['curved_tapered_thorax_neck','breast_pair','anterior_fan_R','anterior_fan_L','posterior_wall_R','posterior_wall_L','shoulder_R','shoulder_L']])
armids=candidate[arm<other];regions[armids]=np.where(c[armids,0]>=0,6,7)
changed=np.flatnonzero(regions!=old['face_region']);examples=[]
for i in [91783,91803,90770,90723,177057,177079,178033,178076]:
    examples.append(dict(payload_triangle=i,world_centroid=c[i].tolist(),old_region=int(old['face_region'][i]),new_region=int(regions[i])))
oldVersion=P/'surface-v2-world-normal.npz'
if not oldVersion.exists():os.link(P/'surface.npz',oldVersion)
new=P/'surface-v3-branch-regions.npz'
if not new.exists():np.savez_compressed(new,world=v,triangles=f,loop_uv=old['loop_uv'],face_region=regions,meshfaceid=ids)
data=np.load(new)
for k in ['world','triangles','loop_uv','meshfaceid']:assert np.array_equal(data[k],old[k]),k
version=dict(meta,payload_version='v3-branch-regions',surface_npz_path=str(new),surface_npz_sha256=sha(new),region_counts={str(i):int((regions==i).sum()) for i in range(1,16)},region_policy='Guideupperarm vsactualthorax/breast/anterior/posteriorfan/shoulder implicitcomponent fieldownership; donorlimb bone/branch anddeclaredcollarregions. Not displayheightmask.')
version['region_examples']=examples
version['mixed_axilla_ownership']=dict(definition='Implicit componentwinner labels are not a unique anatomical partition through smoothunion floor; near-tied componentfields remain uncertain. Fieldscore differences are NOT geometricclearance.',blend_floor_face_count=int((abs(arm-other)<.004).sum()),policy='No convenience ray-through or claiming hiddenroot recovery; artistfituncertainty mustberecorded.')
(P/'surface-v3-branch-regions.json').write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n')
old.close();data.close();joined.close()
tmp=P/'surface-current-next.npz'
if not tmp.exists():os.link(new,tmp)
os.replace(tmp,P/'surface.npz')
temp=P/'surface-current-next.json';temp.write_text(json.dumps(version,indent=2)+'\n',encoding='utf-8',newline='\n');os.replace(temp,P/'surface.json')
proof=dict(only_face_region_changed=True,changed_faces=len(changed),geometry_world_sha256=meta['geometry_world_sha256'],loop_uv_sha256=meta['loop_uv_sha256'],old_payload_sha256=sha(oldVersion),new_payload_sha256=sha(new),examples=examples)
(P/'region-branch-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print('REVIEW12_REGION_BRANCH_FIXED',json.dumps(proof),flush=True)
