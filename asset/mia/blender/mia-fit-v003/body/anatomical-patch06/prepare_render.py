"""Freeze a four-job derivative of the already verified gray fixture recipe."""
from pathlib import Path
import ast
P=Path(__file__).resolve().parent;B=P.parent
s=(B/'render_posed_target_01.py').read_text()
s=s.replace('P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import install_posed_target_01',"P=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(Path(__file__).resolve().parent));import install_prototype as install_posed_target_01")
s=s.replace("P/'posed-target/target-01.npz'","P/'anatomical-patch06/prototype06.npz'")
start=s.index('jobs=');end=s.index('\nfor mode,view',start)
s=s[:start]+"jobs=[('gray','front',0,0,'torso'),('gray','profile',85,0,'torso'),('gray','F2lowoblique',40,-8,'source-low'),('gray','rearoblique',140,-10,'torso')];O=P/'anatomical-patch06/actual-four';O.mkdir(exist_ok=True);records=[]\nguard=json.loads((P/'anatomical-patch06/cpu-guard.json').read_text());assert guard['prototype_sha256']==targetsha and guard['strict_nonadjacent_contacts']==0 and guard['finite']\n"+s[end:]
override="""    if framing=='source-low':
        source_data=json.loads((P/'source-binding/constraints.json').read_text());mpp=source_data['display_metric']['metres_per_pixel'];center=source_data['cameras']['F2']['body_axis_pixel_x']-887
        angle=math.radians(40);elev=math.radians(-8);right=Vector((math.cos(angle),math.sin(angle),0));up=Vector((-math.sin(angle)*math.sin(elev),math.cos(angle)*math.sin(elev),math.cos(elev)))
        target=Vector((0,-.018,0))-right*((center-443.5)*mpp);crown=1.692881464958191;target.z=(crown*math.cos(elev)-(443.5-11)*mpp-up.x*target.x-up.y*target.y)/up.z;dist=2.5
        cam.location=target+Vector((dist*math.sin(angle)*math.cos(elev),-dist*math.cos(angle)*math.cos(elev),dist*math.sin(elev)));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=mpp*887;s.render.resolution_x=s.render.resolution_y=887;bpy.context.view_layer.update()
"""
s=s.replace('    active=[o for o',override+'    active=[o for o')
s=s.replace("native_saved=False)","native_saved=False,prototype_status='DIAGNOSTIC UNSELECTED STATIC; migration/UV/rig UNVERIFIED; manualsourcebinding/tangent FAIL or UNVERIFIED',cpu_guard_sha256=sha(P/'anatomical-patch06/cpu-guard.json'))")
s=s.replace('assert len(records)==8','assert len(records)==4').replace('POSED_TARGET_01_ACTUAL8_DONE','PATCH06_ACTUAL4_DONE')
ast.parse(s)
(P/'render_four.py').write_text(s,encoding='utf-8')
print('PATCH06_RENDER_FOUR_PREPARED',flush=True)
