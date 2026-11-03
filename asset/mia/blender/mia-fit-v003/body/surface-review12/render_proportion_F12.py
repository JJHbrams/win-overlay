"""Root-granted E/F paired12 UNSAVED gray actuals. No saves/shape variants."""
from pathlib import Path
import sys,json
import bpy,numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_review,review_fixture as fixture
O=P/'proportion-F-lattice/gray-actuals';O.mkdir(exist_ok=True);assert not (O/'render-records.json').exists()
cpu=json.loads((P/'proportion-F-lattice/CPU-proof.json').read_text());assert cpu['local_J_min']>=.25 and not cpu['new_nonadjacent_intersections'] and cpu['protected_vertices_byte_exact']
installed=json.loads((P/'installed-source-F-proof.json').read_text());assert installed['source_old_UV_active_state']==installed['installed_old_UV_active_state']
source=Path(bpy.data.filepath);native_sha=fixture.sha(source);assert native_sha=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
objects={};reports={};paths={'E':P/'joined-expanded-E.npz','F':P/'proportion-F-lattice/geometry.npz'}
for state in ['E','F']:
    ob,proof=install_review.apply(geometry_path=paths[state],atlas_path=P/'atlas-E.npz',proof_path=O/(state+'-installed-source.json'),packing_path=O/(state+'-head-normal-packing.json'));ob.name='MIA_Review12_'+state+'_GrayComponent';ob.hide_render=True;objects[state]=ob;reports[state]=proof
scene=bpy.context.scene;fixture.setup(scene);fixture.hair_visibility(scene,False);pose=fixture.pose(scene)
jobs=[('front',0,0,fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES),('profile',90,0,fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES),('back',180,0,fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES),('oblique',30,0,fixture.FULL_TARGET,fixture.FULL_SCALE,fixture.FULL_RES),('high',40,25,(0,-.015,1.335),.65,(800,800)),('low',-40,-25,(0,-.015,1.335),.65,(800,800))]
rows=[]
for view,yaw,pitch,target,scale,res in jobs:
    fixture.aim(scene,yaw,pitch,target,scale,res)
    for state in ['E','F']:
        for name,ob in objects.items():ob.hide_render=name!=state
        assert fixture.pose(scene)==pose
        body=objects[state];data=np.load(paths[state]);assert np.array_equal(np.asarray([v.co[:] for v in body.data.vertices],np.float32),data['world']);data.close()
        file=O/(state+'-'+view+'.png');row=dict(state=state,view=view,path=str(file),actual_source_native=dict(path=str(source),sha256=native_sha),saved_review_native=False,unsaved_component_payload=dict(path=str(paths[state]),sha256=fixture.sha(paths[state])),camera=fixture.record(scene),fixture_scope='Matching E/F gray BODYonly; savedR3b head materials/other actors retained; hairOFF exposes fullbody and shoulders.',body_gray=dict(base_color_linear=[.23,.23,.23,1],roughness=.85),source_preservation=reports[state],F_applied_nominal=cpu['analytic_amplitude_limit'] if state=='F' else None)
        scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);row['sha256']=fixture.sha(file);rows.append(row);(O/'render-records.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n');print('F_PAIRED_ACTUAL',state,view,flush=True)
assert len(rows)==12 and fixture.sha(source)==native_sha
print('F_PAIRED12_DONE_GPU_RELEASE',flush=True)
