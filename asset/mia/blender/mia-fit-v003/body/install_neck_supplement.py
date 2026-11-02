from pathlib import Path
import json,hashlib
import bpy
P=Path(__file__).resolve().parent;COLLECTION='MIA_v003_NeckGuide_R4Supplement'
def install(parent=None):
    file=P/'scaffold-fullbody/neck-supplement.json';data=json.loads(file.read_text());sha=hashlib.sha256(file.read_bytes()).hexdigest()
    if COLLECTION in bpy.data.collections:
        col=bpy.data.collections[COLLECTION];assert col.get('neck_data_sha256')==sha;return col
    col=bpy.data.collections.new(COLLECTION);(parent or bpy.context.scene.collection).children.link(col);col['neck_data_sha256']=sha;col['base_fullbody_sha256']=data['base_fullbody_guide_sha256'];col['purpose']=data['limits'];mat=bpy.data.materials.new('V003_GUIDE_Neck_Current');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.28,.58,1,1);out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
    for item in data['curves']:
        name='V003_GUIDE_NECK_'+item['name'];cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=.00035;cu.bevel_resolution=2;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(item['points'])-1)
        for p,co in zip(sp.bezier_points,item['points']):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
        sp.use_cyclic_u=item['closed'];ob=bpy.data.objects.new(name,cu);col.objects.link(ob);cu.materials.append(mat);ob.show_in_front=True;ob['guide_only']=True
    rings=data['rings'];nc=12;me=bpy.data.meshes.new('V003_GUIDE_NECK_controlnet');me.from_pydata([p for r in rings for p in r],[],[(i*nc+j,i*nc+(j+1)%nc,(i+1)*nc+(j+1)%nc,(i+1)*nc+j) for i in range(3) for j in range(nc)]);me.update();ob=bpy.data.objects.new(me.name,me);col.objects.link(ob);ob.display_type='WIRE';ob.show_wire=ob.show_all_edges=True;ob.hide_render=True;ob['guide_only']=True;col.hide_render=True;return col
