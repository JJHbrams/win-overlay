import bpy,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'integration-wip-8-review/Mia_ReferenceFinish_v22.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
skin=bpy.data.objects['MIA_V14_SculptedSkin'];mat=skin.data.materials[7]
def value(s):
 try:
  v=s.default_value
  return list(v) if hasattr(v,'__len__') else v
 except: return None
data={'source':str(SOURCE),'material':mat.name,'nodes':[],'links':[],'maps':{}}
for n in mat.node_tree.nodes:
 d={'name':n.name,'type':n.bl_idname,'inputs':{s.name:value(s) for s in n.inputs}}
 if n.type=='TEX_IMAGE' and n.image:
  im=n.image;d['image']={'name':im.name,'filepath':im.filepath,'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None}
  if 'FINISH8_' in n.name:
   px=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(px);px=px.reshape(-1,4)
   data['maps'][n.name]={'min':px.min(0).tolist(),'max':px.max(0).tolist(),'mean':px.mean(0).tolist(),'nonzero':int((px[:,0]>.01).sum()),'q':np.quantile(px[:,0],[.5,.9,.99,.999]).tolist()}
 if n.type=='VALTORGB':d['ramp']=[{'pos':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
 data['nodes'].append(d)
data['links']=[[[l.from_node.name,l.from_socket.name],[l.to_node.name,l.to_socket.name]] for l in mat.node_tree.links]
(ROOT/'material-diagnosis.json').write_text(json.dumps(data,indent=2))
print(json.dumps({'material':mat.name,'maps':data['maps']}))
