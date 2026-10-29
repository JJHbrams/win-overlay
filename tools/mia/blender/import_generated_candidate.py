"""Import a generated GLB intact and produce reproducible Blender review views.

Run: blender --background --factory-startup --disable-autoexec --python import_generated_candidate.py -- --input model.glb --output output_dir
"""
import argparse, bpy, os, sys, json, hashlib, math
from mathutils import Vector

REFROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'asset', 'mia', 'references'))
REFS = ["mia-clean-master-v22.png", "mia-canonical-source-v22.png", "mia-expressions-clean-16-v22.png"]

def args():
    p=argparse.ArgumentParser(description="Import actual generated GLB and render native Blender QA views.")
    p.add_argument('--input', required=True, help='Existing external textured .glb file')
    p.add_argument('--output', required=True, help='New/reusable output directory')
    p.add_argument('--reference-dir', default=REFROOT, help='Directory containing the three approved Mia reference PNGs')
    p.add_argument('--height', type=float, default=1.68)
    p.add_argument('--label', default='mia-local-candidate')
    p.add_argument('--front-axis', choices=['+Z','-Z','+X','-X'], default='+Z', help='GLB local forward axis; +Z maps to Blender -Y camera-facing front')
    p.add_argument('--transparent', action='store_true', help='Render transparent RGBA backgrounds')
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def bounds(obs):
    pts=[]
    for o in obs:
        if o.type=='MESH': pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return lo,hi
def aim(o, point): o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
def material(name,color,rough=.68):
    m=bpy.data.materials.new(name); m.use_nodes=True; bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough; return m

a=args(); inp=os.path.abspath(a.input); out=os.path.abspath(a.output); reference_dir=os.path.abspath(a.reference_dir)
if not os.path.isfile(inp): raise FileNotFoundError(inp)
if not inp.lower().endswith('.glb'): raise ValueError('--input must be an actual .glb')
os.makedirs(out,exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=inp)
imported=list(bpy.context.selected_objects)
if not imported: raise RuntimeError('glTF importer returned no objects')
root=bpy.data.objects.new(a.label+'_ROOT',None); bpy.context.scene.collection.objects.link(root)
for o in imported:
    if o.parent is None: o.parent=root
# GLB convention maps local +Z (front) to Blender -Y (camera-facing). Optional whole-root correction only.
rot={'+Z':0,'-Z':math.pi,'+X':-math.pi/2,'-X':math.pi/2}[a.front_axis]; root.rotation_euler[2]=rot
bpy.context.view_layer.update()
lo,hi=bounds(imported); h=hi.z-lo.z
if h<=0: raise RuntimeError('Imported mesh has no positive Z height')
root.scale=(a.height/h,)*3; bpy.context.view_layer.update()
lo,hi=bounds(imported); root.location += Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z)); bpy.context.view_layer.update()
lo,hi=bounds(imported); center=(lo+hi)/2

scene=bpy.context.scene; scene['Mia_status']='unrigged generated candidate; fidelity and topology unapproved'; scene['source_glb']=os.path.basename(inp); scene['source_sha256']=sha256(inp); scene['import_method']='bpy.ops.import_scene.gltf; hierarchy, UVs, PBR materials retained'; scene['requested_height_m']=a.height; scene['front_axis']=a.front_axis; scene['rest_camera']='front'; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.film_transparent=a.transparent
scene.view_settings.look='AgX - Medium Low Contrast'
world=bpy.data.worlds.new('Pale gray studio') if not bpy.data.worlds else bpy.data.worlds[0]; scene.world=world; world.use_nodes=True; world.node_tree.nodes['Background'].inputs['Color'].default_value=(.72,.74,.76,1); world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28
scene['known_reference_sha256']={fn:sha256(os.path.join(reference_dir,fn)) for fn in REFS}
for fn in REFS:
    im=bpy.data.images.load(os.path.join(reference_dir,fn),check_existing=False); im.name='REF_'+fn; im.pack(); im.use_fake_user=True
# Pack model texture images too; only refs are kept as non-render image assets.
for im in bpy.data.images:
    if im.name.startswith('REF_') or im.name in {'Render Result','Viewer Node'}: continue
    if im.has_data: im.pack(); im.use_fake_user=True
