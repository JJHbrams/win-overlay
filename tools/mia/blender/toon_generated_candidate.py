"""Non-destructive NPR review renderer for an already-imported generated candidate.

Run only after generation has released GPU resources:
 blender --background --factory-startup --disable-autoexec --python toon_generated_candidate.py -- --input native.blend --output out --label mia-toon
"""
import argparse, bpy, os, sys, hashlib, json

def parse():
    p=argparse.ArgumentParser(description='Create non-destructive toon QA renders from a native candidate blend.')
    p.add_argument('--input',required=True); p.add_argument('--output',required=True); p.add_argument('--label',default='mia-toon-candidate')
    p.add_argument('--no-outline',action='store_true'); p.add_argument('--albedo-only',action='store_true')
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
def geom_fingerprint():
    h=hashlib.sha256(); total=[0,0]
    for o in sorted((x for x in bpy.data.objects if x.type=='MESH'),key=lambda x:x.name):
        h.update(o.name.encode()); h.update(str(len(o.data.vertices)).encode()); h.update(str(len(o.data.polygons)).encode())
        total[0]+=len(o.data.vertices); total[1]+=len(o.data.polygons)
        for v in o.data.vertices: h.update(('%0.7f,%0.7f,%0.7f;'%(v.co.x,v.co.y,v.co.z)).encode())
    return {'sha256':h.hexdigest(),'vertices':total[0],'polygons':total[1]}
def toon_copy(source, albedo_only):
    # source remains the archived GLB PBR material; this independent duplicate retains its images/UV nodes.
    m=source.copy(); m.name='TOON__'+source.name; m.use_nodes=True; nt=m.node_tree; out=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL'),None)
    bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not out or not bs: return m
    emission=nt.nodes.new('ShaderNodeEmission'); emission.name='Toon albedo emission (no specular)'; emission.inputs['Strength'].default_value=1.0
    base=bs.inputs.get('Base Color'); source_socket=base.links[0].from_socket if base and base.links else None
    if albedo_only:
        if source_socket: nt.links.new(source_socket,emission.inputs['Color'])
        elif base: emission.inputs['Color'].default_value=base.default_value
    else:
        diffuse=nt.nodes.new('ShaderNodeBsdfDiffuse'); diffuse.name='Toon diffuse lighting'; diffuse.inputs['Color'].default_value=(1,1,1,1); diffuse.inputs['Roughness'].default_value=1.0
        normal=bs.inputs.get('Normal')
        if normal and normal.links: nt.links.new(normal.links[0].from_socket,diffuse.inputs['Normal'])
        to_rgb=nt.nodes.new('ShaderNodeShaderToRGB'); to_rgb.name='Toon light quantization'
        ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.name='Three level shadow ramp'; ramp.color_ramp.interpolation='CONSTANT'
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]); ramp.color_ramp.elements[0].position=.30; ramp.color_ramp.elements[0].color=(.55,.55,.55,1)
        mid=ramp.color_ramp.elements.new(.57); mid.color=(.82,.82,.82,1)
        hi=ramp.color_ramp.elements.new(.78); hi.color=(1,1,1,1)
        multiply=nt.nodes.new('ShaderNodeMixRGB'); multiply.name='Albedo × toon shadow'; multiply.blend_type='MULTIPLY'; multiply.inputs[0].default_value=1.0
        nt.links.new(diffuse.outputs['BSDF'],to_rgb.inputs['Shader']); nt.links.new(to_rgb.outputs['Color'],ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'],multiply.inputs[2])
        if source_socket: nt.links.new(source_socket,multiply.inputs[1])
        elif base: multiply.inputs[1].default_value=base.default_value
        nt.links.new(multiply.outputs['Color'],emission.inputs['Color'])
    for link in list(out.inputs['Surface'].links): nt.links.remove(link)
    nt.links.new(emission.outputs['Emission'],out.inputs['Surface'])
    return m
def main():
    a=parse(); inp=os.path.abspath(a.input); out=os.path.abspath(a.output)
    if not os.path.isfile(inp): raise FileNotFoundError(inp)
    os.makedirs(out,exist_ok=True); bpy.ops.wm.open_mainfile(filepath=inp)
    before=geom_fingerprint(); scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=700; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.view_settings.look='None'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
    originals={m.name:m for m in bpy.data.materials if not m.name.startswith('TOON__')}
    replacements={name:toon_copy(m,a.albedo_only) for name,m in originals.items()}
    swapped=[]
    for o in (x for x in bpy.data.objects if x.type=='MESH'):
        for i,m in enumerate(o.data.materials):
            if m and m.name in replacements: swapped.append((o,i,m)); o.data.materials[i]=replacements[m.name]
    if not a.no_outline:
        scene.render.use_freestyle=True
        fs=scene.view_layers[0].freestyle_settings; lineset=fs.linesets[0]; lineset.select_silhouette=True; lineset.select_border=True; lineset.select_crease=False; lineset.select_edge_mark=False
        fs.linesets[0].linestyle.thickness=.7
    else: scene.render.use_freestyle=False
    cams={}
    for o in bpy.data.objects:
        if o.type=='CAMERA' and o.name.lower().startswith('qa_camera_'): cams[o.name.lower().replace('qa_camera_','').replace('_','')]=o
    expected=['front','side','back','threequarter','facecloseup']; missing=[x for x in expected if x not in cams]
    if missing: raise RuntimeError('Missing persistent QA cameras: '+', '.join(missing))
    for key in expected:
        scene.camera=cams[key]; scene.render.resolution_x,scene.render.resolution_y=((700,700) if key=='facecloseup' else (700,900)); scene.render.filepath=os.path.join(out,a.label+'-'+key+'.png'); bpy.ops.render.render(write_still=True)
    scene.camera=cams['front']; scene['toon_preview_status']='generated candidate NPR preview only; fidelity/topology unapproved'; scene['toon_preview_mode']='albedo-only' if a.albedo_only else '3-level diffuse × albedo emission; no specular'
    after=geom_fingerprint()
    if after != before: raise RuntimeError('Geometry integrity assertion failed')
    report={'input':inp,'geometry_before':before,'geometry_after':after,'pbr_archived_materials':sorted(originals),'toon_materials':sorted(replacements),'cameras':{k:cams[k].name for k in expected},'outline_enabled':not a.no_outline,'mode':scene['toon_preview_mode'],'status':scene['toon_preview_status']}
    with open(os.path.join(out,a.label+'-toon-inspection.json'),'w',encoding='utf8') as f: json.dump(report,f,indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,a.label+'-native-toon-preview.blend'))
if __name__=='__main__': main()
