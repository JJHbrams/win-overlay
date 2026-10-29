"""Project exact front/back conditioning art onto an existing generated BODY mesh only."""
import argparse,bpy,os,sys,math,hashlib,json
from mathutils import Vector

REFROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..','..','asset','mia','references','conditioning'))
FRONT=os.path.join(REFROOT,'body_mv_condition_front.png')
BACK=os.path.join(REFROOT,'body_mv_condition_back.png')
def parse():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True);p.add_argument('--label',default='mia-body-projected-v37');p.add_argument('--front-art',default=FRONT);p.add_argument('--back-art',default=BACK);return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def fingerprint(o):
 h=hashlib.sha256();h.update(str(len(o.data.vertices)).encode());h.update(str(len(o.data.polygons)).encode())
 for v in o.data.vertices:h.update(('%0.7f,%0.7f,%0.7f;'%(v.co.x,v.co.y,v.co.z)).encode())
 return h.hexdigest()
def image(path,name):
 im=bpy.data.images.load(path,check_existing=False);im.name=name;im.pack();im.use_fake_user=True;return im
def clamp(v):return max(0.,min(1.,v))
def main():
 a=parse(); inp=os.path.abspath(a.input);out=os.path.abspath(a.out);os.makedirs(out,exist_ok=True)
 front_path=os.path.abspath(a.front_art);back_path=os.path.abspath(a.back_art)
 bpy.ops.wm.open_mainfile(filepath=inp)
 body=bpy.data.objects.get('Mia_Graft_Body_Editable') or bpy.data.objects.get('Mesh_0')
 if not body or body.type!='MESH':raise RuntimeError('Expected named body module or original Mesh_0')
 body.name='Mia_Graft_Body_Editable'
 before=fingerprint(body); root=next((o for o in bpy.data.objects if o.type=='EMPTY' and 'pixal-v32_root' in o.name.lower()),None)
 pixal_from_body=(root.matrix_world.inverted()@body.matrix_world) if root else body.matrix_world.copy()
 front=body.data.uv_layers.get('UV_PROJ_BODY_FRONT') or body.data.uv_layers.new(name='UV_PROJ_BODY_FRONT')
 back=body.data.uv_layers.get('UV_PROJ_BODY_BACK') or body.data.uv_layers.new(name='UV_PROJ_BODY_BACK')
 tan=math.tan(math.radians(10)); d=3.119205
 # Store per-loop projection UV from canonical Pixal coordinates. V is normalized to the 1.68m body height.
 for p in body.data.polygons:
  for li in p.loop_indices:
   q=pixal_from_body@body.data.vertices[body.data.loops[li].vertex_index].co
   front.data[li].uv=(.5+q.x/(2*(q.y+d)*tan),.5+q.z/(2*(q.y+d)*tan))
   back.data[li].uv=(.5-q.x/(2*(d-q.y)*tan),.5+q.z/(2*(d-q.y)*tan))
 # Smooth point weights from canonical face direction. Side faces remain generated-atlas material.
 for name,sign in [('BodyProjectionFrontWeight',-1),('BodyProjectionBackWeight',1)]:
  attr=body.data.attributes.get(name) or body.data.attributes.new(name,'FLOAT','POINT')
  sums=[0.0]*len(body.data.vertices);counts=[0]*len(body.data.vertices)
  for p in body.data.polygons:
   n=(pixal_from_body.to_3x3()@p.normal).normalized(); w=clamp((sign*n.y-.10)/.30)
   for vi in p.vertices:sums[vi]+=w;counts[vi]+=1
  for i,v in enumerate(attr.data):v.value=sums[i]/max(1,counts[i])
 frontim=image(front_path,'BODY_PROJ_FRONT_EXACT');backim=image(back_path,'BODY_PROJ_BACK_EXACT')
 # Archive original PBR material and attach a copy only to the body; projected head materials remain untouched.
 for slot in body.material_slots:
  src=slot.material
  if not src:continue
  projected=src.copy();projected.name='BODY_ART_PROJECTION__'+src.name;projected.use_nodes=True;nt=projected.node_tree
  bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None);base=bs.inputs.get('Base Color') if bs else None
  if not base:continue
  original=base.links[0].from_socket if base.links else None
  texf=nt.nodes.new('ShaderNodeTexImage');texf.name='Body Exact Art Front';texf.image=frontim;uvf=nt.nodes.new('ShaderNodeUVMap');uvf.uv_map=front.name
  texb=nt.nodes.new('ShaderNodeTexImage');texb.name='Body Exact Art Back';texb.image=backim;uvb=nt.nodes.new('ShaderNodeUVMap');uvb.uv_map=back.name
  af=nt.nodes.new('ShaderNodeAttribute');af.attribute_name='BodyProjectionFrontWeight';ab=nt.nodes.new('ShaderNodeAttribute');ab.attribute_name='BodyProjectionBackWeight'
  mixf=nt.nodes.new('ShaderNodeMixRGB');mixf.name='Body original/front blend';mixf.blend_type='MIX';mixb=nt.nodes.new('ShaderNodeMixRGB');mixb.name='Body front/back blend';mixb.blend_type='MIX'
  nt.links.new(uvf.outputs['UV'],texf.inputs['Vector']);nt.links.new(uvb.outputs['UV'],texb.inputs['Vector']);nt.links.new(af.outputs['Fac'],mixf.inputs[0]);nt.links.new(ab.outputs['Fac'],mixb.inputs[0]);nt.links.new(texf.outputs['Color'],mixf.inputs[2]);nt.links.new(texb.outputs['Color'],mixb.inputs[2]);nt.links.new(mixf.outputs['Color'],mixb.inputs[1])
  if original:nt.links.new(original,mixf.inputs[1])
  else:mixf.inputs[1].default_value=base.default_value
  for l in list(base.links):nt.links.remove(l)
  nt.links.new(mixb.outputs['Color'],base);slot.material=projected
 after=fingerprint(body)
 if after!=before:raise RuntimeError('Geometry fingerprint changed during material projection')
 scene=bpy.context.scene;scene['Mia_status']='body art texture projection candidate; geometry/accessory fidelity unapproved';scene['body_projection']='front/back exact conditioning images, FOV20 d3.119205 perspective depth; side retains original atlas'
 report={'input':inp,'body_geometry_before':before,'body_geometry_after':after,'front':front_path,'back':back_path,'root_inverse_used':bool(root),'uv_layers':[front.name,back.name],'point_weights':['BodyProjectionFrontWeight','BodyProjectionBackWeight'],'status':scene['Mia_status']}
 with open(os.path.join(out,a.label+'-projection-report.json'),'w') as f:json.dump(report,f,indent=2)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,a.label+'-native.blend'))
if __name__=='__main__':main()
