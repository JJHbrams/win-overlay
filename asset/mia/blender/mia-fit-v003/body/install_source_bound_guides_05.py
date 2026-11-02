"""Real source-bound upperbody curves, separate from fullbelowheadR4 scaffold."""
from pathlib import Path
import json,hashlib
import bpy,numpy as np
from field_math import cubic_z,periodic_theta
P=Path(__file__).resolve().parent;C=P/'source-binding';COLLECTION='MIA_v003_SourceBoundSupport_05'
def install():
    path=C/'source-3D-sections-05.json';sha=hashlib.sha256(path.read_bytes()).hexdigest();d=json.loads(path.read_text())
    if COLLECTION in bpy.data.collections:
        col=bpy.data.collections[COLLECTION];assert col['data_sha256']==sha;return col
    col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col);col['data_sha256']=sha;col['source_constraints_sha256']=d['constraints_sha256'];col['purpose']='Source-bound supported upperbody sections consumed by05surface; observed cloth tangents and inferred geometry distinguished. FullbelowheadR4 remains separate.'
    u=np.array(d['angles']);z=np.array([q['z'] for q in d['sections']]);rings=np.array([q['points'] for q in d['sections']]);uu=np.linspace(-np.pi,np.pi,257)[:-1]
    def add(name,points,closed,kind):
        data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=.0005;data.bevel_resolution=1;sp=data.splines.new('POLY');sp.points.add(len(points)-1)
        for p,q in zip(sp.points,points):p.co=(*q,1)
        sp.use_cyclic_u=closed;ob=bpy.data.objects.new(name,data);col.objects.link(ob);ob['kind']=kind;ob['guide_only']=True
    for i,row in enumerate(d['sections']):add(f'Source05.section.{i:02d}',periodic_theta(u,rings[i],uu),True,row['kind'])
    for j,t in enumerate(np.linspace(-1.4,1.4,15)):
        vals=np.asarray([periodic_theta(u,r,np.full(101,t)) for r in rings]);zz=np.linspace(z.min(),z.max(),101);add(f'Source05.meridian.{j:02d}',cubic_z(z,vals,zz),False,'inferred interpolation between source-bound sections')
    for sign in [-1,1]:
        src=json.loads((C/'constraints.json').read_text());pts=[[sign*b['inferred_x'],b['inferred_y'],b['world_z']] for b in src['anterior_fold_bands']];add(f'Source05.foldband.{sign}',pts,False,'inferred3D band from short observed skin/ink fragments; not posterior membrane')
    col.hide_render=True;bpy.context.view_layer.update();return col
