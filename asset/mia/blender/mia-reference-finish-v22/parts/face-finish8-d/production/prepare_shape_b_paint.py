from pathlib import Path
import bpy,numpy as np,json
ROOT=Path(__file__).resolve().parent
code=(ROOT/'render_paint_plate.py').read_text().replace("'shape-a/paint-input'","'shape-b/paint-input'").replace("'shape-a/Mia_FaceFinish8_CompactSectionsA.blend'","'shape-b/Mia_FaceFinish8_NasalBuccalB.blend'")
exec(compile(code,str(ROOT/'render_paint_plate.py'),'exec'))
im=bpy.data.images['MIA_V22_Face_BaseColor_LINEAR_2048.001'];p=np.empty(len(im.pixels),np.float32);im.pixels.foreach_get(p);np.save(OUT/'old-pigment-linear.npy',p.reshape(im.size[1],im.size[0],4))
m=bpy.data.materials['MIA_V22_Finish5_LocalUnderEye'];details={'ramps':{n.name:[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] for n in m.node_tree.nodes if n.type=='VALTORGB'},'nodes':{n.name:{'type':n.type,'uv_map':n.uv_map if n.type=='UVMAP' else None} for n in m.node_tree.nodes}}
(OUT/'shader-details.json').write_text(json.dumps(details,indent=2));print('PAINT_PREP_DONE')
