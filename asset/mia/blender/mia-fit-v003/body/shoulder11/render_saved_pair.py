"""Fresh saved09/saved10 only: paired source4+high/low+Normal, one batch."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import bpy
import math
from mathutils import Vector

dry='--cpu-only' in sys.argv
assert all(x['exact'] for x in read(P/'protected-physical-triangles.json').values()) and not read(P/'CPU-audit.json')['new_nonadjacent_intersections']
assert read(P/'native/fresh-reopen.json')['raw_world_triangles_bitexact_to_NPZ']
O=P/('preflight' if dry else 'actual');O.mkdir(exist_ok=True)
assert dry or not (O/'render-records.json').exists(), 'One frozen paired batch; no overwrite.'
jobs=[('gray','front',0,0),('gray','profile',85,0),('gray','back',180,0),('gray','oblique',40,0),
      ('gray','upperoblique',40,30),('gray','loweropposite',-40,-25),('normal','front',0,0),('normal','back',180,0)]
allrows=[];reference_states={};gray_states={}

def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except TypeError:return str(v)

def tree_state(tree):
    nodes=[]
    for n in tree.nodes:
        values=[]
        for i,s in enumerate(n.inputs):
            if hasattr(s,'default_value'):values.append([i,s.name,plain(s.default_value)])
        nodes.append(dict(name=n.name,type=n.bl_idname,operation=getattr(n,'operation',None),values=values))
    links=sorted([l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in tree.links)
    return dict(nodes=sorted(nodes,key=lambda n:n['name']),links=links)

def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()

for state,native,npz in [('09',NATIVE09,BASE/'posterior09.npz'),('11',NATIVE11,P/'shoulder11-canonical.npz')]:
    nativehash=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native))
    data=np.load(npz);scene=bpy.context.scene;meshobs=[o for o in scene.objects if o.type=='MESH'];assert len(meshobs)==1
    body=meshobs[0];assert np.array_equal(np.asarray([v.co[:] for v in body.data.vertices],np.float32),data['world'])
    assert np.array_equal(np.asarray([q.vertices[:] for q in body.data.polygons],np.int32),data['triangles'])
    assert not body.modifiers and np.array_equal(np.array(body.matrix_world),np.eye(4)) and len(scene.objects)==14
    gray=body.data.materials[0];gray_states[state]=tree_state(gray.node_tree)
    normal=bpy.data.materials.new('S10_ActualGeometryNormal');normal.use_nodes=True;nn=normal.node_tree.nodes;nn.clear()
    geo=nn.new('ShaderNodeNewGeometry');vm=nn.new('ShaderNodeVectorMath');vm.operation='MULTIPLY_ADD';vm.inputs[1].default_value=(.5,.5,.5);vm.inputs[2].default_value=(.5,.5,.5)
    em=nn.new('ShaderNodeEmission');out=nn.new('ShaderNodeOutputMaterial')
    normal.node_tree.links.new(geo.outputs['Normal'],vm.inputs[0]);normal.node_tree.links.new(vm.outputs['Vector'],em.inputs['Color']);normal.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    for n in normal.node_tree.nodes:n.name=n.bl_label
    cams=[o for o in scene.objects if o.type=='CAMERA'];assert len(cams)==10
    cam=scene.camera;assert cam in cams
    for mode,view,yaw,pitch in jobs:
        target=Vector((0,-.035,1.33));a,b=math.radians(yaw),math.radians(pitch)
        cam.location=target+Vector((2*math.sin(a)*math.cos(b),-2*math.cos(a)*math.cos(b),2*math.sin(b)))
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.4;cam.data.clip_start=.1;cam.data.clip_end=10
        scene.camera=cam;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100
        scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.render.image_settings.file_format='PNG';scene.frame_set(1)
        mat=normal if mode=='normal' else gray;body.data.materials[0]=mat;bpy.context.view_layer.update()
        lights=[dict(name=o.name,type=o.data.type,energy=o.data.energy,size=o.data.size,shape=o.data.shape,use_shadow=o.data.use_shadow,hidden=o.hide_render,matrix=[list(r) for r in o.matrix_world]) for o in scene.objects if o.type=='LIGHT']
        color={k:getattr(scene.view_settings,k) for k in ['view_transform','look','exposure','gamma','view_settings'] if hasattr(scene.view_settings,k)}
        camera=dict(projection='ORTHO',matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,
                    frame=scene.frame_current,active_shape_keys={},lighting=lights,color_management=color,resolution=[640,640],pixel_aspect=[1,1],lens_shift=[cam.data.shift_x,cam.data.shift_y],yaw=yaw,pitch=pitch)
        semantic=dict(camera=camera,material=tree_state(mat.node_tree),world=tree_state(scene.world.node_tree),lighting=lights,color=color,render=dict(engine=scene.render.engine,transparent=scene.render.film_transparent))
        key=(mode,view)
        if state=='09':reference_states[key]=semantic
        else:assert semantic==reference_states[key],(key,'actual pair setup differs')
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();evaluated=np.asarray([v.co[:] for v in ev.vertices],np.float32);body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
        assert np.array_equal(evaluated,data['world'])
        path=O/(state+'-'+mode+'-'+view+'.png')
        row=dict(state=state,mode=mode,view=view,path=str(path),native=dict(path=str(native),sha256=nativehash),payload=dict(path=str(npz),sha256=sha(npz)),
                 actual_raw_evaluated_f32_sha256=hashlib.sha256(evaluated.tobytes()).hexdigest(),actual_triangles_sha256=hashlib.sha256(data['triangles'].tobytes()).hexdigest(),
                 camera=camera,actual_semantic_state=semantic,semantic_sha256=digest(semantic),renderer_sha256=sha(__file__),
                 provenance='Freshly opened saved small static native. No R3b/private context; runtime same declared camera crop only. Native not saved by capture.',
                 geometry_mutated_after_open=False,native_saved_by_renderer=False,scope='Headless static upperbody design guide; no productionUV/rig/fullbody integration.')
        if not dry:
            assert not path.exists();write(O/(path.stem+'-pre-render.json'),row);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
            assert np.array_equal(np.asarray([v.co[:] for v in body.data.vertices],np.float32),data['world']) and tree_state(mat.node_tree)==semantic['material']
            assert sha(native)==nativehash;row['sha256']=sha(path)
        allrows.append(row)
        if not dry:write(O/'render-records.json',allrows)
        print('SHOULDER11_'+('PREFLIGHT' if dry else 'ACTUAL')+' '+state+' '+mode+' '+view,flush=True)
    assert sha(native)==nativehash
assert gray_states['09']==gray_states['11'] and len(allrows)==16
for path,h in read(P/'protected-input-hashes.json').items():assert sha(path)==h,path
if dry:write(P/'paired-preflight.json',dict(status='PASS sixteen saved-native exact paired fixtures; no render',jobs=allrows,geometry_variants=1,render_called=False))
print('SHOULDER11_PAIRED_PREFLIGHT_PASS' if dry else 'SHOULDER11_ACTUAL16_DONE_GPU_RELEASE',flush=True)
