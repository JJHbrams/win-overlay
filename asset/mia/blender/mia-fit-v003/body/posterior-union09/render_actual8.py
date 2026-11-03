"""Root-token-only eight actual09 views; --cpu-only performs no render.

Reuses frozen E's actual setup read-only. All installer/preflight output is
redirected here; the private design actor receives the frozen09 vertices once.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import types,json,hashlib,copy
import numpy as np
OUT=Path(__file__).resolve().parent
CANONICAL=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
E=CANONICAL/'blender/mia-fit-v003/body/design-sculpt07/E'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit09=json.loads((OUT/'CPU-audit.json').read_text(encoding='utf-8'))
assert audit09['finite'] and audit09['main_lower_passage_open'] and audit09['breast_surface']['exact'] and not audit09['new_nonadjacent_intersections']
payload=OUT/'posterior09.npz';payload_sha=sha(payload);assert payload_sha==audit09['mesh_sha256']
protected=json.loads((OUT/'protected-input-hashes.json').read_text(encoding='utf-8'))
for path,h in protected.items():assert sha(path)==h
INSTALL=types.ModuleType('posterior09_private_context_install');INSTALL.__file__=str(OUT/'install_design.py');INSTALL.OUT=OUT
install_code=(OUT/'install_design.py').read_text(encoding='utf-8')
exec(compile(install_code,str(OUT/'install_design.py'),'exec'),INSTALL.__dict__)
base_renderer=E/'render_core_six.py'
setup=base_renderer.read_text(encoding='utf-8').split('for fixture in old:')[0]
setup=setup.replace('import install_design','install_design=INSTALL').replace("(P/'preservation.json')","(OUT/'preservation.json')").replace("O=P/'actual-E'","O=OUT/'actual8'")
scope={'__file__':str(base_renderer),'INSTALL':INSTALL,'OUT':OUT,'__name__':'posterior09_frozen_E_setup'}
exec(compile(setup,str(base_renderer),'exec'),scope)
globals().update({k:scope[k] for k in ['bpy','s','design','context','original','original_fingerprint','evaluated','gray','transparent','bs','bg','cam','lamps','rig','master','pose','keys','fp','N','NATIVE_SHA']})
from mathutils import Vector
import math
data=np.load(payload);assert len(design.data.vertices)==len(data['world'])
assert np.array_equal(np.asarray([p.vertices[:] for p in design.data.polygons],np.int32),data['triangles'])
design.name='MIA_v003_PosteriorUnion09_UNSELECTED';design.data.vertices.foreach_set('co',data['world'].ravel());design.data.update();bpy.context.view_layer.update()
normal=bpy.data.materials.new('E_Audit_ActualGeometryNormalEmission');normal.use_nodes=True;nn=normal.node_tree.nodes;nn.clear()
geo=nn.new('ShaderNodeNewGeometry');vm=nn.new('ShaderNodeVectorMath');vm.operation='MULTIPLY_ADD';vm.inputs[1].default_value=(.5,.5,.5);vm.inputs[2].default_value=(.5,.5,.5);em=nn.new('ShaderNodeEmission');oo=nn.new('ShaderNodeOutputMaterial')
normal.node_tree.links.new(geo.outputs['Normal'],vm.inputs[0]);normal.node_tree.links.new(vm.outputs['Vector'],em.inputs['Color']);normal.node_tree.links.new(em.outputs[0],oo.inputs['Surface'])
# Frozen E created English node names. Current UI locale localizes new names;
# assign the exact frozen English labels on NEW diagnostic graphs only.
for tree in [gray.node_tree,transparent.node_tree,normal.node_tree,s.world.node_tree]:
    for node in tree.nodes:node.name=node.bl_label
prior_audit=json.loads((E/'actual-audit/render-records.json').read_text(encoding='utf-8'))
prior_core=json.loads((E/'actual-E/render-records.json').read_text(encoding='utf-8'))
jobs=[('gray','rear140'),('normal','rear140'),('gray','back180'),('gray','rear220'),('gray','rearhigh140'),('gray','rearlow140'),('gray','front'),('gray','profile')]
dry='--cpu-only' in sys.argv;O=OUT/'actual8';O.mkdir(exist_ok=True);records=[]
if not dry:assert not (O/'render-records.json').exists(),'Do not overwrite actual evidence'
def actual_vertices():return np.asarray([v.co[:] for v in design.data.vertices],np.float32)
for mode,view in jobs:
    previous=next(r for r in (prior_core if view in ['front','profile'] else prior_audit) if r['view']==view and (r.get('state','E')=='E') and r.get('mode','gray')==mode)
    q=previous['camera'];yaw,pitch=q['yaw'],q['pitch'];target=Vector((0,-.035,1.275));a,b=math.radians(yaw),math.radians(pitch)
    cam.location=target+Vector((2*math.sin(a)*math.cos(b),-2*math.cos(a)*math.cos(b),2*math.sin(b)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.4;s.render.resolution_x=s.render.resolution_y=640
    mat=normal if mode=='normal' else gray;design.data.materials[0]=mat
    for i in range(len(context.data.materials)-1):context.data.materials[i]=mat
    bpy.context.view_layer.update()
    camera=copy.deepcopy(q);camera.update(projection=cam.data.type,matrix=[list(r) for r in cam.matrix_world],ortho_scale=cam.data.ortho_scale,clip_start=cam.data.clip_start,clip_end=cam.data.clip_end,resolution=[640,640],pixel_aspect=[1,1],frame=s.frame_current)
    assert camera==q,(view,'camera differs')
    actual_lights=[dict(name=o.name,hidden=o.hide_render,energy=o.data.energy,size=o.data.size,use_shadow=o.data.use_shadow,matrix=[list(r) for r in o.matrix_world]) for o in s.objects if o.type=='LIGHT']
    old_lights=previous.get('actual_lights',previous.get('actual_all_light_flags_before_render'));assert len(old_lights)==len(actual_lights)
    for x,y in zip(actual_lights,old_lights):
        assert all(x[k]==y[k] for k in ['hidden','energy','size','use_shadow']) and np.max(abs(np.array(x['matrix'])-y['matrix']))<1e-7
    assert np.array_equal(actual_vertices(),data['world']) and np.array_equal(evaluated(design),data['world'])
    assert INSTALL.fingerprint(original)==original_fingerprint and np.array_equal(evaluated(original),evaluated(context))
    assert pose=={b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones} and keys=={k.name:k.value for k in master.data.shape_keys.key_blocks}
    material=fp.material_signature(mat)
    if material!=previous['actual_material_signature']:
        (OUT/'preflight-material-diff.json').write_text(json.dumps(dict(current=material,baseline=previous['actual_material_signature']),indent=2)+'\n',encoding='utf-8')
    assert material==previous['actual_material_signature'],(mode,view,'material differs')
    file=O/('09-'+mode+'-'+view+'.png')
    row=dict(state='09_UNSELECTED',mode=mode,view=view,path=str(file),camera=camera,baseline_E_render=dict(path=previous['path'],sha256=previous['sha256']),
        payload_sha256=payload_sha,actual_private_vertex_sha256=hashlib.sha256(actual_vertices().tobytes()).hexdigest(),
        actual_evaluated_private_vertex_sha256=hashlib.sha256(evaluated(design).tobytes()).hexdigest(),actual_material_signature=material,actual_transparency_signature=fp.material_signature(transparent),
        actual_visible_meshes=[o.name for o in s.objects if o.type=='MESH' and not o.hide_render],actual_lights=actual_lights,
        actual_pose_sha256=fp.json_digest(pose),actual_keys_sha256=fp.json_digest(keys),world=dict(color=list(bg.inputs['Color'].default_value),strength=bg.inputs['Strength'].default_value),color_management=previous['color_management'],
        original47_and_Face690_exact=True,entire_evaluated_original_context_exact=True,native_sha256=NATIVE_SHA,native_saved=False,head_scale_changed=False,
        renderer_sha256=sha(OUT/'render_actual8.py'),frozen_E_base_renderer_sha256=sha(base_renderer),own09_installer_sha256=sha(OUT/'install_design.py'),generated_diagnostic_node_names_match_frozen_English_E=True)
    row['actual_renderer_state_sha256']=fp.json_digest(row)
    if not dry:
        assert not file.exists();(O/(file.stem+'-pre-render.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8',newline='\n');s.render.filepath=str(file);bpy.ops.render.render(write_still=True)
        assert np.array_equal(actual_vertices(),data['world']) and fp.material_signature(mat)==material
        row['sha256']=sha(file);records.append(row);(O/'render-records.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8',newline='\n');print('POSTERIOR09_ACTUAL '+mode+' '+view,flush=True)
    else:records.append(row)
assert sha(N)==NATIVE_SHA and sha(payload)==payload_sha and len(records)==8
for path,h in protected.items():assert sha(path)==h,('Frozen D/E input changed',path)
if dry:(OUT/'render-preparation.json').write_text(json.dumps(dict(status='CPU exact8 camera/material/light/actual mesh/context preflight PASS',jobs=records,render_called=False,native_saved=False),indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_CPU_PREFLIGHT_PASS' if dry else 'POSTERIOR09_ACTUAL8_DONE_GPU_RELEASE',flush=True)
