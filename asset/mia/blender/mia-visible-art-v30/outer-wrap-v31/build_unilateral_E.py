"""Reuse proven per-side Close geometry for unilateral Close correction."""
import bpy,json,sys,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent/'mia-eye-lash-v29'))
from audit_mesh_helpers import snapshot
D=P/'Mia_OuterOrbit_v31_D.blend';assert hashlib.sha256(D.read_bytes()).hexdigest()=='29f4905abde7a4c88da4eb939e114ff15f87053fc033ea2b40e2abaefe379d88'
bo,_,bm,bi=snapshot(D);master=bpy.data.objects['MIA_V27_Foundation_Face'];changed=[]
for side,suffix in [(-1,'R'),(1,'L')]:
    ob=bpy.data.objects['V28G_InnerLid_'+str(side)]
    for key in ob.data.shape_keys.key_blocks[42:]:
        fc=next(d for d in ob.data.shape_keys.animation_data.drivers if d.data_path=='key_blocks['+json.dumps(key.name)+'].value');dr=fc.driver;old=dr.expression;peak=int(key.name.rsplit('_',1)[1])/1000
        assert len(dr.variables)==1 and dr.variables[0].name=='v'
        u=dr.variables.new();u.name='u';u.type='SINGLE_PROP';u.targets[0].id_type='KEY';u.targets[0].id=master.data.shape_keys;u.targets[0].data_path='key_blocks['+json.dumps('Face.M_F00_000_00_Fcl_EYE_Close_'+suffix)+'].value'
        dr.expression='max(0.0, 1.0 - abs(max(v, u) - '+str(peak)+') / 0.125)';changed.append({'owner':ob.name,'key':key.name,'before':old,'after':dr.expression,'side_control':'Face.M_F00_000_00_Fcl_EYE_Close_'+suffix})
out=P/'Mia_OuterOrbit_v31_E.blend';assert not out.exists();bpy.ops.wm.save_as_mainfile(filepath=str(out));ao,_,am,ai=snapshot(out);wallnames=['V28G_InnerLid_-1','V28G_InnerLid_1']
checks={'all_D_coordinates_exact_allowners':all(bo[n]['coordinates']==ao[n]['coordinates'] for n in bo),'all_nonwall_mesh_records_exact_D':all(bo[n]==ao[n] for n in bo if n not in wallnames),'all_wall_nondriver_fields_exact_D':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k!='drivers') for n in wallnames),'all_original42_drivers_exact_D':all(bo[n]['drivers'][:41]==ao[n]['drivers'][:41] for n in wallnames),'all_D_material_graphs_exact':bm==am,'all_D_images_exact':bi==ai}
assert all(checks.values()),checks
report={'input':str(D),'native':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':checks,'changed_drivers':changed,'method':'Driver-only extension: max(globalClose, matching unilateralCloseRorL) feeds same seven sampled per-side contactcorrectives. Affected wall/cap/iris endpointgeometry is bit-exact tobilateral counterpart. Oppositeside remainsneutral up tofewmicrons. No coordinate/key/material/UV changes. Singleglobal or singleunilateral controls validated separately; no arbitraryadditivecontrolclaim.','pending':'Dense bilateral plusunilateral interpolatedactualevaluatedaudit andactual R/L .5/1 render. D remains superseded pendingthisgate, notblanketPASS.'}
(P/'unilateral-E-build.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('UNILATERAL_E_SAVED',report['sha256'],checks)
