"""Read-only depth-scale test; separate from rigid position probe. Never saves native."""
from pathlib import Path
probe=Path(__file__).with_name('eye_depth_probe.py')
exec(compile(probe.read_text().split('variants=[')[0],str(probe),'exec'))
OUT=OUT.parent/'eye-curvature-diagnostic';OUT.mkdir(exist_ok=True)
original=[v.co.copy() for v in eye.data.vertices]
iris_ids={v for p in eye.data.polygons if p.material_index==5 for v in p.vertices}
pivots={sign:max(original[i].y for i in iris_ids if original[i].x*sign>0) for sign in [-1,1]}
records=[]
for label,factor in [('depth_0p9',.9),('depth_1p0',1.),('depth_1p1',1.1)]:
 for v,co in zip(eye.data.vertices,original):
  sign=1 if co.x>=0 else -1
  v.co=co;v.co.y=pivots[sign]+factor*(co.y-pivots[sign])
 eye.data.update();bpy.context.view_layer.update()
 for view,yaw in [('left45',45),('profile90',90)]:
  y=math.radians(yaw);h._aim(s.camera,(2*math.sin(y),-2*math.cos(y),1.55),(0,0,1.55))
  s.render.filepath=str(OUT/(label+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
  records.append({'label':label,'depth_scale':factor,'view':view,'camera_matrix':[list(r) for r in s.camera.matrix_world]})
for v,co in zip(eye.data.vertices,original):v.co=co
eye.data.update();bpy.context.view_layer.update()
assert all((meshhash(bpy.data.objects[n]),str(bpy.data.objects[n].matrix_world))==p for n,p in protected.items())
assert sha(SOURCE)==source_sha
report={'source':str(SOURCE),'source_sha256':source_sha,'no_native_saved':True,'protected_geometry_and_keys_unchanged':True,'method':'Each eye local Y only scaled about its original iris frontmost tangent plane; local X/Z, object transform, skin, lids and materials fixed. This changes curvature depth, not rigid position.','local_y_pivot_per_sign':pivots,'maximum_displacement_m_at_10_percent':max(abs(co.y-pivots[1 if co.x>=0 else -1])*.1 for co in original),'camera':{'ortho':.29,'target':[0,0,1.55],'resolution':[1400,1400]},'variants':records}
(OUT/'diagnostic.json').write_text(json.dumps(report,indent=2));print('EYE_CURVATURE_PROBE_DONE')
