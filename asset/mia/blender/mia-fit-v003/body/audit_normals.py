"""Read-only evaluated normal ownership check on current and B; no GPU/save."""
from pathlib import Path
import json,sys,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import apply_form_B
d=json.loads((P/'current-body-audit.json').read_text());N=Path(d['native'])
assert hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256']
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update();ob=bpy.data.objects[apply_form_B.OWNER]
report=dict(raw_has_custom_normals=ob.data.has_custom_normals,raw_normals_domain=ob.data.normals_domain,modifiers=[dict(name=m.name,type=m.type,show_render=m.show_render) for m in ob.modifiers],variants={})
for variant in ['current','B']:
    if variant=='B':apply_form_B.apply()
    dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);me.calc_loop_triangles()
    v=np.asarray([list(ev.matrix_world@x.co) for x in me.vertices]);tri=np.asarray([t.vertices[:] for t in me.loop_triangles]);cent=v[tri].mean(1);mi=np.asarray([me.polygons[t.polygon_index].material_index for t in me.loop_triangles]);roi=(mi==1)&(abs(cent[:,0])<.135)&(cent[:,1]<-.025)&(cent[:,2]>1.174)&(cent[:,2]<1.344)
    tids=np.flatnonzero(roi);polys={me.loop_triangles[i].polygon_index for i in tids}
    # Smooth corner normals must follow the evaluated surface; a custom normal
    # layer or flat polygons would need separate shading diagnosis.
    rot=np.asarray(ev.matrix_world.to_3x3());corner=np.asarray([x.vector[:] for x in me.corner_normals])@np.linalg.inv(rot)
    vn=np.asarray([x.normal[:] for x in me.vertices])@np.linalg.inv(rot)
    loops=np.asarray([me.loop_triangles[i].loops[:] for i in tids]);cn=corner[loops];expected=vn[tri[tids]]
    dots=(cn*expected).sum(2)/(np.linalg.norm(cn,axis=2)*np.linalg.norm(expected,axis=2));angle=np.degrees(np.arccos(np.clip(dots,-1,1)))
    report['variants'][variant]=dict(evaluated_has_custom_normals=me.has_custom_normals,evaluated_normals_domain=me.normals_domain,ROI_triangles=len(tids),flat_ROI_polygons=sum(not me.polygons[i].use_smooth for i in polys),corner_vs_vertex_normal_max_degrees=float(angle.max()),corner_vs_vertex_normal_p99_degrees=float(np.percentile(angle,99)),interpretation='Actual ROI uses smooth normals with no custom normal layer. Physical-gray test disconnects production normal maps; a silhouette hook cannot be attributed to texture. Smooth shading can still accentuate geometric curvature.')
    ev.to_mesh_clear()
report.update(native_unchanged=hashlib.sha256(N.read_bytes()).hexdigest()==d['sha256'],native_saved=False,gpu_used=False)
(P/'normal-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V003_NORMAL_AUDIT_DONE',json.dumps(report),flush=True)
