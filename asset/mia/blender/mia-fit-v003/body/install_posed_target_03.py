"""Private static posed02; finite anterior fairing, original scene untouched."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
P=Path(__file__).resolve().parent;COLLECTION='MIA_v003_PosedWorkingTarget_03';NAME='V003_PosedWorkingBody_03'
def build(source=None):
    source=source or bpy.data.objects['MIA_V27_SharedHeadBody'];path=P/'posed-target/target-03.npz';sha=hashlib.sha256(path.read_bytes()).hexdigest();d=np.load(path);assert len(source.data.vertices)==4647
    if COLLECTION in bpy.data.collections:
        col=bpy.data.collections[COLLECTION];assert col.get('target_data_sha256')==sha;return bpy.data.objects[NAME]
    col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col);col['target_data_sha256']=sha;col['purpose']='STATIC canonical frame1 connected anterior fairing hypothesis. Original rig/47 keys untouched; no motion/ART approval.';ob=source.copy();ob.data=source.data.copy();ob.name=NAME;ob.data.name=NAME+'_Mesh';assert ob.data is not source.data
    if ob.data.shape_keys:
        assert ob.data.shape_keys is not source.data.shape_keys;ob.shape_key_clear()
    ob.animation_data_clear();arm=[m for m in ob.modifiers if m.type=='ARMATURE'];assert len(arm)==1 and ob.modifiers[0]==arm[0];ob.modifiers.remove(arm[0]);ob.data.vertices.foreach_set('co',d['target_local'].astype(np.float32).ravel());ob.data.update();col.objects.link(ob);col.hide_render=True;ob['static_posed_target']=True;ob['source_owner']=source.name;ob['target_data_sha256']=sha;ob['no_armature_or_shape_key_replay']=True;bpy.context.view_layer.update();return ob
