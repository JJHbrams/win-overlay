"""Actual NPZ meridian intersections and tangent/face-normal variation."""
from pathlib import Path
import json,hashlib,sys,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;B=D.parent;sys.path.insert(0,str(B));import field
p=json.loads((B/'parameters.json').read_text(encoding='utf-8'));data=np.load(B/'sculpt07-C.npz');v=data['world'].astype(float);tri=data['triangles'];x=p['breast']['center_x'];parts=v[tri];delta=parts[:,:,0]-x;selected=np.flatnonzero((delta.min(1)<0)&(delta.max(1)>0));segments=[];faceids=[];nodes={};connect=[]
normal=np.cross(parts[:,1]-parts[:,0],parts[:,2]-parts[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
for fi in selected:
    face=parts[fi];ids=tri[fi];pts=[];ends=[]
    for a,b in [(0,1),(1,2),(2,0)]:
        if (face[a,0]-x)*(face[b,0]-x)<0:
            q=face[a]+(face[b]-face[a])*((x-face[a,0])/(face[b,0]-face[a,0]));key=tuple(sorted((int(ids[a]),int(ids[b]))));pts.append(q);ends.append(key);nodes[key]=q
    if len(pts)==2:segments.append(pts);faceids.append(fi);connect.append(ends)
segments=np.array(segments);faceids=np.array(faceids);degree={key:0 for key in nodes}
for a,b in connect:degree[a]+=1;degree[b]+=1
neighbors={key:[] for key in nodes}
for a,b in connect:neighbors[a].append(b);neighbors[b].append(a)
unvisited=set(nodes);loops=0
while unvisited:
    loops+=1;stack=[unvisited.pop()]
    while stack:
        for other in neighbors[stack.pop()]:
            if other in unvisited:unvisited.remove(other);stack.append(other)
rows=[]
for z in np.arange(1.12,1.360001,.001):
    ok=(segments[:,:,2].min(1)<=z)&(segments[:,:,2].max(1)>=z);ss=segments[ok];ii=faceids[ok]
    if not len(ss):continue
    dz=ss[:,1,2]-ss[:,0,2];keep=abs(dz)>1e-12;ss=ss[keep];ii=ii[keep];dz=dz[keep]
    ys=ss[:,0,1]+(ss[:,1,1]-ss[:,0,1])*((z-ss[:,0,2])/dz);j=int(ys.argmin());dy=ss[j,1,1]-ss[j,0,1];tangent_deg=math.degrees(math.atan2(dy/dz[j],1.));nyz=normal[ii[j],1:];nyz/=np.linalg.norm(nyz)
    rows.append(dict(z=float(z),front_y=float(ys[j]),triangle=int(ii[j]),tangent_degrees_from_vertical=tangent_deg,projected_outward_normal_yz=nyz.tolist(),normal_angle_degrees=math.degrees(math.atan2(nyz[1],-nyz[0]))))
angles=np.array([r['tangent_degrees_from_vertical'] for r in rows]);zs=np.array([r['z'] for r in rows]);ys=np.array([r['front_y'] for r in rows]);jumps=np.abs(np.diff(angles));region=(zs>=1.16)&(zs<=1.24);regional=[r for r in rows if 1.16<=r['z']<=1.24]
f,reg=field.make(p);points=np.array([[x,r['front_y'],r['z']] for r in rows]);regvals={k:field.evaluate(q,points) for k,q in reg.items()}
for j,r in enumerate(rows):r['nearest_positive_primitive']=min(regvals,key=lambda k:regvals[k][j])
report=dict(C_mesh_sha256=hashlib.sha256((B/'sculpt07-C.npz').read_bytes()).hexdigest(),plane_x=x,actual_intersection_segments=len(segments),intersection_nodes=len(nodes),intersection_connected_loops=loops,intersection_nodes_degree_not_two=sum(value!=2 for value in degree.values()),samples=rows,underbust_1mm_triangle_tangent_step_max_degrees=float(jumps[(zs[:-1]>=1.16)&(zs[:-1]<=1.24)].max()),underbust_front_y_range=[float(ys[region].min()),float(ys[region].max())],status='Actual triangle contour and projected geometric normals, not assumed analytic smoothness or shader normals.',limits='1mm sampling traverses a~3mm voxel triangle mesh. Triangle normal/tangent steps include tessellation; C1 analytic field does not imply constant curvature. Rays select anterior minimumY on exactX plane; no global cross-section/collision proof.')
(D/'actual-meridian-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);im=Image.new('RGB',(1100,650),'#202632');draw=ImageDraw.Draw(im)
draw.text((14,10),'ACTUAL C mesh: X=%.4fm anterior meridian / no geometry change'%x,font=font,fill='white')
left=(50,70,510,590);right=(610,70,1050,590)
def yplot(z):return 590-(z-1.12)/.24*520
def contour(y):return 50+(y+.17)/.12*460
def angle(a):return 610+(a+90)/180*440
for z in np.arange(1.12,1.361,.02):
    yy=yplot(z);draw.line((50,yy,1050,yy),fill='#414957');draw.text((9,yy-8),'%.2f'%z,font=small,fill='#b5c7d9')
for b in p['source_consumed_before_geometry']['section_support_bands']:
    yy=yplot(b['world_z']);draw.line((50,yy,1050,yy),fill='#687b5d')
draw.line([(contour(r['front_y']),yplot(r['z'])) for r in rows],fill='#6df6c6',width=3);draw.line([(angle(r['tangent_degrees_from_vertical']),yplot(r['z'])) for r in rows],fill='#efbb67',width=3)
for z in [1.18,1.195,1.205,1.22,1.24]:
    r=min(rows,key=lambda q:abs(q['z']-z));draw.text((615,yplot(z)-9),'%.3f: %.1fdeg'%(r['z'],r['tangent_degrees_from_vertical']),font=small,fill='white')
draw.text((50,612),'Y front depth: -170..-50mm (left→right)',font=small,fill='white');draw.text((610,612),'Tangent from vertical: -90..+90 degrees',font=small,fill='white');im.save(D/'actual-meridian-contour-tangent.png')
print('ACTUAL_MERIDIAN_AUDIT',json.dumps({k:v for k,v in report.items() if k!='samples'}),flush=True)
