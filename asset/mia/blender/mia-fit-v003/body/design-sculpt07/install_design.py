"""Static merged design and a private masked ORIGINAL context; no native save."""
from pathlib import Path
import hashlib,json
import bpy,numpy as np
P=Path(__file__).resolve().parent
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
NAME='MIA_v003_DesignSculpt07_UNSELECTED'
def coords(data):
    a=np.empty(len(data)*3,np.float32);data.foreach_get('co',a);return a.reshape(-1,3)
def fingerprint(source):
    raw={k.name:hashlib.sha256(coords(k.data).tobytes()).hexdigest() for k in source.data.shape_keys.key_blocks}
    face={k.name:hashlib.sha256(coords(k.data)[3957:].tobytes()).hexdigest() for k in source.data.shape_keys.key_blocks}
    return dict(keys=raw,Face690=face,vertices=len(source.data.vertices),polygons=len(source.data.polygons))
def build(gray,transparent):
    original=bpy.data.objects['MIA_V27_SharedHeadBody'];before=fingerprint(original);d=np.load(P/'sculpt07.npz')
    me=bpy.data.meshes.new(NAME+'_Mesh');me.from_pydata(d['world'].tolist(),[],d['triangles'].tolist());me.update();me.materials.append(gray)
    for q in me.polygons:q.use_smooth=True
    design=bpy.data.objects.new(NAME,me);bpy.context.scene.collection.objects.link(design);design['status']='STATIC new design; no keys/UV/weights; not selected'
    # Keep the original raw mesh and all modifier/key evaluation in context.
    # Only per-material visibility changes on the PRIVATE copy. Face690 excluded.
    context=original.copy();context.data=original.data.copy();context.name='Sculpt07_ORIGINAL_CONTEXT_SEAMS_UNVERIFIED';bpy.context.scene.collection.objects.link(context)
    for i in range(len(context.data.materials)):context.data.materials[i]=gray
    slot=len(context.data.materials);context.data.materials.append(transparent)
    mapping=CAN/'blender/mia-fit-v003/body/inputs/mapping-frame1.npz';assert hashlib.sha256(mapping.read_bytes()).hexdigest()=='c36230677c7491af3ec35f1cd0dce579647ce3bad9e4c5db5495304fbd567045'
    q=np.load(mapping)['q0_world'];masked=[]
    for poly in context.data.polygons:
        ids=np.array(poly.vertices[:]);center=q[ids].mean(0)
        if ids.max()<3957 and 1.045<center[2]<1.505 and abs(center[0])<.295:
            poly.material_index=slot;masked.append(poly.index)
    assert fingerprint(original)==before and fingerprint(context)==before
    original.hide_render=True;context.hide_render=False;design.hide_render=False
    report=dict(original_fingerprint_before=before,original_fingerprint_after=fingerprint(original),private_context_raw_all_keys_exact=True,private_context_Face690_exact=True,original_mesh_keys_untouched=True,context_mask_polygons=len(masked),context_mask_definition='Original posed q0_world polygon centroid 1.045<Z<1.505, |X|<.295; raw ids<3957 only. Original topology retained with transparent material mask.',context_seams='UNVERIFIED, separate private source context and design, not final watertight body integration.',new_design_no_keys_uv_weights=True,native_saved=False)
    (P/'preservation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return design,context,before
