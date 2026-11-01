"""Diagnostic display of actual stored pixels/UV/graph, no asset repaint."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;d=json.loads((P/'active-surface-inventory.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
name='V28_ActualUV_OrbitPigment_2048_D';record=d['face_pigment_arrays'][name];px=np.load(P/record['pixel_array'])['pixels'];rgb=px[:,:,:3];srgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.maximum(rgb,0)**(1/2.4)-.055);encoded=(np.clip(srgb,0,1)*255+.5).astype('uint8');im=Image.fromarray(encoded[::-1]);im.save(P/'actual-packed-pigment-display.png')
uvdata=np.load(P/'actual-face-uv-and-mask.npz');uv=uvdata['uv_corners'];tris=uvdata['face_loop_triangles'];wire=im.copy();wd=ImageDraw.Draw(wire)
for tri in tris:
 pts=[(float(uv[i,0])*2048,(1-float(uv[i,1]))*2048) for i in tri];wd.line(pts+[pts[0]],fill=(60,100,125),width=1)
wire.save(P/'actual-packed-pigment-UVwire-display.png')
board=Image.new('RGB',(1550,860),(36,36,36));dr=ImageDraw.Draw(board)
for j,(tile,label) in enumerate([(im,'ACTUAL packed FaceUV2048 pigment'),(wire,'Same pixels + actual face-loop UV wire')]):
 board.paste(tile.resize((740,740),Image.Resampling.LANCZOS),(20+j*770,70));dr.text((20+j*770,15),label,font=font,fill='white')
dr.text((20,830),'Read-only display: scene-linear packed RGB encoded to sRGB for viewing. No native/image edited; this is not pure albedo.',font=small,fill='white');board.save(P/'actual-pigment-UV-thumbnail.png')

graph=Image.new('RGB',(1550,730),'white');gd=ImageDraw.Draw(graph);gd.text((20,15),'ACTUAL f0dead17 face: scene-lit toon diffuse, packed pigment, emission output',font=font,fill='black')
def box(x,y,w,h,title,lines,color=(225,235,242)):
 gd.rounded_rectangle((x,y,x+w,y+h),radius=10,fill=color,outline=(65,85,105),width=2);gd.text((x+12,y+12),title,font=font,fill='black')
 for i,line in enumerate(lines):gd.text((x+12,y+42+i*23),line,font=small,fill='black')
def arrow(a,b):
 gd.line([a,b],fill=(45,60,75),width=3);x,y=b;gd.polygon([(x,y),(x-10,y-6),(x-10,y+6)],fill=(45,60,75))
box(25,95,235,145,'UVMap', ['Actual CORNER UV','Face690 / slot0','InnerLidSkin also samples it'])
box(300,95,285,145,'Packed pigment2048', ['V28_ActualUV_OrbitPigment','_2048_D, float EXR','Non-Color = stored linear RGB'])
box(655,95,260,145,'MULTIPLY, factor1', ['Pigment × controlled light','No separate specular branch','No normal/bump map input'])
box(980,95,240,145,'Emission, strength1', ['Actual active output route','Display is not physical skin','No displacement linked'])
box(1270,95,245,145,'Active material output', ['V28_Orbit_ActualUV','1342 face polygons','Legacy maps not counted'])
for a,b in [((260,165),(300,165)),((585,165),(655,165)),((915,165),(980,165)),((1220,165),(1270,165))]:arrow(a,b)
box(25,330,235,145,'White Diffuse BSDF', ['Color1, roughness0','Normal implicit mesh normal','Actual scene lighting'])
box(300,330,285,145,'ShaderToRGB → BW ÷4', ['EEVEE active scene pathway','Not the old normal-dot fake','MIA_REVIEW area rig60/15/8'])
box(655,330,260,145,'CommonSkinLightRamp', ['EASE4-station warm ramp','0.025/.175/.55/.95','Feeds multiply above'])
arrow((260,402),(300,402));arrow((585,402),(655,402));gd.line([(785,330),(785,240)],fill=(45,60,75),width=3)
box(980,330,535,145,'Head / neck material continuity', ['Slots9/10 use V27_HeadMaterialBlend POINT attribute','Body-light branch ↔ uniform-head controlled-light group','Group uses same actual-light ramp and base(.82,.63,.55)'])
gd.text((25,520),'Needed plan decision: preserve this working light response; extend paint/shadow control and restrained spec only after lid/lash gate.',font=font,fill='black')
gd.text((25,565),'Current map is flattened pigment with fatigue / crease / fixed accents. Old BasePigment / FatigueMask / FineLineMask exist on archived owners.',font=small,fill='black')
gd.text((25,595),'They are not independent active layers on the current face, and no blanket PBR map set should be counted as already working.',font=small,fill='black')
gd.text((25,650),'Read-only schematic of actual traced links, not a proposed shader or a Blender render.',font=small,fill='black');graph.save(P/'actual-active-route-thumbnail.png')

xyz=uvdata['basis_world'];mask=uvdata['mask'];maskboard=Image.new('RGB',(1000,620),(245,245,245));md=ImageDraw.Draw(maskboard);md.text((20,10),'ACTUAL stored head/neck blend attribute on original Body prefix',font=font,fill='black')
for col,axes in enumerate([(0,2),(1,2)]):
 for i,v in enumerate(xyz):
  if i>=3957 or not 1.38<v[2]<1.66:continue
  x=col*500+250+(v[axes[0]]-(0 if col==0 else .025))*2200;y=575-(v[2]-1.38)*1800;m=float(mask[i]);color=(int(40+200*m),int(80+40*(1-m)),int(230-190*m));md.ellipse((x-3,y-3,x+3,y+3),fill=color)
 md.text((col*500+25,50),'Front basis projection' if col==0 else 'Profile basis projection',font=font,fill='black')
md.text((20,590),'Blue0 = body branch; red1 = uniform-head branch. Stored POINT attribute, not a world-Z shader cutoff.',font=small,fill='black');maskboard.save(P/'actual-head-neck-mask-thumbnail.png')
(P/'thumbnail-provenance.json').write_text(json.dumps({'source_image':name,'packed_sha256':record['image']['packed_sha256'],'pixel_hash':record['pixels_sha256'],'uv_method':'Actual Face690 slot0 triangulated loop-corner UVMap; only a wire overlay. Image native rows flip to top-down display.','display_transfer':'sRGB encode of actual stored linear RGB; no pigment edits','native_sha256':d['native_sha256'],'native_saved':False},indent=2),encoding='utf8');print('AUDIT_THUMBNAILS_READY')
