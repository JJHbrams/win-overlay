"""Generated-grid CPU API diagnostic only. No Mia/native/GPU edits."""
from pathlib import Path
import json
import bpy,numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
v=np.array([(x*.01,y*.01,0) for y in range(11) for x in range(11)],float);f=[]
for y in range(10):
    for x in range(10):
        i=y*11+x;f.extend([[i,i+1,i+12],[i,i+12,i+11]])
mesh=bpy.data.meshes.new('GeneratedApiGrid');mesh.from_pydata(v.tolist(),[],f);mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
boundary=np.flatnonzero((v[:,0]==0)|(v[:,0]==.1)|(v[:,1]==0)|(v[:,1]==.1));handle=60;group=ob.vertex_groups.new(name='Anchors');group.add(boundary.tolist()+[handle],1.,'REPLACE');mod=ob.modifiers.new('Probe','LAPLACIANDEFORM');mod.vertex_group=group.name;mod.iterations=10;bpy.context.view_layer.update();bpy.ops.object.laplaciandeform_bind(modifier=mod.name)
mesh.vertices[handle].co.z=.02;mesh.update();bpy.context.view_layer.update();e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();q=np.asarray([x.co[:] for x in me.vertices]);e.to_mesh_clear();free=np.setdiff1d(np.arange(len(v)),np.r_[boundary,handle]);r=dict(bound=mod.is_bind,fixed_error_max_m=float(np.linalg.norm(q[boundary]-v[boundary],axis=1).max()),handle_z=float(q[handle,2]),free_motion_max_m=float(np.linalg.norm(q[free]-v[free],axis=1).max()),scope='Toy API diagnostic, no F geometry')
path=Path(__file__).resolve().parent/'proportion-F/laplacian-api-probe.json';path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(r))
