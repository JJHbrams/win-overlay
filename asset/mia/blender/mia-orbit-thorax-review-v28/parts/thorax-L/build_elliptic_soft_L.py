"""L: whole breast soft mass from a curved footprint on the exact G3 core.

Unlike I/J/K, no upper field or shared lower-row trajectory is inherited.
The smooth elliptic attachment narrows at its poles. Its positive outward
cap travels down/under toward the lower pole; this is an actual vector
deformation, with a continuous root and rounded transverse lower envelope.
The footprint and gravity parameters are a stylized nude inference, not a
literal tracing of the source's sports-bra edge.
"""
import bpy,numpy as np,json,hashlib,ast
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;O=P/'source-soft-L';O.mkdir(exist_ok=True)
CORE=P/'core-first-G3/Mia_G3_TrueCore.blend';SKIN=O/'Mia_L_CorePlusBreast.blend';assert not SKIN.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=np.load(P/'source-soft-I/actual-core-plus-soft.npz');C=np.load(P/'core-first-G3/true-core-plus-soft.npz')
core=D['core_world'];baseline=D['baseline_world'];mat=D['matrix'];base=np.load(P/'inspection.npz')['basis']
Z=C['section_z'];AA=C['core_halfwidth'];FRONT=C['core_front'];BACK=C['core_back']
tree=ast.parse((P/'build_radial_thorax_B.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mono'],type_ignores=[]),'mono','exec'))
offset=np.zeros_like(core);records=[]
for i,(x,y,z) in enumerate(core):
 if i>=3957 or not(1.244<z<1.342):continue
 a=mono(z,Z,AA);fr=mono(z,Z,FRONT);ba=mono(z,Z,BACK);cy=(fr+ba)/2;depth=(ba-fr)/2
 if y>=cy:continue
 u=abs(x+.0004777)/a;eta=(z-1.293)/.049
 # The upper root inclines laterally and tapers into the pectoral/axillary
 # fan. The lower footprint remains a curved ellipse, not a level row.
 center=.49+.045*max(eta,0);width=.44*(1-.15*max(eta,0));q=(u-center)/width;r2=q*q+eta*eta
 if r2>=1:continue
 w=(1-r2)**1.5
 direction=np.array([(x+.0004777)/(a*a),(y-cy)/(depth*depth),0.]);direction/=np.linalg.norm(direction)
 offset[i]=direction*(.061*w)
 # Downward relocation of the cap gives lower fullness, then an actual
 # rolled return below its attachment. The same w shrinks across width,
 # so root corners rise and fade instead of forming J's horizontal floor.
 offset[i,2]=-.018*w-.055*w*max(-eta,0)
 records.append({'index':i,'core_world':[x,y,z],'u':u,'q':q,'eta':eta,'footprint_radius_squared':r2,'cap_weight':w,'offset_world':offset[i].tolist(),'skin_world':(core[i]+offset[i]).tolist()})
skin=core+offset;local_t=offset@np.linalg.inv(mat[:3,:3]).T
bpy.ops.wm.open_mainfile(filepath=str(CORE),use_scripts=False);o=bpy.data.objects['MIA_V27_SharedHeadBody'];m=o.data;ti=np.flatnonzero(np.linalg.norm(local_t,axis=1)>1e-9)
for k in m.shape_keys.key_blocks:
 for i in ti:k.data[int(i)].co+=Vector(local_t[i])
for i in ti:m.vertices[int(i)].co=m.shape_keys.key_blocks[0].data[int(i)].co
o['MIA_ThoraxConstruction']='L: exact corrected G3 ribcage/pectoral core + independent width-curved elliptic breast footprint with positive cap and 3D lower-pole roll; no I/J/K tissue inherited'
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SKIN))
delta=(skin-baseline)@np.linalg.inv(mat[:3,:3]).T;idx=np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-8)
np.savez_compressed(O/'thorax-L-delta.npz',indices=idx,local_delta=delta[idx],world_delta=skin[idx]-baseline[idx],baseline_local=base[idx],baseline_world=baseline[idx],full_baseline=base)
np.savez_compressed(O/'actual-core-plus-soft.npz',baseline_world=baseline,core_world=core,tissue_offset_world=offset,skin_world=skin,triangles=D['triangles'],matrix=mat)
report={'actual_unchanged_core':{'path':str(CORE),'sha256':sha(CORE)},'skin':{'path':str(SKIN),'sha256':sha(SKIN)},'core_changed':False,'inherited_I_J_K_tissue':False,'method':'One smooth elliptical attachment chart per breast on actual G3 cage. Positive cap moves outward and down/under; its weight varies in both width and height, creating a rounded lower envelope and rising/fading root corners. C1 zero-offset attachment, no constant-height lower row.','source_constraints':'Uniform-SRT supported apex height Z1.2646..1.2832; relative waist projection24.9..32px under recorded camera; source bra masks exact nude attachment. Actual evaluated source/projection and 3D review required.','controls':{'footprint_center_core_z':1.293,'footprint_vertical_radius':.049,'footprint_center_u':.49,'footprint_halfwidth_u':.44,'upper_center_lateral_drift_u':.045,'upper_width_taper':.15,'cap_power':1.5,'normal_magnitude':.061,'central_drop':.018,'lower_roll':.055},'soft_records':records,'max_explicit_offset_m':float(np.linalg.norm(offset,axis=1).max()),'sum_error_m':float(abs(core+offset-skin).max()),'status':'UNREVIEWED L whole-soft-mass construction; source/actual evaluated normals/intersection/3D review required'}
(O/'construction.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('L_SOFT_SAVED',len(records),'soft stations',flush=True)
