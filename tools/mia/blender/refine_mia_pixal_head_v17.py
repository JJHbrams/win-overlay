"""Reference-directed Pixal hair recovery and editable static regional ownership."""
import bpy,bmesh,sys,argparse,json,hashlib,math,struct
from mathutils.bvhtree import BVHTree
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(exist_ok=True,parents=True)
STAGE=ROOT/'asset/mia/blender/mia-production-stage1/v11/Mia_Stage1_DesignReview.blend';AUTH=Path(r'D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(f):sha(f) for f in [SOURCE,STAGE,AUTH,Path(r'D:/ai/Mia3DWork/output/mia_pixal_head512_tex2048_00001.glb')]}
bpy.ops.wm.open_mainfile(filepath=str(STAGE));src=next(o for o in bpy.data.collections['SOURCE_SINGLE_RAW'].objects if o.type=='MESH');src.hide_viewport=False;src.hide_set(False);bpy.context.view_layer.update()
img=next(n.image for n in src.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image);w,hh=img.size;pixels=np.array(img.pixels[:],np.float32).reshape(hh,w,4);uv=src.data.uv_layers.active;world=[src.matrix_world@v.co for v in src.data.vertices]
selected=[];positions={};verts_to_poly={};centers={};tie_ids=set()
for poly in src.data.polygons:
 t=sum((uv.data[i].uv for i in poly.loop_indices),Vector((0,0)))/poly.loop_total;c=pixels[min(hh-1,max(0,int(t.y*hh))),min(w-1,max(0,int(t.x*w))),:3];q=src.matrix_world@poly.center;x,y,z=q
 gray=c.mean()<.49 and c.max()-c.min()<.16 and c[0]>=c[1]-.008 and c[0]>=c[2]-.008
 region=z>1.38 or (z>1.13 and (y>.06 or abs(x)>.125 or (.075<x<.19 and y>-.15)))
 tie=(math.hypot(.64944*x-.10,.64944*z+.55636158-1.36)<.013 and y<-.03 and c[1]>c[0]*1.15 and c[2]>c[0]*1.15)
 strap_x=.15-.97*(z-.95)
 strap=(.94<z<1.35 and y<.025 and abs(x-strap_x)<.032) or (z<1.38 and c[0]-c[2]>.060 and c[0]-c[1]>.025)
 if not (gray or tie or z>1.61) or not region or strap:continue
 if tie:tie_ids.add(poly.index)
 selected.append(poly.index);centers[poly.index]=q
 for i in poly.vertices:
  key=tuple(round(t,5) for t in world[i]);verts_to_poly.setdefault(key,[]).append(poly.index)
# Keep continuous hair-connected components. Isolated dark eyelash/eye paint is not hair.
adj={i:set() for i in selected}
for ids in verts_to_poly.values():
 if len(ids)>1:
  for i in ids:adj[i].update(ids)
remaining=set(selected);keep=[];components=[]
while remaining:
 first=remaining.pop();stack=[first];comp=[first]
 while stack:
  i=stack.pop()
  for j in adj[i]:
   if j in remaining:remaining.remove(j);stack.append(j);comp.append(j)
 pts=[centers[i] for i in comp];seed=any(q.z>1.56 for q in pts) or any(q.y>.065 and q.z>1.36 for q in pts) or (len(comp)>70 and any(q.x>.075 and q.z<1.39 for q in pts))
 if seed and len(comp)>8:keep+=comp
 components.append({'faces':len(comp),'kept':seed and len(comp)>8})
# Fill only small rejected components enclosed in the retained upper hair.
# This restores light textured strand highlights; the large face/skin component stays excluded.
kept=set(keep);vmap={};pkeys={}
for poly in src.data.polygons:
 if (src.matrix_world@poly.center).z<1.45:continue
 kk=[tuple(round(t,5) for t in world[i]) for i in poly.vertices];pkeys[poly.index]=kk
 for k in kk:vmap.setdefault(k,[]).append(poly.index)
rej=set(pkeys)-kept;recovered=[]
while rej:
 first=rej.pop();stack=[first];comp=[first];border=set()
 while stack:
  i=stack.pop()
  for k in pkeys[i]:
   for j in vmap[k]:
    if j in kept:border.add(j)
    elif j in rej:rej.remove(j);stack.append(j);comp.append(j)
 if len(comp)<140 and len(border)>3:recovered+=comp
keep+=recovered
keep.sort();used=sorted({v for i in keep for v in src.data.polygons[i].vertices});mapping={v:j for j,v in enumerate(used)}
me=bpy.data.meshes.new('MIA_V17_PixalRecoveredUV');me.from_pydata([world[i] for i in used],[],[[mapping[v] for v in src.data.polygons[i].vertices] for i in keep]);newuv=me.uv_layers.new(name=uv.name)
for ni,oi in enumerate(keep):
 for aa,bb in zip(me.polygons[ni].loop_indices,src.data.polygons[oi].loop_indices):newuv.data[aa].uv=uv.data[bb].uv
for mat in src.data.materials:me.materials.append(mat)
srcattr=me.attributes.new('MIA_SOURCE_POLYGON','INT','FACE');tieattr=me.attributes.new('MIA_BRAID_TIE','INT','FACE')
for po,oi in zip(me.polygons,keep):
 po.use_smooth=True;po.material_index=1 if oi in tie_ids else 0;srcattr.data[po.index].value=oi;tieattr.data[po.index].value=int(oi in tie_ids)
# Quantiles in both stored byte-like RGB and shader-decoded scene-linear luminance.
uvs=np.array([tuple(newuv.data[p.loop_start].uv) for p in me.polygons]);cols=pixels[np.clip((uvs[:,1]*hh).astype(int),0,hh-1),np.clip((uvs[:,0]*w).astype(int),0,w-1),:3];lin=np.where(cols<=.04045,cols/12.92,((cols+.055)/1.055)**2.4);lum=lin@np.array([.2126,.7152,.0722]);quantiles={'percentiles':[0,5,25,50,75,95,100],'encoded_mean':np.percentile(cols.mean(1),[0,5,25,50,75,95,100]).tolist(),'shader_linear_luminance':np.percentile(lum,[0,5,25,50,75,95,100]).tolist()}
hair=bpy.data.objects.new('MIA_V17_PIXAL_DetailedHair',me);bpy.context.scene.collection.objects.link(hair);hair['source_vertices']=used;hair['source_polygons']=keep;hair['source_raw_sha256']=hashes[str(Path(r'D:/ai/Mia3DWork/output/mia_pixal_head512_tex2048_00001.glb'))]
# Raw proxy eye spacing was ~10% wider than current face. Uniform fit preserves hair aspect.
v07=Matrix.Translation((0,.025,1.556))@Matrix.Scale(.88,4)@Matrix.Translation((0,0,-1.516))
for v in me.vertices:
 q=v07@v.co;q=Vector(((q.x+.0004777)*.82-.000394,(q.y+.0861166)*.82-.07108,1.559+(q.z-1.565739)*.82));v.co=Vector((q.x*.90,(q.y+.07)*.90-.07,1.540+(q.z-1.550)*.90))
regions={n:hair.vertex_groups.new(name=n) for n in ['Crown','Fringe','Side_Nape','Rear_Waves','Left_Braid','Loose_Tips','Roots_Locked']}
for v in me.vertices:
 x,y,z=v.co
 name='Crown' if z>1.60 else 'Fringe' if y<-.055 and z>1.49 else 'Left_Braid' if x>.05 and y<-.005 and z<1.50 else 'Rear_Waves' if y>.045 and z<1.53 else 'Side_Nape'
 regions[name].add([v.index],1,'REPLACE')
 if z>1.63:regions['Roots_Locked'].add([v.index],1,'REPLACE')
 if z<1.41:regions['Loose_Tips'].add([v.index],min(1,(1.41-z)/.08),'REPLACE')
lib=OUT/'Recovered_Pixal_Hair_Source.blend';bpy.data.libraries.write(str(lib),{hair},path_remap='ABSOLUTE',fake_user=True,compress=True)
# Reuse the earlier independent closed knot and strand wraps, not its complete hairstyle.
bpy.ops.wm.open_mainfile(filepath=str(AUTH));bpy.context.view_layer.update();knot=[]
for src in list(bpy.data.objects):
 if not ((src.name=='MiaHair_HalfUp_OneClosedKnot' or src.name.startswith('MiaHair_Knot_Wrap')) and not any(t in src.name for t in ['Edge','Etch'])):continue
 src.hide_viewport=False;src.hide_set(False);bpy.context.view_layer.update();ev=src.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());me.transform(ev.matrix_world);o=bpy.data.objects.new('MIA_V17_'+src.name,me);bpy.context.scene.collection.objects.link(o);knot.append(o)
