"""UV-anchored narrow lower-lid creases; source pigment and UVs stay intact."""
import bpy
import numpy as np

def apply_fatigue_ink(face):
    size=1024
    mask=np.zeros((size,size),dtype=np.float32)
    mesh=face.data;mesh.calc_loop_triangles()
    uv=mesh.uv_layers.active.data
    basis=mesh.shape_keys.key_blocks[0].data
    for tri in mesh.loop_triangles:
        if mesh.polygons[tri.polygon_index].material_index!=7:continue
        p=np.array([tuple(basis[i].co) for i in tri.vertices])
        if p[:,1].max()<.03 or p[:,2].min()>1.532 or p[:,2].max()<1.506:continue
        t=np.array([tuple(uv[i].uv) for i in tri.loops])*size
        lo=np.maximum(np.floor(t.min(axis=0)).astype(int),0);hi=np.minimum(np.ceil(t.max(axis=0)).astype(int),size-1)
        if np.any(hi<lo):continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
        if abs(den)<1e-8:continue
        a=((t[1,1]-t[2,1])*(xx+.5-t[2,0])+(t[2,0]-t[1,0])*(yy+.5-t[2,1]))/den
        b=((t[2,1]-t[0,1])*(xx+.5-t[2,0])+(t[0,0]-t[2,0])*(yy+.5-t[2,1]))/den
        c=1-a-b;inside=(a>=0)&(b>=0)&(c>=0)
        xyz=a[...,None]*p[0]+b[...,None]*p[1]+c[...,None]*p[2]
        x=np.abs(xyz[...,0]);z=xyz[...,2];y=xyz[...,1]
        u=(x-.037)/.023
        curve=1.5205+.0045*u*u
        fade=np.clip((1-np.abs(u))/.3,0,1)*np.clip((y-.025)/.025,0,1)
        ink=(.47*np.exp(-((z-curve)/.00065)**2)+.14*np.exp(-((z-curve-.0012)/.0025)**2)) * fade
        ink+=.16*np.exp(-((z-curve+.0038)/.0007)**2)*fade*np.clip((x-.026)/.014,0,1)
        region=mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1];np.maximum(region,np.where(inside,ink,0),out=region)
    rgba=np.ones((size,size,4),dtype=np.float32);rgba[:,:,:3]=mask[:,:,None]
    im=bpy.data.images.new('MIA_Astra_UV_LowerLid_Ink_v08',width=size,height=size,alpha=True)
    im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(rgba.ravel());im.pack()
    mat=face.material_slots[7].material
    nodes=mat.node_tree.nodes;links=mat.node_tree.links
    emit=next(n for n in nodes if n.type=='EMISSION')
    old=emit.inputs['Color'].links[0].from_socket
    tex=nodes.new('ShaderNodeTexImage');tex.name='MIA_UV_Fatigue_Ink';tex.image=im
    mix=nodes.new('ShaderNodeMixRGB');mix.name='MIA_Narrow_LowerLid_Ink';mix.blend_type='MULTIPLY';mix.inputs[2].default_value=(.36,.34,.37,1)
    links.new(tex.outputs['Color'],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(mix.outputs[0],emit.inputs['Color'])
    return {'image':im.name,'uv_unchanged':True,'source_pigment_unchanged':True,'maximum_mask':float(mask.max()),'method':'narrow lower-lid curves rasterized on existing skin UV triangles'}