def packed_bytes(im):
    return len(im.packed_file.data) if im.packed_file else 0
for fn in REFS:
    im=bpy.data.images.get('REF_'+fn)
    if not im or packed_bytes(im) <= 0: raise RuntimeError('Reference packing failed: '+fn)

def light(n,loc,e,size):
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=n; o.data.energy=e; o.data.shape='DISK'; o.data.size=size; aim(o,center); return o
d=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
light('Studio_Key',(-d*1.6,-d*2.0,center.z+d*.8),900,d*1.2); light('Studio_Fill',(d*1.5,-d*1.2,center.z+d*.35),450,d*1.5); light('Studio_Rim',(d*1.4,d*1.5,center.z+d*.9),700,d)
def camera(name):
    bpy.ops.object.camera_add(); o=bpy.context.object; o.name=name; o.data.type='ORTHO'; return o
cams={k:camera('QA_Camera_'+k.title()) for k in ('front','side','back','threequarter','facecloseup')}
scene.camera=cams['front']
clay=material('QA Clay Override',(.43,.38,.35),.72); wire=material('QA Wire Override',(.08,.08,.08),.55)
def render(key,name,loc,target,scale,size=(700,900),override=None):
    cam=cams[key]; scene.camera=cam; cam.location=loc; aim(cam,target); cam.data.ortho_scale=scale; scene.render.resolution_x,scene.render.resolution_y=size
    previous=bpy.context.view_layer.material_override; bpy.context.view_layer.material_override=override
    try: scene.render.filepath=os.path.join(out,name+'.png'); bpy.ops.render.render(write_still=True)
    finally: bpy.context.view_layer.material_override=previous
height=hi.z-lo.z; full=max(height,(hi.x-lo.x)*(900/700))*1.12; dist=d*3
render('front',a.label+'-front',(center.x,center.y-dist,center.z),center,full)
render('side',a.label+'-side',(center.x+dist,center.y,center.z),center,full)
render('back',a.label+'-back',(center.x,center.y+dist,center.z),center,full)
render('threequarter',a.label+'-threequarter',(center.x+dist*.72,center.y-dist*.72,center.z),center,full)
face_target=Vector((center.x,center.y,hi.z-height*.105)); render('facecloseup',a.label+'-face-closeup',(center.x,center.y-dist,face_target.z),face_target,height*.28,(700,700))
render('front',a.label+'-front-clay',(center.x,center.y-dist,center.z),center,full,(700,900),clay)
render('threequarter',a.label+'-threequarter-clay',(center.x+dist*.72,center.y-dist*.72,center.z),center,full,(700,900),clay)
scene.camera=cams['front']
meshes=[o for o in imported if o.type=='MESH']; mats={m.name for o in meshes for m in o.data.materials if m}; uv=sum(1 for o in meshes if o.data.uv_layers)
report={'input':inp,'sha256':scene['source_sha256'],'blender':bpy.app.version_string,'height_m':a.height,'bounds_min':list(lo),'bounds_max':list(hi),'dimensions':list(hi-lo),'components':len(imported),'meshes':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'materials':sorted(mats),'meshes_with_uv':uv,'empty_heads':[o.name for o in imported if o.type=='EMPTY' and o.parent is None],'cameras':{k:c.name for k,c in cams.items()},'rest_camera':cams['front'].name,'packed_references':{im.name:packed_bytes(im) for im in bpy.data.images if im.name.startswith('REF_')},'packed_model_images':[{'name':im.name,'filepath':im.filepath,'packed_bytes':packed_bytes(im)} for im in bpy.data.images if not im.name.startswith('REF_') and im.name not in {'Render Result','Viewer Node'}],'status':scene['Mia_status']}
with open(os.path.join(out,a.label+'-inspection.json'),'w',encoding='utf8') as f: json.dump(report,f,indent=2)
with open(os.path.join(out,'README-ko.txt'),'w',encoding='utf8') as f: f.write('생성 GLB를 Blender에 원형 보존해 불러온 검토 후보입니다. 미아 충실도·토폴로지 승인은 아직 아닙니다.\n')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,a.label+'-native.blend'))
