"""Guarded D-to-F2 geometry replay, no scene opening/saving/material transfer."""
import json,bpy
from pathlib import Path
import numpy as np

def apply_replay(path,include_cap=True):
 data=json.loads(Path(path).read_text());pending=[]
 assert data['material_transfer']['method'].startswith('UNCHANGED')
 for name,channels in data['owners'].items():
  if name=='MIA_V06_BODY_SKIN' and not include_cap:continue
  o=bpy.data.objects[name]
  for key,rows in channels.items():
   target=o.data.vertices if key=='mesh_cache' else o.data.shape_keys.key_blocks[key].data
   for row in rows:
    current=np.array(target[row['id']].co)
    assert np.max(abs(current-row['before']))<2e-7,(name,key,row['id'],'D baseline mismatch')
    pending.append((target[row['id']],row['after']))
 for vertex,after in pending:vertex.co=after
 for name in data['owners']:bpy.data.objects[name].data.update()
 bpy.context.view_layer.update()
 return {'changed_points':len(pending),'saved':False,'materials_transferred':False,'status':'REVIEW ONLY / ART UNAPPROVED'}
