"""Replace430 declared ear-terminal faces with one closed volumetric hair island."""
import bpy,bmesh,json,hashlib,math,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
O=Path(__file__).resolve().parent;S=O.parent/'ink-study/generated-paint/Mia_HairInkPaint_v22.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(S);selection=json.loads((O/'proposed-selection.json').read_text());deleted=selection['delete_faces'];assert len(deleted)==430
bpy.ops.wm.open_mainfile(filepath=str(S));h=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=h.data;assert m.shape_keys is None and not h.animation_data and not m.animation_data and len(h.modifiers)==0
world=[h.matrix_world@v.co for v in m.vertices];sourcefaces=[list(m.polygons[i].vertices) for i in deleted];tree=BVHTree.FromPolygons(world,sourcefaces,all_triangles=True);uvnames=[u.name for u in m.uv_layers];uvdata={u.name:[[u.data[l].uv.copy() for l in m.polygons[i].loop_indices] for i in deleted] for u in m.uv_layers};weights=[{g.group:g.weight for g in v.groups} for v in m.vertices];oldnv=len(m.vertices);oldnf=len(m.polygons)
bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();ov=bm.verts.layers.int.new('MIA_V22_OLD_VERTEX_ID');of=bm.faces.layers.int.new('MIA_V22_OLD_FACE_ID');region=bm.faces.layers.int.new('MIA_V22_TERMINAL_REGION')
for v in bm.verts:v[ov]=v.index
for f in bm.faces:f[of]=f.index;f[region]=0
bmesh.ops.delete(bm,geom=[bm.faces[i] for i in deleted],context='FACES_ONLY')
# Preserve original source topology/coordinates outside430 removed faces. Old loose vertices remain for exact indexing provenance.
oldmat=m.materials[0];newmat=oldmat.copy();newmat.name=oldmat.name+'_EarTerminalGeometryNormals';nodes=newmat.node_tree.nodes;links=newmat.node_tree.links
for node in nodes:
 if node.type in {'BSDF_DIFFUSE','BSDF_ANISOTROPIC','FRESNEL'} and 'Normal' in node.inputs:
  for link in list(node.inputs['Normal'].links):links.remove(link)
newmat_name=str(newmat.name)
newmat['V22_terminal_normal_scope']='Same pigment/light graph; source-derived object normalmap bypassed only on new closed geometry, so it uses actual smooth surface normals.';m.materials.append(newmat);slot=len(m.materials)-1
# Curved broad-to-round terminal; upper closed3mm is buried in retained root, not welded to it.
controls=np.array([[.073,-.003,1.516,.0010,.0020],[.073,-.005,1.513,.0028,.0045],[.074,-.010,1.509,.0043,.0070],[.075,-.016,1.504,.0060,.0100],[.077,-.022,1.498,.0061,.0100],[.078,-.026,1.492,.0048,.0075],[.078,-.028,1.487,.0031,.0048],[.0775,-.029,1.483,.0018,.0028],[.077,-.029,1.481,.0008,.0013]])
# Cubic interpolation of center/radii; endpoint duplicated for stable roots.
def interp(t):
 f=t*(len(controls)-1);i=min(int(f),len(controls)-2);u=f-i;p0=controls[max(0,i-1)];p1=controls[i];p2=controls[i+1];p3=controls[min(len(controls)-1,i+2)];return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)
N=28;R=25;verts=[];samples={};deform=bm.verts.layers.deform.verify();inv=h.matrix_world.inverted();patchfaces=[]
def add_vertex(q):
 v=bm.verts.new(inv@Vector(q));v[ov]=-1;loc,nor,idx,dist=tree.find_nearest(Vector(q));face=sourcefaces[idx];abc=[world[i] for i in face];bary=barycentric_transform(loc,*abc,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));ww={}
 for w,vid in zip(bary,face):
  for group,val in weights[vid].items():ww[group]=ww.get(group,0)+max(0,float(w))*val
 for group,val in ww.items():v[deform][group]=val
 samples[v]=(idx,bary,dist);return v
for ri in range(R):
 t=ri/(R-1);cx,cy,cz,rx,ry=interp(t);ring=[]
 for j in range(N):
  theta=2*math.pi*j/N;shape=1-.07*math.exp(-((math.sin(theta)-.25)/.22)**2)*math.sin(math.pi*t)**2
  q=(cx+rx*math.cos(theta)*shape,cy+ry*math.sin(theta),cz+.00055*math.sin(theta)*math.sin(math.pi*t));ring.append(add_vertex(q))
 verts.append(ring)
