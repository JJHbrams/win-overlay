"""Fixed original-UV lower-lid pigment control. No raster, geometry, UV, eye or light edits."""
import bpy,sys,argparse,json,hashlib,ast,numpy as np
from pathlib import Path
H=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(H.parent/'finish-4/Mia_FaceFinish_v22.blend'));ap.add_argument('--output-dir',default=str(H));a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(exist_ok=True,parents=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();art=lambda p:{'path':str(Path(p)),'sha256':sha(p)};ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
old=H/'dependencies/legacy_snapshot_apply_interp.py';tree=ast.parse(old.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),str(old),'exec'))
sourcehash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));before=snapshots();packed={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file};skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=json.loads((H/'lowerlid-uv.json').read_text())
ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();p=np.array([tuple(v.co) for v in me.vertices]);tri_uv=np.array([[tuple(me.uv_layers.active.data[i].uv) for i in t.loops] for t in me.loop_triangles]);tri_co=np.array([p[list(t.vertices)] for t in me.loop_triangles]);A=tri_uv[:,0]-tri_uv[:,2];B=tri_uv[:,1]-tri_uv[:,2];den=A[:,0]*B[:,1]-A[:,1]*B[:,0]
def sample_uv(q):
 Q=np.array(q)-tri_uv[:,2];aa=(Q[:,0]*B[:,1]-Q[:,1]*B[:,0])/np.where(abs(den)>1e-12,den,1);bb=(A[:,0]*Q[:,1]-A[:,1]*Q[:,0])/np.where(abs(den)>1e-12,den,1);cc=1-aa-bb;valid=np.where((aa>=-1e-6)&(bb>=-1e-6)&(cc>=-1e-6)&(abs(den)>1e-12))[0];assert len(valid)>0,q;i=valid[0];return aa[i]*tri_co[i,0]+bb[i]*tri_co[i,1]+cc[i]*tri_co[i,2]
guides=[]
for eye in eyes:
 uv=np.array([v['uv'] for v in eye['lower']]);u0,u1=uv[:,0].min(),uv[:,0].max();us=np.linspace(u0+(u1-u0)*.08,u1-(u1-u0)*.08,24);vs=np.interp(us,uv[:,0],uv[:,1]);metrics=[]
 for u,v in zip(us,vs):
  p0=sample_uv((u,v-.001));p1=sample_uv((u,v-.011));metrics.append(float(np.linalg.norm(p1-p0)/.010))
 guides.append({'u_start':float(u0),'u_end':float(u1),'curve_uv':list(map(list,zip(us.tolist(),vs.tolist()))),'meters_per_v':list(map(list,zip(us.tolist(),metrics)))})
ev.to_mesh_clear()
m=skin.material_slots[7].material.copy();m.name='MIA_V22_Finish5_LocalUnderEye';n=m.node_tree.nodes;l=m.node_tree.links;mul=n['PigmentTimesControlledLight'];input_color=mul.inputs[1].links[0].from_socket;uv=n.new('ShaderNodeUVMap');uv.name='V22_F5_FIXED_ORIGINAL_UV';uv.uv_map=skin.data.uv_layers.active.name;sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs[0],sep.inputs[0])
def mathnode(op,a,b=None,name=None):
 node=n.new('ShaderNodeMath');node.operation=op
 if name:node.name=name
 for i,x in enumerate([a,b]):
  if x is not None:
   if isinstance(x,(int,float)):node.inputs[i].default_value=x
   else:l.new(x,node.inputs[i])
 return node.outputs[0]
def ramp(inp,stops,name):
 node=n.new('ShaderNodeValToRGB');node.name=name;node.color_ramp.interpolation='LINEAR';els=node.color_ramp.elements
 while len(els)>1:els.remove(els[-1])
 for i,(pos,value) in enumerate(stops):e=els[0] if i==0 else els.new(pos);e.position=pos;e.color=(value,value,value,1)
 l.new(inp,node.inputs[0]);return node.outputs[0]
factors=[]
for i,g in enumerate(guides):
 curve=ramp(sep.outputs[0],g['curve_uv'],'V22_F5_LowerLidCurve_'+str(i));metric=ramp(sep.outputs[0],g['meters_per_v'],'V22_F5_UVToSurfaceMeter_'+str(i));distance=mathnode('MULTIPLY',mathnode('SUBTRACT',curve,sep.outputs[1]),metric);distance=mathnode('MULTIPLY',distance,1000)
 # Map 0..6mm into ColorRamp0..1. A narrow crescent, strongest2..3.6mm below rim.
 normalized=mathnode('DIVIDE',distance,6);band=ramp(normalized,[(0,0),(.13,0),(.27,.75),(.36,1),(.60,1),(.88,0),(1,0)],'V22_F5_2to4mmCrescent_'+str(i));t=mathnode('DIVIDE',mathnode('SUBTRACT',sep.outputs[0],g['u_start']),g['u_end']-g['u_start']);taper=ramp(t,[(0,0),(.10,0),(.26,1),(.74,1),(.90,0),(1,0)],'V22_F5_CanthusTaper_'+str(i));factors.append(mathnode('MULTIPLY',band,taper))
factor=mathnode('MAXIMUM',factors[0],factors[1],name='V22_F5_LOCAL_CRESCENT_MASK');tint=n.new('ShaderNodeMixRGB');tint.name='V22_F5_BrownMauvePigmentMultiplier';tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[2].default_value=(.72,.62,.66,1);l.new(input_color,tint.inputs[1]);mix=n.new('ShaderNodeMixRGB');mix.name='V22_F5_LocalPigmentOnly';l.new(factor,mix.inputs[0]);l.new(input_color,mix.inputs[1]);l.new(tint.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],mul.inputs[1]);skin.material_slots[7].material=m
after=snapshots()
for name in before:
 if name!='MIA_V14_SculptedSkin':assert before[name]==after[name],name
 else:
  for k in before[name]:
   if k!='materials':assert before[name][k]==after[name][k],k
native=OUT/'Mia_FaceFinish5_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
for name,h in packed.items():assert hashlib.sha256(bpy.data.images[name].packed_file.data).hexdigest()==h,name
assert sha(SOURCE)==sourcehash
report={'source':art(SOURCE),'native':art(native),'recipe':art(__file__),'guide_source':art(H/'lowerlid-uv.json'),'snapshot_dependency':art(old),'guides':guides,'multiplier_linear':[.72,.62,.66],'scope':'Only visible skin material slot7 copy and fixed-original-UV procedural crescent. All coordinates/keys/UV/weights/topology/modifiers/other materials unchanged. No new raster/image changes. No iris/lash/light edits.','source_packed_count':len(packed),'all_source_packed_exact':True,'geometry_uv_keys_weights_exact':True,'other_mesh_snapshots_exact':True,'before':before,'after':after,'limitations':['2-4mm is approximate skin distance estimated from evaluated UV derivative near lower rim, not a reflection measurement.','Display under-eye/cheek target .78-.85 must be checked in renders; parameter values alone do not prove it.','No full face ART or expression approval.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('FINISH5_NATIVE',report['native'])
