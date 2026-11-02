"""Add reversible, separate3D guide curves/loft control nets. No scene open/save."""
from pathlib import Path
import json,hashlib
import bpy
P=Path(__file__).resolve().parent;COLLECTION='MIA_v003_FullBodySourceScaffold_R4';PREFIX='V003_GUIDE_FULL4_'
def install():
    path=P/'scaffold-fullbody/guide-data.json';data=json.loads(path.read_text(encoding='utf-8'));data_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    if COLLECTION in bpy.data.collections:
        c=bpy.data.collections[COLLECTION];assert c.get('guide_schema')==1 and c.get('guide_revision')==data['revision'] and c.get('guide_data_sha256')==data_sha;return c
    col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col);col['guide_schema']=1;col['guide_revision']=data['revision'];col['guide_data_sha256']=data_sha;col['purpose']='Source-constrained inferred3D guide; NOT production body or uniqueCT recovery';col['reference_sha256']=data['reference_sha256'];mats={}
    for kind,color in data['colors'].items():
        rgb=tuple(int(color[i:i+2],16)/255 for i in [1,3,5]);mat=bpy.data.materials.new(PREFIX+kind);mat.diffuse_color=(*rgb,1);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*rgb,1);out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],out.inputs['Surface']);mats[kind]=mat
    for spec in data['curves']:
        name=PREFIX+spec['name'];assert name not in bpy.data.objects;cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=.00045;cu.bevel_resolution=2;sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(spec['points'])-1)
        for p,co in zip(sp.bezier_points,spec['points']):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
        sp.use_cyclic_u=bool(spec['closed']);ob=bpy.data.objects.new(name,cu);col.objects.link(ob);cu.materials.append(mats[spec['kind']]);ob['source_kind']=spec['kind'];ob['limitation']=spec['limitation'];ob['guide_only']=True;ob.show_in_front=True
    for label,key,kind in [('core_controlnet','core_loft_rings','structural_core'),('support_controlnet','support_loft_rings','garment')]:
        rings=data[key];verts=[p for r in rings for p in r];nr=len(rings);nc=len(rings[0]);faces=[(r*nc+j,r*nc+(j+1)%nc,(r+1)*nc+(j+1)%nc,(r+1)*nc+j) for r in range(nr-1) for j in range(nc)];name=PREFIX+label;me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mats[kind]);ob.display_type='WIRE';ob.show_wire=True;ob.show_all_edges=True;ob.hide_render=True;ob['guide_only']=True;ob['limitation']='Open inferred section/control loft, not a valid body surface or finished garment. No caps/internal anatomy inferred.'
    for spec in data['branch_controlnets']:
        name=PREFIX+spec['name'];me=bpy.data.meshes.new(name);me.from_pydata(spec['vertices'],[],spec['faces']);me.update();ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mats[spec['kind']]);ob.display_type='WIRE';ob.show_wire=ob.show_all_edges=True;ob.hide_render=True;ob['guide_only']=True;ob['limitation']=spec['limitation']
    col.hide_render=True
    return col
