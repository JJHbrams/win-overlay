"""Importable guarded recipe. Root may call apply_replay on its isolated scene.
No automatic scene opening, saving, or live operation occurs on import.
"""
import json,bpy
from pathlib import Path
import numpy as np
def apply_replay(path,include_cap=True):
 data=json.loads(Path(path).read_text());pending=[]
 for name,channels in data['owners'].items():
  if name=='MIA_V06_BODY_SKIN' and not include_cap:continue
  o=bpy.data.objects[name]
  for key,rows in channels.items():
   target=o.data.vertices if key=='mesh_cache' else o.data.shape_keys.key_blocks[key].data
   for row in rows:
    current=np.array(target[row['id']].co);assert np.max(abs(current-row['before']))<2e-7,(name,key,row['id'],'baseline mismatch')
    pending.append((target[row['id']],row['after']))
 for vertex,after in pending:vertex.co=after
 for name in data['owners']:bpy.data.objects[name].data.update()
 with bpy.data.libraries.load(data['candidate']['path'],link=False) as (src,dst):dst.materials=[data['material_transfer']['material']]
 bpy.data.objects['MIA_V14_SculptedSkin'].data.materials[7]=dst.materials[0]
 bpy.context.view_layer.update()
 return {'changed_points':len(pending),'saved':False,'status':'WORKING CANDIDATE / ART UNAPPROVED'}
