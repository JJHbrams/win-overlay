"""Bounded body-only diagnosis and normal A/B for Mia v06 breast/rib shading."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
import bpy
from mathutils import Vector

def parse():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True);return p.parse_args(sys.argv[sys.argv.index('--')+1:])
def geo_hash(m):
 h=hashlib.sha256()
 for v in m.vertices:h.update(struct.pack('<3f',*v.co))
 for p in m.polygons:h.update(struct.pack('<%dI'%len(p.vertices),*p.vertices))
 return h.hexdigest()
def position_hash(m):
 h=hashlib.sha256()
 for v in m.vertices:h.update(struct.pack('<3f',*v.co))
 return h.hexdigest()
def topology_set_hash(m):
 h=hashlib.sha256()
 for p in sorted(tuple(sorted(p.vertices)) for p in m.polygons):h.update(struct.pack('<%dI'%len(p),*p))
 return h.hexdigest()
def linked(obj):bpy.context.scene.collection.objects.link(obj);return obj
def material():
 m=bpy.data.materials.new('MIA_V06_NORMAL_AB_CLAY');m.use_nodes=True;n=m.node_tree.nodes;n.clear();o=n.new('ShaderNodeOutputMaterial');b=n.new('ShaderNodeBsdfPrincipled');b.inputs['Base Color'].default_value=(.23,.26,.31,1);b.inputs['Roughness'].default_value=.88;m.node_tree.links.new(b.outputs['BSDF'],o.inputs['Surface']);return m
def aim(cam,loc,target):cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
def component_sizes(mesh):
 left=set(range(len(mesh.vertices)));adj={i:set() for i in left}
 for e in mesh.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  q=[left.pop()];c=set(q)
  while q:
   v=q.pop()
   for n in adj[v]&left:left.remove(n);c.add(n);q.append(n)
  out.append(len(c))
 return sorted(out,reverse=True)
def component_bust_report(mesh,bust):
 left=set(range(len(mesh.vertices)));adj={i:set() for i in left};out=[]
 for e in mesh.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 while left:
  q=[left.pop()];c=set(q)
  while q:
   v=q.pop()
   for n in adj[v]&left:left.remove(n);c.add(n);q.append(n)
  count=len(c&bust)
  if count:out.append({'component_vertices':len(c),'bust_weight_vertices':count,'all_bust_weighted':count==len(c)})
 return sorted(out,key=lambda x:x['component_vertices'],reverse=True)
def main():
 a=parse();out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=a.input);s=bpy.context.scene;body=bpy.data.objects['MIA_V06_BODY_SKIN'];face=bpy.data.objects['MIA_V06_FACE_SKIN'];m=body.data
 groups={g.name:g.index for g in body.vertex_groups};bust=set()
 for n,i in groups.items():
  if 'Bust' in n:
   bust.update(v.index for v in m.vertices if any(x.group==i and x.weight>.2 for x in v.groups))
 boundary=sum((e.vertices[0] in bust)!=(e.vertices[1] in bust) for e in m.edges)
 before={'geometry_hash':geo_hash(m),'position_hash':position_hash(m),'topology_set_hash':topology_set_hash(m),'vertices':len(m.vertices),'polygons':len(m.polygons),'uv_layers':[u.name for u in m.uv_layers], 'custom_normals':getattr(m,'has_custom_normals',None),'smooth_polygons':sum(p.use_smooth for p in m.polygons),'component_sizes':component_sizes(m)[:20],'bust_weight_vertices':len(bust),'bust_boundary_edges':boundary,'components_with_bust_weights':component_bust_report(m,bust)}
 # isolate source body for the A image; face/cards are deliberately absent.
 for o in s.objects:o.hide_render=o not in (body,)
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_layers[0].material_override=material()
 cd=bpy.data.cameras.new('MIA_V06_NORMAL_AB_CAMERA');cd.type='ORTHO';cd.ortho_scale=.82;cam=linked(bpy.data.objects.new(cd.name,cd));s.camera=cam
 for i,(loc,energy) in enumerate((((2.2,-3,3),260),((-2,-2,2),120),((0,2.5,2.5),150))):
  d=bpy.data.lights.new('MIA_V06_NORMAL_AB_LIGHT_%d'%i,'AREA');d.energy=energy;d.shape='DISK';d.size=2
  o=linked(bpy.data.objects.new(d.name,d));o.location=loc;aim(o,loc,(0,0,1.16))
 for name,loc in [('profile',(3,0,1.16)),('three_quarter',(2.2,-2.2,1.16))]:aim(cam,loc,(0,0,1.16));s.render.filepath=str(out/('before_'+name+'.png'));bpy.ops.render.render(write_still=True)
 # Copy only derived body; recalc normals on the copy.  No UV/coordinate/topology operation occurs.
 test=body.copy();test.data=body.data.copy();test.name='MIA_V06_BODY_NORMAL_AB';linked(test);body.hide_render=True
 bpy.context.view_layer.objects.active=test;test.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');test.select_set(False)
 after={'geometry_hash':geo_hash(test.data),'position_hash':position_hash(test.data),'topology_set_hash':topology_set_hash(test.data),'vertices':len(test.data.vertices),'polygons':len(test.data.polygons),'uv_layers':[u.name for u in test.data.uv_layers], 'custom_normals':getattr(test.data,'has_custom_normals',None),'smooth_polygons':sum(p.use_smooth for p in test.data.polygons)}
 for name,loc in [('profile',(3,0,1.16)),('three_quarter',(2.2,-2.2,1.16))]:aim(cam,loc,(0,0,1.16));s.render.filepath=str(out/('after_recalc_'+name+'.png'));bpy.ops.render.render(write_still=True)
 (out/'breast-normal-diagnosis.json').write_text(json.dumps({'before':before,'after':after,'coordinates_unchanged':before['position_hash']==after['position_hash'],'topology_set_unchanged':before['topology_set_hash']==after['topology_set_hash'],'uv_unchanged':before['uv_layers']==after['uv_layers'],'interpretation':'Bust weighted region has boundary edges into the same mesh. Recalculate may reverse polygon winding, so ordered geometry hash is expected to change; coordinate and unordered-topology hashes record the bounded test. Source, Face and UVs remain untouched.'},indent=2),encoding='utf-8')
if __name__=='__main__':main()
