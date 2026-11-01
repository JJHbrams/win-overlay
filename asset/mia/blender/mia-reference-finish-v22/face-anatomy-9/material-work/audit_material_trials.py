import bpy,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from apply_material_identity import snapshots
SOURCE=ROOT.parents[1]/'integration-wip-8-review/Mia_ReferenceFinish_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slots():return {o.name:[m.name if m else None for m in o.data.materials] for o in bpy.data.objects if o.type=='MESH'}
def maps(mat):return {n.name:{'name':n.image.name,'hash':hashlib.sha256(n.image.packed_file.data).hexdigest(),'colorspace':n.image.colorspace_settings.name,'size':list(n.image.size)} for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.name.startswith('FINISH8_')}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False);baseline=snapshots();bs=slots();bm=maps(bpy.data.objects['MIA_V14_SculptedSkin'].data.materials[7]);records={}
for variant in ['m1','m2','m3','m4']:
 native=ROOT/('trial-'+variant)/'Mia_FaceIdentity9_Material.blend';bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
 assert snapshots()==baseline,variant
 actual=slots()
 for owner,sl in bs.items():
  for index,name in enumerate(sl):
   if owner=='MIA_V14_SculptedSkin' and index==7:continue
   assert actual[owner][index]==name,(variant,owner,index)
 mat=bpy.data.objects['MIA_V14_SculptedSkin'].data.materials[7];mm=maps(mat);assert mm==bm
 light=mat.node_tree.nodes['PigmentTimesControlledLight'];assert light.inputs[1].links[0].from_node.name=='IDENTITY9_SecondaryFoldPigment'
 records[variant]={'native':str(native),'sha256':sha(native),'mesh_uv_topology_keys_transforms_exact':True,'only_skin_slot7_assignment_changed':True,'existing_packed_maps_exact':True,'consumed_route':light.inputs[1].links[0].from_node.name,'fold_method':'13-sample lower-lid UV FloatCurve, lateral endpoints, Gaussian falloff' if variant in ('m3','m4') else 'existing FineLineMask with a UV shift','limits':'Neutral fixed front/oblique and color-only render evidence is separate; new eye geometry, blink and remaining views not validated here. No ART PASS.'}
(ROOT/'saved-trial-audit.json').write_text(json.dumps({'source':{'path':str(SOURCE),'sha256':sha(SOURCE)},'records':records},indent=2));print('AUDIT_TRIALS_DONE')
