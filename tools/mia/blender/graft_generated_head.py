"""Cut/align an external generated head module onto a generated body without remeshing UV topology.

This is a mesh-module graft, not a facial proxy generator. Run after GPU generation is idle.
"""
import argparse, bpy, bmesh, os, sys, json, hashlib
from array import array
from mathutils import Vector, Matrix

def cli():
    p=argparse.ArgumentParser()
    p.add_argument('--body',required=True); p.add_argument('--head',required=True); p.add_argument('--out',required=True)
    p.add_argument('--join-z',type=float,default=1.35); p.add_argument('--head-crown',type=float,default=1.68); p.add_argument('--chin-z',type=float,default=1.422)
    p.add_argument('--head-chin-min',type=float,default=.275); p.add_argument('--head-chin-max',type=float,default=.42); p.add_argument('--source-chin-override',type=float,default=.305,help='Reference-calibrated source head lower-jaw Z; set negative to use automatic estimate')
    p.add_argument('--head-scale-min',type=float,default=.75); p.add_argument('--head-scale-max',type=float,default=1.25)
    p.add_argument('--keep-old-body-hair',action='store_true')
    p.add_argument('--label',default='mia-graft-v33'); return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def mwverts(o): return [o.matrix_world@v.co for v in o.data.vertices]
def bounds(o):
 ps=mwverts(o); return Vector(map(min,zip(*ps))),Vector(map(max,zip(*ps)))
PIXELS={}; MAT_ALBEDO={}
def albedo_image(m):
    if m in MAT_ALBEDO:return MAT_ALBEDO[m]
    image=None
    if m and m.use_nodes:
        bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        base=bs.inputs.get('Base Color') if bs else None
        if base and base.links and base.links[0].from_node.type=='TEX_IMAGE': image=base.links[0].from_node.image
        # Projection inserts a Mix node. For topology cuts use the original generated atlas and active
        # original UV layer, never the front-projected artwork (which uses UV_PROJ_FRONT).
        if image is None:
            candidates=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.size[0] and n.image.colorspace_settings.name=='sRGB' and 'originalart' not in n.image.name.lower()]
            if candidates: image=max(candidates,key=lambda i:i.size[0]*i.size[1])
    MAT_ALBEDO[m]=image; return image
def tex_color(obj, poly):
    # Sample only the actual Principled Base Color image (never normal/metallic maps), cached once per image.
    if not obj.data.uv_layers or poly.material_index>=len(obj.data.materials): return None
    m=obj.data.materials[poly.material_index]
    if not m or not m.use_nodes:return None
    img=albedo_image(m)
    if not img:return None
    uv=obj.data.uv_layers.active.data; us=[uv[i].uv for i in poly.loop_indices]; u=sum(x.x for x in us)/len(us)%1; v=sum(x.y for x in us)/len(us)%1
    if img not in PIXELS:
        data=array('f',[0.0])*(img.size[0]*img.size[1]*4); img.pixels.foreach_get(data); PIXELS[img]=data
    x=min(img.size[0]-1,int(u*img.size[0])); y=min(img.size[1]-1,int(v*img.size[1])); i=(y*img.size[0]+x)*4; px=PIXELS[img][i:i+3]
    return tuple(px)
def warm_skin(c): return c and c[0]>.35 and c[0]>c[1]*1.08 and c[1]>c[2]*.92
def neutral_hair(c):
    if not c:return False
    return c[0]>=c[1]*.98 and c[0]>=c[2] and c[1]>=c[2]*.95 and max(c)-min(c)<.12 and .035<sum(c)/3<.55
def delete_faces(obj,predicate):
    bm=bmesh.new(); bm.from_mesh(obj.data); faces=[f for f in bm.faces if predicate(f)]; bmesh.ops.delete(bm,geom=faces,context='FACES_ONLY'); bm.to_mesh(obj.data); bm.free(); obj.data.update(); return len(faces)
def delete_indices(obj, indices):
    bm=bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table(); faces=[bm.faces[i] for i in indices if i<len(bm.faces)]
    bmesh.ops.delete(bm,geom=faces,context='FACES_ONLY'); bm.to_mesh(obj.data); bm.free(); obj.data.update(); return len(faces)
