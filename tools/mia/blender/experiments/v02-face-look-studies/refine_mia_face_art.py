"""Bounded Mia face-art study: existing expression rig/material owners only."""
import argparse, hashlib, json, os, sys
import bpy
from mathutils import Vector

FACE = "Mia_Face_AnimeTopology"

def args():
    raw=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True); p.add_argument('--output',required=True); p.add_argument('--render-dir',required=True)
    return p.parse_args(raw)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def fp(o):
    h=hashlib.sha256(); m=o.data
    for v in m.vertices:h.update(bytes(v.co))
    for uv in m.uv_layers.active.data:h.update(bytes(uv.uv))
    for k in m.shape_keys.key_blocks:
        h.update(k.name.encode())
        for p in k.data:h.update(bytes(p.co))
    return h.hexdigest(),[k.name for k in m.shape_keys.key_blocks]
def key(o,end,v):
    found=[k for k in o.data.shape_keys.key_blocks if k.name.endswith(end)]
    if len(found)!=1: raise RuntimeError('key '+end)
    found[0].value=v
def pose(o,blink=False,mouth_a=False):
    for k in o.data.shape_keys.key_blocks:
        if 'Fcl_EYE_' in k.name or 'Fcl_BRW_' in k.name or 'Fcl_MTH_' in k.name:k.value=0
    key(o,'Fcl_EYE_Close',1.0 if blink else .60); key(o,'Fcl_EYE_Natural',0); key(o,'Fcl_EYE_Sorrow',.10)
    # Existing brow/mouth channels supply the dry, sloped lid read; no coordinate edit.
    key(o,'Fcl_BRW_Angry',.22); key(o,'Fcl_MTH_Angry',.40); key(o,'Fcl_MTH_Neutral',.18)
    if mouth_a:key(o,'Fcl_MTH_A',1.0)
def camera(o):
    s=bpy.context.scene; c=bpy.data.cameras.new('MIA_FACE_ART_CAMERA'); co=bpy.data.objects.new(c.name,c); s.collection.objects.link(co); s.camera=co
    c.type='ORTHO'; c.ortho_scale=.30; co.location=(0,-.65,1.58); co.rotation_euler=((Vector((0,0,1.58))-co.location).to_track_quat('-Z','Y').to_euler())
    s.render.resolution_x=s.render.resolution_y=768; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; return co
def render(path): bpy.context.scene.render.filepath=path; bpy.ops.render.render(write_still=True)
def main():
    a=args(); inp=os.path.abspath(a.input); out=os.path.abspath(a.output); rd=os.path.abspath(a.render_dir)
    if inp==out:raise RuntimeError('refusing input overwrite')
    bpy.ops.wm.open_mainfile(filepath=inp); os.makedirs(rd,exist_ok=True)
    o=bpy.data.objects.get(FACE)
    if not o or len([x for x in bpy.context.scene.objects if x.visible_get() and x.name==FACE])!=1:raise RuntimeError('canonical face')
    before,names=fp(o); source=sha(inp); cam=camera(o)
    pose(o); bpy.ops.wm.save_as_mainfile(filepath=out)
    for label,blink,mouth in [('neutral',False,False),('blink',True,False),('mouthA',False,True)]:
        pose(o,blink,mouth); render(os.path.join(rd,'face_art_'+label+'_front.png')); cam.location=(.12,-.62,1.60); cam.rotation_euler=((Vector((0,0,1.58))-cam.location).to_track_quat('-Z','Y').to_euler()); render(os.path.join(rd,'face_art_'+label+'_3q.png')); cam.location=(0,-.65,1.58); cam.rotation_euler=((Vector((0,0,1.58))-cam.location).to_track_quat('-Z','Y').to_euler())
    pose(o)
    selected={k.name:k.value for k in o.data.shape_keys.key_blocks}
    after,names2=fp(o)
    if before!=after or names!=names2:raise RuntimeError('face invariant breach')
    bpy.ops.wm.save_as_mainfile(filepath=out)
    if selected.get('Face.M_F00_000_00_Fcl_MTH_A') != 0.0: raise RuntimeError('proof state leaked into saved neutral')
    with open(os.path.join(rd,'face_art_report.json'),'w') as f:json.dump({'status':'FACE_ART_STUDY_UNVERIFIED','source_sha_before_after':[source,sha(inp)],'fingerprint_before_after':[before,after],'shape_key_count':len(names),'selected_values':selected,'affected_regions':['existing EYE/BRW/MTH channels only; no face/body coordinates, UVs, materials, or new geometry']},f,indent=2)
if __name__=='__main__':main()
