#!/usr/bin/env python3
"""Construct Mia's first continuous hair-mass prototype from frozen anatomy."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(r"D:/ai/Mia3DWork/model-v02/hair-mass-stage")
EXPECTED = "d90744a9ec2370ae8d9564e482fbffd6b2485334f9571278d4482ce26ac943ca"

def args():
    p=argparse.ArgumentParser(); v=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p.add_argument('--input', required=True); p.add_argument('--output', default=str(ROOT/'Mia_HairMass_v01.blend'))
    p.add_argument('--output-dir', default=str(ROOT/'previews')); p.add_argument('--report', default=str(ROOT/'hair-mass-report.json'))
    return p.parse_args(v)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def fingerprint(o):
    h=hashlib.sha256(); m=o.data
    for v in m.vertices:h.update(('%0.9f,%0.9f,%0.9f;'%tuple(v.co)).encode())
    for f in m.polygons:h.update(('p'+','.join(map(str,f.vertices))).encode())
    for uv in m.uv_layers:
        h.update(uv.name.encode())
        for x in uv.data:h.update(('%0.9f,%0.9f;'%tuple(x.uv)).encode())
    for k in (m.shape_keys.key_blocks if m.shape_keys else []):
        h.update(k.name.encode())
        for x in k.data:h.update(('%0.9f,%0.9f,%0.9f;'%tuple(x.co)).encode())
    return h.hexdigest()
def coll(n):
    c=bpy.data.collections.get(n)
    if not c:c=bpy.data.collections.new(n);bpy.context.scene.collection.children.link(c)
    return c
def move(o,c):
    for q in list(o.users_collection):q.objects.unlink(o)
    c.objects.link(o);return o
def mat(n,color):
    m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.82;b.inputs['Specular IOR Level'].default_value=.10
    return m
def tag(o,region,side='CENTER',overlaps='foundation'):
    o['owner']='Mia';o['stage']='HAIR_MASS_V01';o['role']='HAIR_SURFACE_PATCH';o['deformation_region']=region;o['anatomical_side']=side
    o['construction']='longitudinal_lateral_shallow_convex_surface_grid';o['intentional_overlap']=overlaps
def smooth(o):
    for f in o.data.polygons:f.use_smooth=True
def make_mesh(name,vs,fs,material,c,region,side='CENTER',overlaps='foundation'):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(vs,[],fs);me.materials.append(material);me.update()
    o=move(bpy.data.objects.new(name,me),c);tag(o,region,side,overlaps);smooth(o)
    sol=o.modifiers.new('Physical surface thickness 1.5mm','SOLIDIFY');sol.thickness=.0015;sol.offset=-.25
    return o
def cubic(ps,t):
    x=t*(len(ps)-1);i=min(int(x),len(ps)-2);u=x-i;a=Vector(ps[max(0,i-1)]);b=Vector(ps[i]);c=Vector(ps[i+1]);d=Vector(ps[min(len(ps)-1,i+2)])
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
def patch(name, controls, widths, material, c, region, side='CENTER', rows=24, cols=7, camber=.004, lobes=True):
    # A real broad u/v surface: lateral camber + subtle longitudinal ridges, not a swept tube.
    vs=[];fs=[]; old=Vector((1,0,0))
    for i in range(rows):
        t=i/(rows-1);p=cubic(controls,t);p0=cubic(controls,max(0,t-.015));p1=cubic(controls,min(1,t+.015));tan=(p1-p0).normalized()
        across=Vector((1,0,0))-tan*tan.x
        if across.length<.1:across=Vector((0,1,0))-tan*tan.y
        across.normalize()
        if across.dot(old)<0:across=-across
        old=across; normal=tan.cross(across).normalized(); w=widths[0]*(1-t)+widths[-1]*t
        for j in range(cols):
            q=j/(cols-1)*2-1; ridge=.0010*math.cos(q*math.pi*2)*(math.sin(t*math.pi)**1.5)
            # only final segment breaks into uneven lobes, while the rest remains one continuous parent.
            split=(.010*(t-.72)/.28*math.sin((q+1)*4.7) if lobes and t>.72 else 0)
            vs.append(p+across*(q*w+split)+normal*(camber*(1-q*q)+ridge))
    for i in range(rows-1):
        for j in range(cols-1):fs.append((i*cols+j,(i+1)*cols+j,(i+1)*cols+j+1,i*cols+j+1))
    return make_mesh(name,vs,fs,material,c,region,side)
def foundation(c,m):
    # Closed rear/side horseshoe volume; open front preserves the face and hides patch gaps.
    vs=[];fs=[]; rings=20; seg=28
    for i in range(rings):
        t=i/(rings-1);z=1.700-.410*t;rx=.118+.045*math.sin(math.pi*t);back=.145+.027*math.sin(math.pi*t)
        for j in range(seg):
            a=math.radians(-35+250*j/(seg-1)); y=.005+back*math.sin(a);x=rx*math.cos(a)
            vs.append((x,y,z))
    for i in range(rings-1):
        for j in range(seg-1):fs.append((i*seg+j,(i+1)*seg+j,(i+1)*seg+j+1,i*seg+j+1))
    # close side boundary and lower rim, creating a deliberately concealed shell.
    for i in range(rings-1):
        fs += [(i*seg,(i+1)*seg,(i+1)*seg+1,i*seg+1),(i*seg+seg-2,(i+1)*seg+seg-2,(i+1)*seg+seg-1,i*seg+seg-1)]
    o=make_mesh('Mia_Hair_Concealed_Horseshoe_Foundation',vs,fs,m,c,'SCALP_FOUNDATION');o['role']='HAIR_CONCEALED_FOUNDATION';o['stops_above_outer_tips']=True;return o
def knot(c,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=.040, location=(0,.153,1.615));o=move(bpy.context.object,c);o.name='Mia_Hair_Compact_HalfUp_Knot';o.scale=(1.12,.82,.74);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);tag(o,'HALF_UP_KNOT');o['role']='HAIR_CLOSED_BUNDLE_MASS';smooth(o)
def braid_tube(name,phase,c,m):
    # The only tubes: the three explicitly interwoven braid strands.
    pts=[]
    for i in range(42):
        t=i/41;pts.append(Vector((.104+.038*t+.006*math.sin(6*math.pi*t+phase),-.008-.142*t,1.603-.380*t)))
    vs=[];fs=[];rings=7
    for i,p in enumerate(pts):
        tan=(pts[min(i+1,41)]-pts[max(i-1,0)]).normalized();a=tan.cross(Vector((0,1,0)))
        if a.length<.1:a=Vector((1,0,0))
        a.normalize();n=tan.cross(a).normalized();r=.009*(1-t*.55) if (t:=i/41)<.92 else .004
        for j in range(rings):vs.append(p+a*math.cos(j*2*math.pi/rings)*r+n*math.sin(j*2*math.pi/rings)*r*.72)
    for i in range(41):
        for j in range(rings):fs.append((i*rings+j,i*rings+(j+1)%rings,(i+1)*rings+(j+1)%rings,(i+1)*rings+j))
    o=make_mesh(name,vs,fs,m,c,'LEFT_BRAID','LEFT','temple patch');o['role']='HAIR_BRAID_STRAND';return o
def aim(o,p,t):o.location=p;o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def add_review(c):
    for n,p,e in [('Key',(.5,-.7,2),35),('Fill',(-.5,-.5,1.8),12),('Rim',(0,.65,1.9),20)]:
        d=bpy.data.lights.new('HairMass_'+n,'AREA');d.energy=e;d.shape='DISK';d.size=.7;aim(move(bpy.data.objects.new('HairMass_'+n,d),c),p,(0,0,1.49))
    d=bpy.data.cameras.new('HairMassReviewCamera');d.type='ORTHO';return move(bpy.data.objects.new('HairMassReviewCamera',d),c)
def bounds(objs):
    p=[o.matrix_world@v.co for o in objs if o.type=='MESH' for v in o.data.vertices];return tuple(min(x[i] for x in p) for i in range(3)),tuple(max(x[i] for x in p) for i in range(3))
def main():
    a=args();src=Path(a.input);assert sha(src)==EXPECTED,'frozen anatomy sha mismatch';bpy.ops.wm.open_mainfile(filepath=str(src));assert sha(src)==EXPECTED
    assert not bpy.data.collections.get('MIA_HAIR_MASS_V01_OWNED'),'reject prior mass-stage input'
    f=bpy.data.objects.get('Mia_Face_AnimeTopology');b=bpy.data.objects.get('Mia_Body_Anatomy_Skin');assert f and b
    canon=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('Mia_Face_AnimeTopology') or o.name.startswith('Mia_Body_Anatomy_Skin') or o.get('role') in ('FACE_ANIME_TOPOLOGY','BODY_ANATOMY_SKIN'))]
    assert len(canon)==2 and {o.name for o in canon}=={f.name,b.name},[o.name for o in canon]
    assert sum(len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0 for o in canon)==42,'expected 42 source keys including Basis'
    before={o.name:fingerprint(o) for o in canon};c=coll('MIA_HAIR_MASS_V01_OWNED');dark=mat('Mia_HairMass_Neutral_Charcoal',(.026,.024,.030));ash=mat('Mia_HairMass_Neutral_Ash',(.055,.050,.060))
    foundation(c,dark)
    # Crown dome sectors: overlapping part-to-fringe and part-to-knot flows.
    crown=[(-.090,-.018),(-.062,-.010),(-.034,-.006),(-.008,-.003),(.020,-.003),(.048,-.010),(.077,-.018)]
    for i,(x,y) in enumerate(crown):
        patch('Mia_Hair_Crown_Fringeflow_%02d'%i,[(x*.22,y,1.735),(x*.60,y-.040,1.718),(x,y-.090,1.680),(x*1.12,y-.115,1.627)], [.036,.016],dark,c,'CROWN_TO_FRINGE','LEFT' if x>0 else 'RIGHT',camber=.004)
        patch('Mia_Hair_Crown_Knotflow_%02d'%i,[(x*.20,.005,1.733),(x*.70,.060,1.710),(x,.125,1.672),(x*.45,.157,1.625)], [.033,.014],ash if i in (1,5) else dark,c,'CROWN_TO_KNOT','LEFT' if x>0 else 'RIGHT',camber=.004)
    # Low asymmetric fringe, sunk into the crown overlaps; eye apertures remain intentionally open.
    fringe=[(-.082,1.594,.029),(-.049,1.574,.032),(-.018,1.557,.027),(.020,1.575,.031),(.056,1.595,.029)]
    for i,(x,z,w) in enumerate(fringe):patch('Mia_Hair_Brow_Forelock_%02d'%i,[(x*.42,-.080,1.692),(x,-.130,1.655),(x*.82,-.157,z)], [w,.008],ash if i==2 else dark,c,'BROW_FRINGE','LEFT' if x>0 else 'RIGHT',rows=22,cols=6,camber=.003,lobes=False)
    # Broad nested side/rear sheets, shortest over longest; the profile remains a connected outer mass.
    for side,label in ((1,'LEFT'),(-1,'RIGHT')):
        for i in range(4):
            end=1.245+.052*(i%2);x=.115+.014*i
            patch('Mia_Hair_%s_LongRear_%02d'%(label,i),[(side*.070,.065,1.700),(side*x,.105,1.630),(side*(x+.025),.105,1.510),(side*(x-.003),.065,end)], [.040,.013],dark,c,'SIDE_REAR_LONG',label,camber=.005)
        for i in range(3):
            x=.118+.014*i;patch('Mia_Hair_%s_ShortOverlay_%02d'%(label,i),[(side*.075,-.010,1.695),(side*x,-.058,1.615),(side*(x+.018),-.080,1.490),(side*(x-.003),-.055,1.372-.018*i)], [.034,.010],ash if i==1 else dark,c,'TEMPLE_SHORT_OVERLAY',label,camber=.005)
    for i,x in enumerate((-.10,-.055,0,.052,.098)):
        patch('Mia_Hair_Rear_CenterLayer_%02d'%i,[(x*.5,.130,1.690),(x,.185,1.600),(x*1.15,.160,1.470),(x*1.05,.125,1.275+.025*(i%2))],[.038,.011],ash if i==2 else dark,c,'REAR_LOOSE_LAYER','CENTER',camber=.005)
    knot(c,dark)
    for i,s in enumerate((-1,1,-1,1,0)):
        patch('Mia_Hair_Knot_Wrap_%02d'%i,[(s*.070,.122,1.665),(s*.047,.180,1.646),(s*.012,.192,1.615),(s*.025,.174,1.585)],[.014,.006],ash if i==1 else dark,c,'KNOT_WRAP','CENTER',rows=14,cols=5,camber=.002,lobes=False)
    for i,p in enumerate((0,2.094,4.189),1):braid_tube('Mia_Hair_Left_Braid_Strand_%02d'%i,p,c,dark)
    # Keep the authored envelope inside the specified 40cm width without changing source anatomy.
    for o in c.objects:
        if o.type=='MESH':
            for v in o.data.vertices:v.co.x*=.970
    # Optional rigid head preview ownership only; no secondary rig claim.
    arm=bpy.data.objects.get('Armature')
    if arm and arm.pose and arm.pose.bones.get('J_Bip_C_Head'):
        for o in c.objects:
            if o.type=='MESH':g=o.vertex_groups.new(name='J_Bip_C_Head');g.add(range(len(o.data.vertices)),1,'REPLACE');o['initial_binding']='head weight preview only; secondary rig unverified'
    after={o.name:fingerprint(o) for o in canon};assert before==after,'canonical geometry/UV/keys mutated'
    hb=bounds(list(c.objects));assert hb[0][0]>=-.20 and hb[1][0]<=.20 and hb[0][1]>=-.22 and hb[1][1]<=.23 and hb[0][2]>=1.16 and hb[1][2]<=1.80,hb
    ROOT.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=a.output);assert sha(src)==EXPECTED
    rc=coll('MIA_HAIR_MASS_REVIEW');cam=add_review(rc);sc=bpy.context.scene;sc.camera=cam;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=sc.render.resolution_y=768;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';Path(a.output_dir).mkdir(parents=True,exist_ok=True)
    views={'front':(0,-1,.72),'left_profile':(1,0,.72),'right_profile':(-1,0,.72),'back':(0,1,.72),'left_3q':(.72,-.72,.72),'right_3q':(-.72,-.72,.72),'full_front':(0,-2,2.0),'full_back':(0,2,2.0)};renders=[]
    for n,(x,y,s) in views.items():cam.data.ortho_scale=s;aim(cam,(x,y,1.49),(0,.01,1.49));sc.render.filepath=str(Path(a.output_dir)/(n+'.png'));bpy.ops.render.render(write_still=True);renders.append(sc.render.filepath)
    Path(a.report).write_text(json.dumps({'input_sha256':EXPECTED,'input_unchanged':sha(src)==EXPECTED,'canonical_objects':[o.name for o in canon],'canonical_fingerprints_before':before,'canonical_fingerprints_after':after,'canonical_unchanged':before==after,'hair_bounds':hb,'collection':c.name,'regions':['scalp','crown','fringe','rear','side','knot','braid'],'braid_assemblies':1,'braid_strands':3,'materials':2,'renders':renders,'status':'prototype rendered; artistic review pending'},indent=2))
if __name__=='__main__':main()