def skin_centers(obj,zlo,zhi,halfwidth=.07):
    points=[]
    for p in obj.data.polygons:
        c=tex_color(obj,p)
        cen=sum((obj.matrix_world@obj.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
        if zlo<=cen.z<=zhi and abs(cen.x)<halfwidth and warm_skin(c): points.append(cen)
    return points
def append_head(path):
    with bpy.data.libraries.load(path,link=False) as (src,dst): dst.objects=[n for n in src.objects if n]
    out=[]
    for o in dst.objects:
        if o and o.type in {'MESH','EMPTY'}: bpy.context.scene.collection.objects.link(o); out.append(o)
    # Linked parent transforms are evaluated only after depsgraph update; never measure raw child data first.
    bpy.context.view_layer.update()
    return [o for o in out if o.type=='MESH']
def main():
 a=cli(); bodypath=os.path.abspath(a.body); headpath=os.path.abspath(a.head); out=os.path.abspath(a.out); os.makedirs(out,exist_ok=True)
 bpy.ops.wm.open_mainfile(filepath=bodypath)
 body=bpy.data.objects.get('Mia_Graft_Body_Editable') or bpy.data.objects.get('Mesh_0')
 if not body or body.type!='MESH': raise RuntimeError('Expected named editable body module or original Mesh_0; refusing largest-mesh inference')
 body.name='Mia_Graft_Body_Editable'
 # Corrected body sources may carry an older graft head for historical QA. Archive it before append:
 # only the named body and this run's appended head may remain visible editable modules.
 for o in bpy.data.objects:
    if o.type=='MESH' and o != body and ('Mia_Graft_Head_Editable' in o.name or o.name.startswith('mia-head')):
        o.name='ARCHIVE_Inherited_Head_'+o.name.replace('Mia_Graft_Head_Editable','')
        o.hide_render=True; o.hide_viewport=True
        if o.parent: o.parent.hide_render=True; o.parent.hide_viewport=True
 archive=body.copy(); archive.data=body.data.copy(); archive.name='ARCHIVE_Original_Body_Unmodified'; bpy.context.scene.collection.objects.link(archive); archive.hide_render=True; archive.hide_viewport=True; archive['source_sha256']=sha(bodypath)
 # Body cut intentionally stops at join Z. It does not attempt uncertain texture-based shirt deletion below Z=1.08.
 old_top=delete_faces(body,lambda f:(sum((body.matrix_world@v.co for v in f.verts),Vector())/len(f.verts)).z>a.join_z and abs((sum((body.matrix_world@v.co for v in f.verts),Vector())/len(f.verts)).x)<.30)
 # Remove only old hair in a bounded shoulder/neck ROI; blue-gray tee and central torso are excluded.
 neckps=[archive.matrix_world@v.co for v in archive.data.vertices if 1.30<v.co.z<1.42 and abs(v.co.x)<.07]
 neck_y=sorted(p.y for p in neckps)[len(neckps)//2] if neckps else 0.0
 old_hair=[]
 for p in body.data.polygons:
    c=tex_color(body,p); cen=sum((body.matrix_world@body.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
    rear=cen.y>neck_y+.025; braid=cen.x>.08 and cen.y<neck_y-.06 and cen.z>1.17
    if 1.08<cen.z<a.join_z and abs(cen.x)<.22 and (rear or braid) and neutral_hair(c): old_hair.append(p.index)
 old_hair_cut=0 if a.keep_old_body_hair else delete_indices(body,old_hair)
 headmeshes=append_head(headpath)
 if not headmeshes: raise RuntimeError('No head meshes appended')
 head=max(headmeshes,key=lambda x:len(x.data.vertices)); head.name='Mia_Graft_Head_Editable'
 # Bake world transforms so the graft is a stable editable module; UV loops/material links remain unchanged.
 for o in headmeshes:
    world=o.matrix_world.copy(); o.parent=None; o.matrix_world=Matrix.Identity(4); o.data.transform(world)
 lo,hi=bounds(head); source_crown=hi.z
 if abs(source_crown-lo.z-.55)>.0002: raise RuntimeError('Expected normalized .55m head source; got height %.6f'%(source_crown-lo.z))
 # Candidate chin faces: centered, lower expected head range, warm skin, downward-facing jaw plane.
 candidates=[]; stats={'head_faces':len(head.data.polygons),'skin_chin_faces':0,'unknown_color_faces':0}
 for p in head.data.polygons:
    c=tex_color(head,p)
    if c is None: stats['unknown_color_faces']+=1
    z=sum(head.data.vertices[i].co.z for i in p.vertices)/len(p.vertices); cx=sum(abs(head.data.vertices[i].co.x) for i in p.vertices)/len(p.vertices)
    if a.head_chin_min<=z<=a.head_chin_max and cx<.10 and p.normal.z<-.20 and warm_skin(c): candidates.append(z)
 stats['skin_chin_faces']=len(candidates)
 fallback=False
 if a.source_chin_override>=0:
    source_chin=a.source_chin_override; fallback=False; chin_method='reference_calibrated_override'
 elif candidates:
    source_chin=sorted(candidates)[max(0,int(len(candidates)*.10)-1)]; chin_method='lower_decile_skin_jaw'
 else:
    source_chin=a.head_chin_min; fallback=True; chin_method='unsafe_fallback'
 if source_crown<=source_chin: raise RuntimeError('Invalid head crown/chin measurement')
 scale=(a.head_crown-a.chin_z)/(source_crown-source_chin)
 if not a.head_scale_min<=scale<=a.head_scale_max: raise RuntimeError('Head scale %.5f outside asserted safe range %.3f..%.3f'%(scale,a.head_scale_min,a.head_scale_max))
 for o in headmeshes:
    o.data.transform(Matrix.Scale(scale,4)); o.location.z+=a.head_crown-source_crown*scale
 bpy.context.view_layer.update()
 _, head_pre_hi=bounds(head)
 if abs(head_pre_hi.z-a.head_crown)>.0001: raise RuntimeError('Head world crown stale/misaligned: %.6f expected %.6f'%(head_pre_hi.z,a.head_crown))
 # Match central skin neck medians, if both sources supply reliable warm-skin points.
 bodyneck=skin_centers(archive,1.30,1.41,.08)
 headneck=skin_centers(head,a.join_z-.05,a.join_z+.06,.08)
 neck_fallback=not bodyneck or not headneck
 if not neck_fallback:
    def med(ps,i): return sorted(p[i] for p in ps)[len(ps)//2]
    dx,dy=med(bodyneck,0)-med(headneck,0),med(bodyneck,1)-med(headneck,1)
    for o in headmeshes:o.location.x+=dx; o.location.y+=dy
 bpy.context.view_layer.update()
 head_pre_lo,head_pre_hi=bounds(head)
 if abs(head_pre_hi.z-a.head_crown)>.0001 or head_pre_hi.z<1.0: raise RuntimeError('Head world bounds invalid before cut: '+str(tuple(head_pre_hi)))
 # New head: retain warm neck margin and neutral gray hair; remove only colored/dark lower garment faces.
 # Classification is deliberately spatially bounded below the overlap margin, so central body clothing is never touched.
 cut_new=[]
 for p in head.data.polygons:
    cen=sum((head.matrix_world@head.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices); z=cen.z; c=tex_color(head,p)
    # Preserve a narrow actual generated skin sleeve through the collar zone; it overlaps the body neck,
    # avoids black seam holes, and is not a fabricated primitive.
    keep_neck=warm_skin(c) and z>=a.join_z-.005 and abs(cen.x)<.055
    # Below the jaw, never use color to preserve front hair: brown strap/pin geometry is indistinguishable
    # from hair albedo. Keep only rear volume or the deliberate left-braid spatial corridor.
    keep_hair=neutral_hair(c) and (cen.y>neck_y+.015 or (cen.x>.08 and z>1.28))
    # The selected single-head source also carries an unwanted cyan/gold pin on anatomical right
    # front chest (negative X). This explicit ROI is apparel-only; warm neck skin is excluded.
    source_pin_roi=(-.17<=cen.x<=-.04 and 1.40<=z<=1.54 and cen.y<neck_y-.015 and not warm_skin(c))
    if source_pin_roi or (z<a.join_z and not keep_neck and not keep_hair): cut_new.append(p.index)
 dropped_new=delete_indices(head,cut_new)
 bpy.context.view_layer.update(); head_post_lo,head_post_hi=bounds(head)
 body['graft_join_z']=a.join_z; head['graft_head_crown']=a.head_crown; head['graft_chin_z']=a.chin_z; head['graft_scale']=scale; head['graft_chin_fallback']=fallback; head['source_sha256']=sha(headpath)
 for o in headmeshes:
    for m in o.data.materials:
        if m: m.use_fake_user=True
 bpy.context.scene['Mia_status']='unrigged generated mesh graft; fidelity, seam and topology unapproved'; bpy.context.scene['graft_method']='UV-preserving face cut + independently editable imported head module'; bpy.context.scene['source_body_sha256']=sha(bodypath); bpy.context.scene['source_head_sha256']=sha(headpath)
 report={'body':bodypath,'head':headpath,'body_sha256':sha(bodypath),'head_sha256':sha(headpath),'join_z':a.join_z,'target_crown':a.head_crown,'target_chin':a.chin_z,'source_crown':source_crown,'estimated_source_chin':source_chin,'chin_method':chin_method,'scale':scale,'chin_fallback':fallback,'neck_alignment_fallback':neck_fallback,'skin_neck_centroids':{'body':len(bodyneck),'head':len(headneck)},'head_bounds_before_cut':[list(head_pre_lo),list(head_pre_hi)],'head_bounds_after_cut':[list(head_post_lo),list(head_post_hi)],'body_faces_cut':old_top,'old_body_hair_faces_cut':old_hair_cut,'new_head_faces_cut':dropped_new,'region_stats':stats,'manual_qc_required':['neck seam','head/body overlap','texture-classification boundary'],'status':bpy.context.scene['Mia_status']}
 with open(os.path.join(out,a.label+'-graft-report.json'),'w',encoding='utf8') as f:json.dump(report,f,indent=2)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,a.label+'-native.blend'))
if __name__=='__main__':main()
