import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent/'boundary1';P.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'sculpt2/Mia_HairStructure_v24.blend'),use_scripts=False)
s=bpy.context.scene;o=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];mesh=o.data
original=[v.co.copy() for v in mesh.vertices]
adj={v.index:[] for v in mesh.vertices};boundary={}
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
for e in bm.edges:
 a,b=e.verts;adj[a.index].append(b.index);adj[b.index].append(a.index)
 if e.is_boundary:
  boundary.setdefault(a.index,[]).append(b.index);boundary.setdefault(b.index,[]).append(a.index)
bm.free()
def ramp(v,a,b,feather):return max(0,min(1,(v-a)/feather,(b-v)/feather))
weights={i:ramp(abs(p.x),.045,.135,.015)*ramp(p.y,-.044,.055,.016)*ramp(p.z,1.445,1.572,.020) for i,p in enumerate(original)}
selected=[i for i,n in boundary.items() if len(n)==2 and weights[i]>.001]
cams={}
for label,deg in [('profile',82),('opposite_profile',-82),('front_oblique',35),('opposite_oblique',-35)]:
 d=bpy.data.cameras.new('Boundary '+label);d.type='ORTHO';d.ortho_scale=.30;c=bpy.data.objects.new(d.name,d);s.collection.objects.link(c);a=math.radians(deg);c.location=(2*math.sin(a),-2*math.cos(a),1.515);c.rotation_euler=(Vector((0,0,1.515))-c.location).to_track_quat('-Z','Y').to_euler();cams[label]=c
def render(prefix):
 for label,c in cams.items():
  s.camera=c;s.render.filepath=str(P/(prefix+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
render('baseline')
coords=[p.copy() for p in original]
for _ in range(8):
 nxt=[p.copy() for p in coords]
 for i in selected:
  a,b=boundary[i];desired=(coords[a]+coords[b])*.5;disp=(desired-coords[i])*.62*weights[i];value=coords[i]+disp;delta=value-original[i]
  if delta.length>.004:value=original[i]+delta.normalized()*.004
  nxt[i]=value
 coords=nxt
# Blend a single interior ring to avoid creating a sharp ridge at the boundary.
selectedset=set(selected)
for i,neighbors in adj.items():
 if i in selectedset or weights[i]<=0:continue
 near=[j for j in neighbors if j in selectedset]
 if near:coords[i]+=sum((coords[j]-original[j] for j in near),Vector())/len(near)*.35*weights[i]
for v,p in zip(mesh.vertices,coords):v.co=p
mesh.update()
render('candidate')
out=P/'Mia_HairBoundary1_v24.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
changed=[(i,(coords[i]-original[i]).length) for i in range(len(coords)) if (coords[i]-original[i]).length>1e-8]
report={'status':'LOCAL PROBE, visually unreviewed','selected_boundary_vertices':len(selected),'changed_vertices':len(changed),'max_displacement_m':max(d for _,d in changed),'mean_displacement_m':sum(d for _,d in changed)/len(changed),'owner':o.name,'topology_and_uv':'unchanged','limitations':['Does not close all extraction holes or reconstruct missing hair','Baked source normal texture retained; local shading requires review'],'changed':changed}
(P/'report.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='changed'})
