"""Read-only front rays distinguish hair occlusion from aperture shape."""
exec(compile((__import__('pathlib').Path(__file__).parent/'project_aperture.py').read_text(),'project_aperture.py','exec'))
hair={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
hair.update(o.name for o in s.objects if o.type=='MESH' and any(t in o.name for t in ['Hair','HAIR','PIXAL']))
direction=s.camera.matrix_world.to_quaternion()@Vector((0,0,-1));allrows=[]
for role in ['hair_on','hair_off']:
 if role=='hair_off':
  for name in hair:
   o=bpy.data.objects.get(name)
   if o:o.hide_set(True)
  bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for eye in eyes:
  raw=np.array([pp['raw'] for pp in eye['boundary']]);mn=np.floor(raw.min(0)).astype(int);mx=np.ceil(raw.max(0)).astype(int);hits=[]
  for yy in range(mn[1],mx[1]+1):
   for xx in range(mn[0],mx[0]+1):
    origin=s.camera.matrix_world@Vector(((xx/1000-.5)*.29,(.5-yy/1000)*.29,0));hit,loc,normal,index,obj,mat=s.ray_cast(deps,origin,direction)
    if hit and obj.name=='MIA_V14_EyeSurface':hits.append((A@np.array([xx,yy])+t).tolist())
  q=np.array(hits);allrows.append({'role':role,'local_side':eye['local_side'],'eye_surface_first_hit_count':len(hits),'registered_x_minmax':[float(q[:,0].min()),float(q[:,0].max())] if len(hits) else None,'width':float(np.ptp(q[:,0])) if len(hits) else 0,'limit':'First object hit in original aperture bbox at 1px grid. Does not evaluate shader alpha/backface culling. Use actual ON/OFF renders for final visibility interpretation.'})
assert r.sha(src)==before
(H/'hair-occlusion-rays.json').write_text(json.dumps({'rays':allrows,'source_unchanged':True},indent=2));print(json.dumps(allrows,indent=2))
