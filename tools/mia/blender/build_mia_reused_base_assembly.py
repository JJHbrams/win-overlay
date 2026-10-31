"""Assemble detailed hair on the preserved 02:40 Mia facial/body foundation.

Skin topology/UV/original expressions remain authored independently. The hair
is an isolated design surface attached to the head bone, not a replacement face.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector


def load_helper(file, name):
    spec=importlib.util.spec_from_file_location(name,str(Path(__file__).with_name(file)))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_hair_design(src,dest):
    """UV-preserving first-pass hair extraction, explicitly not art-approved."""
    image=next(n.image for n in src.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
    w,h=image.size;pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4);uv=src.data.uv_layers.active;ids=[]
    for poly in src.data.polygons:
        t=sum((uv.data[i].uv for i in poly.loop_indices),Vector((0,0)))/poly.loop_total
        c=pixels[min(h-1,max(0,int(t.y*h))),min(w-1,max(0,int(t.x*w))),:3];q=src.matrix_world@poly.center;x,y,z=q
        warm=c[0]>.48 and c[0]-c[1]>.015 and c[0]-c[2]>.045 and y<-.015
        paint=1.405<z<1.548 and abs(x)<.113 and y>-.128
        if c.mean()<.46 and max(c)-min(c)<.16 and not warm and not paint:ids.append(poly.index)
    used=sorted({v for i in ids for v in src.data.polygons[i].vertices});mapping={v:j for j,v in enumerate(used)}
    me=bpy.data.meshes.new('MIA_PIXAL_HAIR_DESIGN_MESH');me.from_pydata([src.data.vertices[i].co[:] for i in used],[],[[mapping[v] for v in src.data.polygons[i].vertices] for i in ids])
    for layer in src.data.uv_layers:
        new=me.uv_layers.new(name=layer.name)
        for ni,oi in enumerate(ids):
            for a,b in zip(me.polygons[ni].loop_indices,src.data.polygons[oi].loop_indices):new.data[a].uv=layer.data[b].uv
    for m in src.data.materials:me.materials.append(m)
    for p,source_i in zip(me.polygons,ids):p.material_index=src.data.polygons[source_i].material_index;p.use_smooth=True
    ob=bpy.data.objects.new('MIA_PIXAL_HAIR_DESIGN_SEPARATE',me);dest.objects.link(ob);ob.matrix_world=src.matrix_world.copy();ob['source_vertices']=used;ob['source_polygons']=ids;ob['semantic_status']='design extraction; visible boundary FAIL; manual cleanup required'
    return ob


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--hair-source',required=True);p.add_argument('--output',required=True);p.add_argument('--proofs',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);src=Path(a.input).resolve();hair_source=Path(a.hair_source).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    before={str(src):sha(src),str(hair_source):sha(hair_source)}
    art=load_helper('build_mia_face_art_v02.py','mia_reuse_art');art.NEUTRAL_CLOSE=.35
    bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.name='Mia_ExistingFoundation_DetailedHair_Review'
    face=bpy.data.objects['Mia_Face_AnimeTopology'];body=bpy.data.objects['Mia_Body_Anatomy_Skin'];bpy.context.view_layer.update()
    face_before=art.fingerprint(face);body_before=art.fingerprint(body)
    old_hair=[o for o in scene.objects if o.name.startswith('MiaHair_')]
    old_visibility={o.name:o.hide_render for o in old_hair}
    # Preserve the existing complete hair support volume as an independently
    # switchable cap. All original strands remain archived in the same native.
    for ob in old_hair:
        keep=False
        ob.hide_render=ob.hide_viewport=not keep
        if keep:
            mat=bpy.data.materials.new('Mia_DetailedHair_InnerCap_Charcoal');mat.use_nodes=True
            n=mat.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.055,.048,.052,1);o=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],o.inputs['Surface'])
            ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(mat)
    hair_col=bpy.data.collections.new('MIA_HIGH_DETAIL_HAIR_ASSEMBLY');scene.collection.children.link(hair_col)
    capmat=bpy.data.materials.new('Mia_Hair_SeparateScalpCap_Charcoal');capmat.use_nodes=True
    cn=capmat.node_tree.nodes;cn.clear();ce=cn.new('ShaderNodeEmission');ce.inputs['Color'].default_value=(.045,.038,.042,1);co=cn.new('ShaderNodeOutputMaterial');capmat.node_tree.links.new(ce.outputs[0],co.inputs['Surface'])
    caps=[]
    # A separate, skin-fitted scalp cap fills only the concealed head surface;
    # it does not replace/delete the complete skin underneath it.
    for original,label in [(face,'Front'),(body,'Rear')]:
        cap=original.copy();cap.data=original.data.copy();cap.name='MIA_HAIR_SCALP_CAP_'+label;hair_col.objects.link(cap)
        cap.data.materials.clear();cap.data.materials.append(capmat)
        skin_ids={v for poly in original.data.polygons if original==body or poly.material_index==7 for v in poly.vertices}
        for poly in cap.data.polygons:poly.material_index=0
        group=cap.vertex_groups.new(name='SEPARATE_SCALP_CAP_SCOPE');ids=[]
        for v in original.data.vertices:
            q=original.matrix_world@v.co
            if v.index in skin_ids and abs(q.x)<.14 and (q.z>1.620 or (q.y>.015 and q.z>1.475)):ids.append(v.index)
        group.add(ids,1,'REPLACE');mask=cap.modifiers.new('Independent hair cap region; skin master unchanged','MASK');mask.vertex_group=group.name
        cap['role']='replaceable hair scalp cap; duplicated support surface, underlying skin retained'
        caps.append(cap)
    names=['MIA_PIXAL_HAIR_DESIGN_SEPARATE','SINGLE_HAIR_MIXED_REVIEW']
    with bpy.data.libraries.load(str(hair_source),link=False) as (available,loaded):
        names=names if names[0] in available.objects else ['SINGLE_HEAD_MIXED_REVIEW','SINGLE_HAIR_MIXED_REVIEW']
        loaded.objects=[n for n in names if n in available.objects]
    imported=list(loaded.objects)
    if any(o and o.name.startswith('SINGLE_HEAD_MIXED_REVIEW') for o in imported):
        head=next(o for o in imported if o and o.name.startswith('SINGLE_HEAD_MIXED_REVIEW'));hair_col.objects.link(head);bpy.context.view_layer.update()
        extracted=extract_hair_design(head,hair_col);head.hide_render=head.hide_viewport=True;imported=[extracted if o==head else o for o in imported]
    arm=next(m.object for m in face.modifiers if m.type=='ARMATURE' and m.object)
    bone='J_Bip_C_Head' if 'J_Bip_C_Head' in arm.data.bones else None
    fitting=Matrix.Translation((0,.025,1.556))@Matrix.Scale(.88,4)@Matrix.Translation((0,0,-1.516))
    new_hair=[]
    for ob in imported:
        if ob is None:continue
        if ob.name not in hair_col.objects:hair_col.objects.link(ob)
        ob.hide_render=ob.hide_viewport=False;ob.hide_set(False);bpy.context.view_layer.update()
        fitted=fitting@ob.matrix_world.copy()
        if bone:
            ob.parent=arm;ob.parent_type='BONE';ob.parent_bone=bone
        bpy.context.view_layer.update();ob.matrix_world=fitted
        ob['role']='separate high-detail hair design surface fitted onto existing head; no skin or clothing ownership'
        ob['rig_status']='head attachment only; strand deformation/collision not approved'
        new_hair.append(ob)
    if len(new_hair)!=2:raise RuntimeError('Both upper and lower hair design surfaces are required')
    camera=bpy.data.objects['MIA_REVIEW_CAMERA'];scene.camera=camera;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100
    camera.data.type='ORTHO';camera.data.ortho_scale=.48;scene.render.image_settings.file_format='PNG'
    cameras=[]
    def render(name,yaw):
        target=Vector((0,.01,1.580));r=math.radians(yaw);camera.location=target+Vector((.9*math.sin(r),-.9*math.cos(r),.015));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
        cameras.append({'file':name+'.png','yaw':yaw,'matrix_world':[list(v) for v in camera.matrix_world],'ortho_scale':camera.data.ortho_scale})
    art.pose(face)
    bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
    native=out/'Mia_ReusedFoundation_DetailedHair.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native),check_existing=False)
    for name,yaw in [('front',0),('side',90),('quarter_right',35),('quarter_left',-35),('back',180)]:render('assembly_'+name,yaw)
    all_hair=new_hair+caps
    for ob in all_hair:ob.hide_render=True
    for name,yaw in [('front',0),('side',90),('back',180)]:render('skin_only_'+name,yaw)
    for ob in all_hair:ob.hide_render=False
    if a.proofs:
        bones=[arm.pose.bones[n] for n in ('J_Adj_L_FaceEye','J_Adj_R_FaceEye')]
        rest={b.name:(b.matrix_basis.copy(),b.rotation_mode) for b in bones}
        def restore_eyes():
            for b in bones:b.matrix_basis=rest[b.name][0];b.rotation_mode=rest[b.name][1]
        for blink in (0,.5,1):
            for gaze in ('center','left','right','up','down'):
                restore_eyes();art.pose(face)
                next(k for k in face.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close')).value=.35+.65*blink
                if gaze!='center':
                    axis=Vector((0,0,1)) if gaze in ('left','right') else Vector((1,0,0))
                    angle=12 if gaze in ('left','right') else 8
                    if gaze in ('right','down'):angle=-angle
                    for b in bones:
                        b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((b.bone.matrix_local.to_3x3().inverted()@axis).normalized(),math.radians(angle))
                bpy.context.view_layer.update()
                for label,yaw in [('front',0),('quarter',35)]:render('eye_%s_%s_%s'%(blink,gaze,label),yaw)
        restore_eyes()
        for expression in ('mouth_a','annoyed','smile','left_blink','right_blink'):
            art.pose(face,'mouth_a' if expression=='mouth_a' else 'neutral');ks=face.data.shape_keys.key_blocks
            wanted={}
            if expression=='annoyed':wanted={'Fcl_EYE_Angry':.3,'Fcl_MTH_Angry':.35,'Fcl_BRW_Angry':.4}
            if expression=='smile':wanted={'Fcl_MTH_Fun':.6}
            if expression=='left_blink':wanted={'Fcl_EYE_Close_L':.65}
            if expression=='right_blink':wanted={'Fcl_EYE_Close_R':.65}
            for key,value in wanted.items():
                next(k for k in ks if k.name.endswith(key)).value=value
            bpy.context.view_layer.update()
            for label,yaw in [('front',0),('quarter',35)]:render(expression+'_'+label,yaw)
        restore_eyes();art.pose(face)
    face_after=art.fingerprint(face);body_after=art.fingerprint(body)
    assert face_before==face_after,'Assembly changed facial geometry/UV/key coordinates'
    assert body_before==body_after,'Assembly changed body geometry/UV'
    assert before=={path:sha(path) for path in before},'Input native was modified'
    report={'status':'MODULAR_ASSEMBLY_AND_FACE_ART_STUDY; ART_NOTAPPROVED; CHARACTER_INCOMPLETE','base':'02:40 HairSurface_v06 facial/body topology, rig and UV preserved; two explicitly owned face-art correctives were added in the preceding operation','input_hashes_before':before,'input_hashes_after':{path:sha(path) for path in before},'face_fingerprint_before':face_before,'face_fingerprint_after':face_after,'body_fingerprint_before':body_before,'body_fingerprint_after':body_after,'base_face_key_count':len(face.data.shape_keys.key_blocks),'new_hair_objects':[o.name for o in new_hair],'existing_hair_original_visibility':old_visibility,'existing_inner_cap_reused':False,'skin_fitted_independent_caps':[o.name for o in caps],'fitting_matrix':[list(v) for v in fitting],'hair_head_attachment_bone':bone,'cameras':cameras,'proofs_rendered':a.proofs,'limitations':['Art likeness and texture detail require further comparison against approved original art','Hair semantic extraction remains a design partition and needs boundary/strand production review','Hair is head-attached only; strand bones/weights, collision and secondary motion are not complete','Existing body proportions and garments are not reapproved by this facial checkpoint','Original concept image has not been projected as the final skin texture; current UV pigment is a restrained study']}
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    render('assembly_final_front',0);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native),check_existing=False)
    print('REUSED_BASE_ASSEMBLY_SAVED',native)


if __name__=='__main__':main()
