"""CPU API check of an UNASSIGNED temporary material; no save or render."""
import bpy,numpy as np,json,hashlib,ast
from pathlib import Path
P=Path(__file__).parent.resolve();S=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');expected='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(S)==expected
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);owner=bpy.data.objects['MIA_V27_SharedHeadBody'];images={}
for key,path,cs in [('art',P/'art-pigment-B/Mia_UVPigment_Art_B.png','sRGB'),('features',P/'native-control-maps-final/V29_FeatureControls_RGB.exr','Non-Color'),('response',P/'native-control-maps-final/V29_LightReflectControls_RGB.exr','Non-Color')]:
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=cs;images[key]=im
tree=ast.parse((P/'apply_surface_after_eye_gate.py').read_text());wanted={'scalar','graph','digest','material'};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted],type_ignores=[]),'staging_api_functions','exec'))
newmaterials=[];old=owner.material_slots[0].material;before=digest(graph(old.node_tree));mat=material(old,'V29_UNASSIGNED_API_CHECK');assert owner.material_slots[0].material==old and before==digest(graph(old.node_tree));bpy.context.view_layer.update()
drivers=[]
for fc in mat.node_tree.animation_data.drivers:
 drivers.append({'path':fc.data_path,'expression':fc.driver.expression,'valid':fc.driver.is_valid,'variables':[(v.name,v.targets[0].id.name,v.targets[0].data_path) for v in fc.driver.variables]})
 assert fc.driver.is_valid
report={'native_sha256_before':expected,'native_sha256_after':sha(S),'unassigned_material_only':True,'native_saved':False,'rendered':False,'original_face_graph_unchanged':True,'new_material_node_count':len(mat.node_tree.nodes),'actual_specular_bsdf':{'type':mat.node_tree.nodes['V29_ACTUAL_SpecularBSDF'].bl_idname,'input_names':[x.name for x in mat.node_tree.nodes['V29_ACTUAL_SpecularBSDF'].inputs]},'drivers':drivers,'images':{k:{'size':list(im.size),'file_depth':im.depth,'colorspace':im.colorspace_settings.name} for k,im in images.items()},'status':'API construction validated only. Material not assigned to any owner; no active-render response or ART acceptance established.'};assert report['native_sha256_after']==expected
(P/'surface-staging-api-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('SURFACE_UNASSIGNED_API_VALID',json.dumps(report),flush=True)