pts=[v.co for o in knot for v in o.data.vertices];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);center=(lo+hi)/2;scale=.070/(hi.x-lo.x)
for o in knot:
 for v in o.data.vertices:v.co=(v.co-center)*scale+Vector((0,.135,1.568))
 o['ownership']='HalfUp_Knot';o['source_sha256']=hashes[str(AUTH)]
# Reuse the original 150x10 three-lane interweave; flatten and taper individual lobes.
lanes=[bpy.data.objects['MiaHair_LEFT_OneBraid_Lane'+str(i)] for i in range(3)];raw=[np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]).reshape(150,10,3) for o in lanes];axis=np.mean(np.stack(raw),axis=(0,2));braid=[]
for lane,src in enumerate(lanes):
 m=src.data.copy();o=bpy.data.objects.new('MIA_V17_LeftBraid_Lane'+str(lane),m);bpy.context.scene.collection.objects.link(o)
 for i,v in enumerate(m.vertices):
  row=i//10;t=row/149;d=Vector(raw[lane][row,i%10]-axis[row]);u=min(1,t/.75);u=u*u*(3-2*u);center=Vector((.075+.04*t+.004*math.sin(t*math.pi),float(np.interp(t,[0,.35,.75,1],[.005,-.015,-.052,-.044])),1.535-.225*t));d.x*=.92*(1+.12*math.sin(t*math.pi*5));d.y*=.60;d.z*=.78;v.co=center+d
 if m.uv_layers:uv1=m.uv_layers.active
 else:uv1=m.uv_layers.new(name='MIA_V17_Braid_Longitudinal')
 for po in m.polygons:
  for li in po.loop_indices:
   vi=m.loops[li].vertex_index;uv1.data[li].uv=((vi%10)/10,(vi//10)/149)
  us=[uv1.data[li].uv.x for li in po.loop_indices]
  if max(us)-min(us)>.5:
   for li in po.loop_indices:
    if uv1.data[li].uv.x<.5:uv1.data[li].uv.x+=1
 o['ownership']='Left_Braid';o['source_sha256']=hashes[str(AUTH)];vg=o.vertex_groups.new(name='Left_Braid');vg.add(list(range(len(m.vertices))),1,'REPLACE');braid.append(o)
src=bpy.data.objects['MiaHair_Braid_Tail'];m=src.data.copy();o=bpy.data.objects.new('MIA_V17_LeftBraid_Tail',m);bpy.context.scene.collection.objects.link(o);pts=[src.matrix_world@v.co for v in m.vertices];zlo=min(q.z for q in pts);zhi=max(q.z for q in pts)
for v,q in zip(m.vertices,pts):
 t=(zhi-q.z)/(zhi-zlo);v.co=Vector((.115+.012*t+(q.x-(.145+.008*t))*.8,-.044-.003*t+(q.y-sum(a.y for a in pts)/len(pts))*.55,1.314-.045*t))
uv1=m.uv_layers.active or m.uv_layers.new(name='MIA_V17_Tail_UV')
for po in m.polygons:
 for li in po.loop_indices:
  q=m.vertices[m.loops[li].vertex_index].co;t=(1.314-q.z)/.045;uv1.data[li].uv=((q.x-(.115+.012*t))/.022+.5,t)
o['ownership']='Loose_Tips';vg=o.vertex_groups.new(name='Loose_Tips');vg.add(list(range(len(m.vertices))),1,'REPLACE');braid.append(o)
braidlib=OUT/'Reused_Braid_Source.blend';bpy.data.libraries.write(str(braidlib),set(braid),path_remap='ABSOLUTE',fake_user=True,compress=True)
klib=OUT/'Reused_HalfUp_Knot_Source.blend';bpy.data.libraries.write(str(klib),set(knot),path_remap='ABSOLUTE',fake_user=True,compress=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;cam=scene.camera
for o in bpy.data.collections['MIA_V16_PIXAL_HAIR_GUIDE'].objects:o.hide_render=True;o.hide_viewport=True
col=bpy.data.collections.new('MIA_V17_PIXAL_HAIR');scene.collection.children.link(col);owned=[]
for f in [lib,klib,braidlib]:
 with bpy.data.libraries.load(str(f),link=False) as (av,ld):ld.objects=av.objects
 for o in ld.objects:col.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False);owned.append(o)
hair=next(o for o in owned if o.name.startswith('MIA_V17_PIXAL_DetailedHair'))
# Preserve the real braid volume and move it in front of the torso coherently.
for v in hair.data.vertices:
 x,y,z=v.co;front=max(0,min(1,(.02-y)/.04));below=max(0,min(1,(1.515-z)/.055));side=math.exp(-((x-.10)/.043)**4)
 v.co.y-=.025*front*below*side
# Remove manually localized side garment sheets, not braid contact faces.

body=bpy.data.objects['MIA_V06_BODY_SKIN'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bm0=ev.to_mesh();bv=BVHTree.FromPolygons([ev.matrix_world@v.co for v in bm0.vertices],[list(p.vertices) for p in bm0.polygons]);ev.to_mesh_clear()
# Coherent ring-center fit to evaluated world-space body, preserving the weave.
lanes=[bpy.data.objects['MIA_V17_LeftBraid_Lane'+str(i)] for i in range(3)]
centers=[];desired=[]
for row in range(150):
 pts0=[o.data.vertices[row*10+j].co.copy() for o in lanes for j in range(10)];c=sum(pts0,Vector())/30;rad=max(abs(p.y-c.y) for p in pts0);hit=bv.ray_cast(Vector((c.x,-.6,c.z)),Vector((0,1,0)))[0];centers.append(c)
 desired.append(hit.y-rad-.003 if hit is not None and c.z<1.40 else c.y)
filtered=np.convolve(np.pad(np.array(desired),(4,4),mode='edge'),np.ones(9)/9,mode='valid')
for row,c in enumerate(centers):
 for o in lanes:
  for j in range(10):o.data.vertices[row*10+j].co.y+=float(filtered[row])-c.y
braid_end_y=float(filtered[-1])
for v in bpy.data.objects['MIA_V17_LeftBraid_Tail'].data.vertices:v.co.y+=braid_end_y-(-.044)
bm=bmesh.new();bm.from_mesh(hair.data);bad=[]
for po in bm.faces:
 q=po.calc_center_median()
 if (q.z<1.48 and q.y<.065 and abs(q.x)<.18) or (q.z<1.42 and q.y<.09 and abs(q.x)<.12):bad.append(po);continue
 if 1.30<q.z<1.37 and .065<q.y<.12 and abs(q.x)<.12:bad.append(po);continue
 if q.z>1.445:continue
 hit,normal,idx,dist=bv.find_nearest(q)
 if 1.25<q.z<1.448-.12*abs(q.x) and abs(q.x)<.18 and -.025<q.y<.060:bad.append(po)
bmesh.ops.delete(bm,geom=bad,context='FACES')
# Remove small disconnected extraction remnants below the head; preserve connected Pixal mass.
buckets={}
for po in bm.faces:
 for v in po.verts:buckets.setdefault(tuple(round(a,5) for a in v.co),set()).add(po)
remaining=set(bm.faces);fragments=[]
while remaining:
 first=remaining.pop();component={first};stack=[first]
 while stack:
  po=stack.pop()
  for v in po.verts:
   for other in buckets[tuple(round(a,5) for a in v.co)]:
    if other in remaining:remaining.remove(other);component.add(other);stack.append(other)
 if len(component)<600 and max(v.co.z for po in component for v in po.verts)<1.54:fragments.extend(component)
bmesh.ops.delete(bm,geom=fragments,context='FACES')
for _ in range(2):
 moves={v:sum((e.other_vert(v).co for e in v.link_edges),Vector())/len(v.link_edges) for v in bm.verts if v.is_boundary and v.co.z<1.45 and len(v.link_edges)>1}
 for v,q in moves.items():v.co=v.co.lerp(q,.3)
bm.to_mesh(hair.data);bm.free();hair.data.update()
# Round the inherited knot silhouette coherently and give its reused geometry local UVs.
for o in owned:
 if o==hair or 'LeftBraid' in o.name:continue
 for v in o.data.vertices:
  q=v.co-Vector((0,.135,1.568));xx=q.x/.035;zz=q.z/.028;rad=math.hypot(xx,zz);factor=(max(abs(xx),abs(zz))/rad if rad>1e-6 else 1);q.x*=.5+.5*factor;q.z*=.5+.5*factor;v.co=q*(.72 if 'OneClosedKnot' in o.name else 1)+Vector((0,.135,1.568))
 if not o.data.uv_layers:
  uv0=o.data.uv_layers.new(name='MIA_V17_Knot_Cylindrical')
  for po in o.data.polygons:
   for li in po.loop_indices:
    q=o.data.vertices[o.data.loops[li].vertex_index].co-Vector((0,.135,1.568));uv0.data[li].uv=((math.atan2(q.z,q.x)+math.pi)/math.tau,(q.y+.04)/.08)
for ob in owned:
 if ob==hair or 'LeftBraid' in ob.name or not ob.data.uv_layers:continue
 layer=ob.data.uv_layers.active
 for po in ob.data.polygons:
  us=[layer.data[i].uv.x for i in po.loop_indices]
  if max(us)-min(us)>.5:
   for i in po.loop_indices:
    if layer.data[i].uv.x<.5:layer.data[i].uv.x+=1
atlas=next(n.image for n in hair.material_slots[0].material.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
# Owned ash-gray response preserves UV texture strata and geometry normals.
mat=bpy.data.materials.new('MIA_V17_Pixal_AshGray_Detail');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links;out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=atlas;tex.name='ORIGINAL_PIXAL_ATLAS';bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],bw.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.001;r.color_ramp.elements[0].color=(.065,.063,.067,1);r.color_ramp.elements[1].position=.11;r.color_ramp.elements[1].color=(.32,.31,.325,1);l.new(bw.outputs[0],r.inputs[0]);power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=.5;l.new(bw.outputs[0],power.inputs[0]);gain=n.new('ShaderNodeMath');gain.operation='MULTIPLY';gain.inputs[1].default_value=.50;l.new(power.outputs[0],gain.inputs[0]);geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.3,-.65,.7);l.new(geo.outputs['Normal'],dot.inputs[0]);mr=n.new('ShaderNodeMapRange');mr.inputs['From Min'].default_value=-1;mr.inputs['From Max'].default_value=1;mr.inputs['To Min'].default_value=.62;mr.inputs['To Max'].default_value=1.;l.new(dot.outputs['Value'],mr.inputs['Value']);mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(gain.outputs[0],mul.inputs[1]);l.new(mr.outputs[0],mul.inputs[2]);l.new(mul.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0]);hair.data.materials.clear();hair.data.materials.append(mat)
tie_mat=h._flat_paper_material('MIA_V17_RecoveredBraidTie',(.04,.23,.23,1));hair.data.materials.append(tie_mat)
for po in hair.data.polygons:po.material_index=hair.data.attributes['MIA_BRAID_TIE'].data[po.index].value
kmat=mat.copy();kmat.name='MIA_V17_KnotAsh_StrandNormals';kn=kmat.node_tree.nodes;kl=kmat.node_tree.links;km=next(n for n in kn if n.type=='MIX_RGB');
for lk in list(km.inputs[1].links):kl.remove(lk)
km.inputs[1].default_value=(.20,.19,.205,1)
uvn=kn.new('ShaderNodeTexCoord');wave=kn.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=18;wave.inputs['Distortion'].default_value=.5;kl.new(uvn.outputs['UV'],wave.inputs['Vector']);kr=kn.new('ShaderNodeValToRGB');kr.name='OWNED_STRAND_RAMP';kr.color_ramp.elements[0].color=(.073,.071,.075,1);kr.color_ramp.elements[1].color=(.087,.084,.09,1);kl.new(wave.outputs['Color'],kr.inputs[0]);kl.new(kr.outputs[0],km.inputs[1])
for o in owned:
 if o!=hair:
  o.data.materials.clear();o.data.materials.append(kmat)
  for po in o.data.polygons:po.material_index=0;po.use_smooth=True
# Separate longitudinal strand response on the reused braid, not a uniform rope material.
bmat=kmat.copy();bmat.name='MIA_V17_BraidAsh_Strata';bn=bmat.node_tree.nodes;bl=bmat.node_tree.links;bwav=next(n for n in bn if n.type=='TEX_WAVE');bwav.bands_direction='X';bwav.inputs['Scale'].default_value=18;bwav.inputs['Distortion'].default_value=.5;br=bn['OWNED_STRAND_RAMP'];br.color_ramp.elements[0].color=(.06,.058,.062,1);br.color_ramp.elements[1].color=(.115,.111,.118,1)
for o in owned:
 if 'LeftBraid' in o.name:
  o.data.materials.clear();o.data.materials.append(bmat)
  for po in o.data.polygons:po.material_index=0;po.use_smooth=True
# An explicit owned tie at the braid/tail join, with its native torus UVs.
bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=12,location=(.115,braid_end_y,1.310),major_radius=.0105,minor_radius=.0022);tie=bpy.context.object;tie.name='MIA_V17_LeftBraid_Tie';tie.scale.y=.65
for c in list(tie.users_collection):c.objects.unlink(tie)
col.objects.link(tie);tie.data.materials.append(h._flat_paper_material('MIA_V17_MutedTealTie',(.035,.14,.14,1)));tie['ownership']='Left_Braid';owned.append(tie)
scene.render.resolution_x=scene.render.resolution_y=1000;cam.data.ortho_scale=.48
def paired(prefix):
 for mode in ['hair','bald']:
  for o in owned:o.hide_render=mode=='bald'
  for name,loc in [('front',(0,-2,1.54)),('profile',(2,0,1.54))]:
   h._aim(cam,loc,(0,0,1.54));scene.render.filepath=str(OUT/(prefix+'_'+mode+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
 for o in owned:o.hide_render=False
paired('crownA')
# Bounded above-brow lift, identical spatial mapping for all current key coordinates.
def warp_above_brow(ob,lift=.008):
 mw=ob.matrix_world;inv=mw.inverted()
 arrays=[ob.data.vertices] if not ob.data.shape_keys else [k.data for k in ob.data.shape_keys.key_blocks]
 changed=0
 for arr in arrays:
  for v in arr:
   q=mw@v.co;t=max(0,min(1,(q.z-1.56)/.075));delta=lift*t*t*(3-2*t)
   if delta>0:q.z+=delta;v.co=inv@q;changed+=1
 ob.data.update();return changed
warp_counts={}
for name in ['MIA_V06_BODY_SKIN','MIA_V14_SculptedSkin']:warp_counts[name]=warp_above_brow(bpy.data.objects[name])
bpy.context.view_layer.update();paired('crownB')
# Resolve measured crown contact locally; retain all skin and the outer hairstyle envelope.
vv=[];ff=[]
for ob in [bpy.data.objects['MIA_V06_BODY_SKIN'],bpy.data.objects['MIA_V14_SculptedSkin']]:
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();off=len(vv);pts=[ev.matrix_world@v.co for v in mm.vertices];vv+=pts;ff.extend([off+i for i in po.vertices] for po in mm.polygons if all(pts[i].z>1.555 for i in po.vertices));ev.to_mesh_clear()
contact=BVHTree.FromPolygons(vv,ff);contact_shifts=[]
for v in hair.data.vertices:
 if v.co.z<1.56:continue
 hit,nor,idx,dist=contact.find_nearest(v.co)
 if hit is not None and dist<.025 and (v.co-hit).dot(nor)<.003:
  q=hit+nor*.003;contact_shifts.append((q-v.co).length);v.co=q
hair.data.update();bpy.context.view_layer.update()
# Hair-owned root lining covers strand gaps at crown/occiput, with no skin deletion.
rootmat=h._flat_paper_material('MIA_V17_HairRootAsh',(.067,.065,.069,1))
for skin_name in ['MIA_V06_BODY_SKIN','MIA_V14_SculptedSkin']:
 ob=bpy.data.objects[skin_name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mm.vertices];selected=[]
 for po in mm.polygons:
  q=sum((pts[i] for i in po.vertices),Vector())/len(po.vertices)
  threshold=1.605 if q.y<0 and abs(q.x)<.06 else 1.58 if q.y<.025 else 1.56
  if all(pts[i].z>threshold for i in po.vertices):selected.append(po.index)
 ids=sorted({i for j in selected for i in mm.polygons[j].vertices});mp={i:j for j,i in enumerate(ids)};m=bpy.data.meshes.new('V17_RootLiningMesh');normalmat=ev.matrix_world.to_3x3().inverted().transposed();m.from_pydata([pts[i]+(normalmat@mm.vertices[i].normal).normalized()*.001 for i in ids],[],[[mp[i] for i in mm.polygons[j].vertices] for j in selected]);uvnew=m.uv_layers.new(name='UVMap')
 if mm.uv_layers.active:
  for ii,jj in enumerate(selected):
   for aa,bb in zip(m.polygons[ii].loop_indices,mm.polygons[jj].loop_indices):uvnew.data[aa].uv=mm.uv_layers.active.data[bb].uv
 for po in m.polygons:po.use_smooth=True
 lining=bpy.data.objects.new('MIA_V17_RootLining_'+skin_name,m);col.objects.link(lining);m.materials.append(rootmat);vg=lining.vertex_groups.new(name='Roots_Locked');vg.add(list(range(len(m.vertices))),1,'REPLACE');lining['ownership']='Hair-only scalp root surface, original head intact';owned.append(lining);ev.to_mesh_clear()
paired('crownB_contact_fit')

cam.data.ortho_scale=.48;h._aim(cam,(0,-2,1.54),(0,0,1.54));native=OUT/'Mia_PixalHead_v17.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native))
bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera
for name,loc in [('front',(0,-2,1.54)),('left',(1.4,-1.4,1.54)),('right',(-1.4,-1.4,1.54)),('profile',(2,0,1.54)),('back',(0,2,1.54))]:
 h._aim(cam,loc,(0,0,1.54));scene.render.filepath=str(OUT/('beauty_'+name+'.png'));bpy.ops.render.render(write_still=True)
atlas=bpy.data.materials['MIA_V17_Pixal_AshGray_Detail'].node_tree.nodes['ORIGINAL_PIXAL_ATLAS'].image
r={'native_sha256':sha(native),'source_hashes':hashes,'recipe_sha256':sha(Path(__file__)),'hair_texture_intensity_quantiles':quantiles,'source_faces_retained':len(keep),'source_vertices_retained':len(used),'component_segmentation':components,'head_change':'8mm maximum smooth above-brow crown lift; z<=1.56 fixed','warp_key_coordinate_counts':warp_counts,'hair_crown_contact_vertex_count':len(contact_shifts),'hair_crown_contact_max_delta':max(contact_shifts,default=0),'fit':'Uniform .90 refinement of v16 source fit about raw-eye center; no anisotropic squash','raw_atlas':{'name':atlas.name,'size':list(atlas.size),'packed':bool(atlas.packed_file)},'state':'Art candidate; inspect visible boundaries before final'}
(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE_SHA',r['native_sha256'])
