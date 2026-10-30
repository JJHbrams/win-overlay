#!/usr/bin/env python3
"""Transient Blender import of the verified Victoria Rubin VRM reference."""
import argparse, hashlib, json, pathlib, sys
from mathutils import Vector
import bpy

def args():
    values=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument('--source',required=True); p.add_argument('--addon-runtime',required=True); p.add_argument('--output',required=True); p.add_argument('--expected-sha256',default='b1372131bdbf233f46320146d565f342a7e4f6f4b8f2aefb301f1a283ec07e1e'); return p.parse_args(values)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()
def bounds(obj):
    points=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def main():
    o=args(); source=pathlib.Path(o.source).resolve(); out=pathlib.Path(o.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    source_hash=sha(source)
    if source_hash.lower()!=o.expected_sha256.lower(): raise RuntimeError('source SHA-256 mismatch: expected %s got %s' % (o.expected_sha256,source_hash))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sys.path.insert(0,str(pathlib.Path(o.addon_runtime).resolve())); import addon_utils
    addon_utils.modules_refresh(); addon_utils.enable('io_scene_vrm',default_set=True,persistent=False)
    if bpy.context.preferences.addons.get('io_scene_vrm') is None: raise RuntimeError('io_scene_vrm preferences slot was not created in memory')
    result=bpy.ops.import_scene.vrm(filepath=str(source)); objects=[]
    for obj in bpy.data.objects:
        if obj.type not in {'MESH','ARMATURE'}: continue
        rec={'name':obj.name,'type':obj.type,'bounds':bounds(obj),'parent':obj.parent.name if obj.parent else None}
        if obj.type=='MESH': rec.update({'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),'materials':[m.name if m else None for m in obj.data.materials],'shape_keys':[k.name for k in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else []})
        else: rec['bones']=[b.name for b in obj.data.bones]
        objects.append(rec)
    report={'source':str(source),'source_sha256':source_hash,'operator_result':str(result),'objects':objects,'images':[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file)} for i in bpy.data.images],'note':'Reference import only; no Mia geometry adoption.'}
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'Victoria_Rubin_imported.blend'))
    if sha(source)!=source_hash: raise RuntimeError('source VRM changed during import')
    (out/'inventory.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8'); print(json.dumps({'operator_result':str(result),'objects':len(objects),'source_sha256':source_hash}))
if __name__=='__main__': main()
