"""Render the v06 neutral validation matrix from an already-built native blend."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse():
    p=argparse.ArgumentParser()
    p.add_argument("--input", required=True); p.add_argument("--output-dir", required=True)
    p.add_argument("--crops", default="full,torso,head")
    p.add_argument("--views", default="front,profile_l,back,three_quarter_l,three_quarter_r")
    p.add_argument("--modes", default="actual,clay,wire")
    return p.parse_args(sys.argv[sys.argv.index("--")+1:])


def digest(path):
    hasher=hashlib.sha256()
    with open(path,"rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):
            hasher.update(block)
    return hasher.hexdigest()


def mat(name, color):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=m.node_tree.nodes; n.clear(); out=n.new("ShaderNodeOutputMaterial"); bs=n.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value=color; bs.inputs["Roughness"].default_value=.86
    m.node_tree.links.new(bs.outputs["BSDF"],out.inputs["Surface"]); return m


def aim(cam, loc, target):
    cam.location=loc; cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()


def camera(scene):
    data=bpy.data.cameras.new("MIA_V06_MATRIX_CAMERA"); data.type="ORTHO"
    obj=bpy.data.objects.new(data.name,data); scene.collection.objects.link(obj); scene.camera=obj; return obj


def lighting(scene):
    if any(o.name.startswith("MIA_V06_MATRIX_") and o.type=="LIGHT" for o in scene.objects): return
    for i,(loc,energy) in enumerate((((2.4,-3.0,3.0),240),((-2.2,-1.8,2.2),110),((0,2.5,2.7),150))):
        d=bpy.data.lights.new("MIA_V06_MATRIX_%d"%i,"AREA"); d.energy=energy; d.shape="DISK"; d.size=2
        o=bpy.data.objects.new(d.name,d); scene.collection.objects.link(o); o.location=loc; aim(o,loc,(0,0,1))


def face_skin_copy(face):
    copy=face.copy(); copy.data=face.data.copy(); copy.name="MIA_V06_MATRIX_FACE_WIRE_SKIN"
    bpy.context.scene.collection.objects.link(copy); copy.hide_render=False; copy.hide_viewport=False
    keep={0,7}
    bpy.context.view_layer.objects.active=copy; copy.select_set(True); bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    for p in copy.data.polygons: p.select=p.material_index not in keep
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT"); copy.select_set(False)
    return copy


def wire_copies(body, face):
    result=[]
    for src in (body,face_skin_copy(face)):
        obj=src.copy(); obj.data=src.data.copy(); obj.name="MIA_V06_MATRIX_WIRE_"+src.name
        bpy.context.scene.collection.objects.link(obj); obj.hide_render=False; obj.hide_viewport=False; obj.data.materials.clear(); obj.data.materials.append(mat(obj.name,(.05,.08,.13,1)))
        mod=obj.modifiers.new("MIA_V06_MATRIX_WIREFRAME","WIREFRAME"); mod.thickness=.0012
        result.append(obj)
        if src.name.startswith("MIA_V06_MATRIX_FACE_WIRE_SKIN"): bpy.data.objects.remove(src,do_unlink=True)
    return result


def main():
    a=parse(); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); bpy.ops.wm.open_mainfile(filepath=a.input)
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=900; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"
    body=bpy.data.objects["MIA_V06_BODY_SKIN"]; face=bpy.data.objects["MIA_V06_FACE_SKIN"]
    # Geometry gate is derived anatomy only.  Archive, reference, hair and
    # display shells are hidden in every validation mode.
    for obj in scene.objects:
        if obj.type=="MESH" and obj not in (body,face): obj.hide_render=True
        if obj.type=="LIGHT": obj.hide_render=True
    cam=camera(scene); lighting(scene); clay=mat("MIA_V06_MATRIX_CLAY",(.18,.21,.25,1))
    views={"front":((0,-4,0), (0,0,0)), "profile_l":((4,0,0),(0,0,0)), "back":((0,4,0),(0,0,0)),
           "three_quarter_l":((2.83,-2.83,0),(0,0,0)), "three_quarter_r":((-2.83,-2.83,0),(0,0,0))}
    crops={"full":((0,0,.93),1.90),"torso":((0,0,1.11),.80),"head":((0,0,1.58),.44)}
    report={"input_native":str(Path(a.input).resolve()),"input_native_sha256":digest(Path(a.input).resolve()),
            "script":str(Path(__file__).resolve()),"script_sha256":digest(Path(__file__).resolve()),
            "views":{},"mode_visible_owners":{},"note":"Reference panels remain illustrative; this is a consistent review matrix, not orthographic registration. All anatomy gates exclude archive, hair, references and display proxy."}
    selected_crops=[item for item in a.crops.split(",") if item in crops]
    selected_views=[item for item in a.views.split(",") if item in views]
    selected_modes=[item for item in a.modes.split(",") if item in ("actual","clay","wire")]
    report["selection"]={"crops":selected_crops,"views":selected_views,"modes":selected_modes}
    for crop in selected_crops:
        target,scale=crops[crop]
        for view in selected_views:
            offset,_=views[view]
            pos=Vector(target)+Vector(offset); aim(cam,pos,target); cam.data.ortho_scale=scale
            key="%s_%s"%(crop,view); report["views"][key]={"target":list(target),"camera":list(pos),"ortho_scale":scale}
            for mode in selected_modes:
                original_override=bpy.context.view_layer.material_override; copies=[]; old=(body.hide_render,face.hide_render)
                body.hide_render=False; face.hide_render=False
                if mode=="clay":
                    # Transparent eye/liner cards would become fake opaque
                    # goggles under override; render body + face skin islands.
                    face.hide_render=True; skin=face_skin_copy(face); copies.append(skin)
                    bpy.context.view_layer.material_override=clay
                if mode=="wire":
                    body.hide_render=True; face.hide_render=True; copies=wire_copies(body,face)
                visible=[{"name":o.name,"polygons":len(o.data.polygons)} for o in scene.objects if o.type=="MESH" and not o.hide_render]
                report["mode_visible_owners"].setdefault(mode,visible)
                scene.render.filepath=str(out/(key+"_"+mode+".png")); bpy.ops.render.render(write_still=True)
                bpy.context.view_layer.material_override=original_override; body.hide_render,face.hide_render=old
                for obj in copies: bpy.data.objects.remove(obj,do_unlink=True)
    (out/"matrix-camera-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")


if __name__=="__main__": main()