def add_face(vs):
 f=bm.faces.new(vs);f[of]=-1;f[region]=1;f.material_index=slot;f.smooth=True
 layer=bm.faces.layers.int.get('MIA_SOURCE_POLYGON')
 if layer:f[layer]=-1
 tie=bm.faces.layers.int.get('MIA_BRAID_TIE')
 if tie:f[tie]=0
 for loop in f.loops:
  idx,bary,dist=samples[loop.vert]
  for name in uvnames:
   triuv=uvdata[name][idx];loop[bm.loops.layers.uv[name]].uv=sum((u*w for u,w in zip(triuv,bary)),Vector((0,0)))
 patchfaces.append(f);return f
for ri in range(R-1):
 for j in range(N):add_face([verts[ri][j],verts[ri+1][j],verts[ri+1][(j+1)%N],verts[ri][(j+1)%N]])
top=add_vertex((.073,-.003,1.5168));bottom=add_vertex((.0768,-.029,1.4802))
for j in range(N):add_face([top,verts[0][j],verts[0][(j+1)%N]]);add_face([bottom,verts[-1][(j+1)%N],verts[-1][j]])
bmesh.ops.recalc_face_normals(bm,faces=patchfaces);patchids=set(v for ring in verts for v in ring)|{top,bottom};badedges=[e for e in bm.edges if all(v in patchids for v in e.verts) and len(e.link_faces)!=2];assert not badedges
assert all(sum(v[deform].values())>0 for v in patchids);bm.to_mesh(m);bm.free();m.update()
D=O/'Mia_EarLockVolume_v22.blend';s=bpy.context.scene;s.camera=bpy.data.objects['MIA_REVIEW_Head_Front'];bpy.ops.wm.save_as_mainfile(filepath=str(D));bpy.ops.wm.open_mainfile(filepath=str(D));s=bpy.context.scene
for view,key in [('Front','front'),('LeftOblique','left_oblique'),('RightOblique','right_oblique'),('Profile','profile'),('Back','back')]:
 s.camera=bpy.data.objects['MIA_REVIEW_Head_'+view];s.render.filepath=str(O/('candidate_'+key+'.png'));bpy.ops.render.render(write_still=True)
for label,path in [('before',S),('after',D)]:
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;clay=bpy.data.materials.new('DIAG_CLAY');clay.use_nodes=True;n=clay.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');d=n.new('ShaderNodeBsdfDiffuse');d.inputs[0].default_value=(.18,.18,.18,1);clay.node_tree.links.new(d.outputs[0],o.inputs[0])
 for ob in bpy.data.collections['MIA_V17_PIXAL_HAIR'].all_objects:
  if ob and ob.type=='MESH':
   for j in range(len(ob.data.materials)):ob.data.materials[j]=clay
 for view in ['Front','Profile','LeftOblique']:
  old=bpy.data.objects['MIA_REVIEW_Head_'+view];cam=old.copy();cam.data=old.data.copy();s.collection.objects.link(cam);cam.location+=Vector((.0803828,-.0187201,1.4967201))-Vector((0,0,1.55));cam.data.ortho_scale=.095;s.camera=cam;s.render.filepath=str(O/(label+'_clay_'+view+'.png'));bpy.ops.render.render(write_still=True)
assert sha(S)==source_sha
(O/'manifest.json').write_text(json.dumps({'source':str(S),'source_sha256':source_sha,'native':str(D),'native_sha256':sha(D),'recipe_sha256':sha(Path(__file__)),'changed_owner':'MIA_V17_PIXAL_DetailedHair','deleted_faces':430,'deleted_source_ids':selection['delete_source_ids'],'old_vertices':oldnv,'old_faces':oldnf,'new_patch_vertices':R*N+2,'new_patch_faces':(R-1)*N+2*N,'new_patch_closed_two_faces_per_edge':True,'old_vertex_coords_changed':0,'new_material_slot':slot,'new_material_name':newmat_name,'material_change':'New patch only: exact existing pigment/light graph, but actual new geometric normals replace obsolete source-derived normalmap. Original slots untouched.','UV':'Both UV layers transferred barycentrically from nearest declared outer-lobe source430faces; no whole atlas edits. Stretch review pending.','weights':'Same source vertex group indices and interpolated donor values; no zero total new weights.','topology_limit':'New terminal island closed, rooted by overlap; retained global main mesh still open, no wholehair watertight claim.','shape_keys':None,'drivers':None,'modifiers':[],'status':'Candidate pending actual visual review and provenance audit'},indent=2));print('VOLUME_DONE',sha(D))
