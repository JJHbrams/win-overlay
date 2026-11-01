"""Authoritative H diagnosis: observed ocular-to-lid boundary, no invented source anatomy."""
import json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).parent;pkg=json.loads((O/'reference-review-G2.json').read_text());proj=json.loads((O/'upper-H-G2-projections.json').read_text())
tr={
 'front':{
  'image_left':{'upper_visible':[[411,325],[424,322],[440,320],[456,320],[470,322]],'lower_visible':[[412,329],[424,337],[440,340],[458,337],[470,332]],'unknown_medial_xyxy':[470,318,485,333]},
  'image_right':{'upper_visible':[[547,312],[562,306],[582,302],[602,300],[615,300]],'lower_visible':[[548,319],[563,321],[582,321],[599,317],[611,309]],'unknown_medial_xyxy':[536,305,549,323]}},
 'left_oblique':{
  'image_right':{'upper_visible':[[1320.5,82.5],[1327,78.5],[1336,76.5],[1344,74.5]],'lower_visible':[[1323,88],[1331,87.5],[1340,84],[1346,78]],'unknown_medial_xyxy':[1314,80,1323,89]},
  'image_left':{'upper_visible':[[1276,101.5],[1284,99],[1292,97.5],[1295,98.5]],'lower_visible':[[1278,106],[1287,103],[1295,99.5]],'unknown_medial_xyxy':[1294,94,1301,101]}},
 'right_oblique':{
  'image_right':{'upper_visible':[[954,94],[963,88],[974,84.5],[981,83.5]],'lower_visible':[[959,98],[970,95.5],[980,91.5]],'unknown_medial_xyxy':[947,90,958,100]},
  'image_left':{'upper_visible':[[897,117],[907,112.5],[918,109],[925,107]],'lower_visible':[[903,119.5],[915,116],[923,111]],'unknown_medial_xyxy':[922,102,931,112]}},
 'profile':{'near':{'upper_visible':[[554,71.5],[558,69],[564,68],[569,67.5]],'lower_visible':[[555,75],[559,75],[564,72]],'unknown_medial_xyxy':[549,66,556,77]}}
}
data={'schema_version':1,'authority':'Latest user correction: ocular opening/free lid differs from decorative ink/lashes/brow/makeup. This supersedes anatomical endpoint inference in upper-H-source-traces.json.','native_unchanged':'Mia_Orbit_v28_G2.blend','native_edits_for_H':False,'source_policy':'Original source pixels unchanged. Cyan/yellow show only visible ocular-to-lid occlusion segments; magenta region is UNKNOWN covered margin/canthus. A black tail is not an anatomical endpoint. No inpainting, no source clean-lid synthesis.','uncertainty_original_px':{'front':1.5,'profile':1.5,'left_oblique':1.0,'right_oblique':1.0},'views':tr,'limits':'Opaque eyeliner can cover the true free margin. Traced ocular border is an observed occlusion contour, not proof of the hidden 3D lid margin or canthus. Need review clean G2 opening and separate ink, without using outer black edge as skin target.'}
(O/'upper-H-visible-opening-traces.json').write_text(json.dumps(data,indent=2))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
board=Image.new('RGB',(2400,1360),(237,242,246));dr=ImageDraw.Draw(board)
def fit(im,w,h):
 s=min(w/im.width,h/im.height);return im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.BICUBIC)
for ri,v in enumerate(pkg['views']):
 id=v['id'];y=ri*340;bb=v['reference']['crop_xyxy'];src=Image.open(v['reference']['path']).convert('RGB').crop(bb);ann=src.copy();ad=ImageDraw.Draw(ann)
 for eye,t in tr[id].items():
  for k,col in [('upper_visible',(0,255,255)),('lower_visible',(255,220,0))]:ad.line([(p[0]-bb[0],p[1]-bb[1]) for p in t[k]],fill=col,width=1)
  a=t['unknown_medial_xyxy'];ad.rectangle((a[0]-bb[0],a[1]-bb[1],a[2]-bb[0],a[3]-bb[1]),outline=(255,0,150),width=1)
 for x,im in [(0,src),(430,ann)]:board.paste(fit(im,420,275),(x,y+35))
 clean=Image.open(O/'upper-H-clean-G2'/(id+'-clean-lid.png')).convert('RGB');over=clean.copy();od=ImageDraw.Draw(over);ps=proj['views'][id]['skin'];qq=[]
 for side,p in ps.items():
  if id=='profile' and side=='-1':continue # Hidden far aperture must not be mistaken for a visible margin.
  for key,col in [('upper',(0,255,255)),('lower',(255,220,0))]:
   q=(np.array(p[key])-384)*(.29/.14)+384;qq.extend(q.tolist());od.line([tuple(a) for a in q],fill=col,width=1)
  for a in [p['upper'][0],p['upper'][-1]]:
   x,z=(np.array(a)-384)*(.29/.14)+384;od.ellipse((x-2,z-2,x+2,z+2),fill=(255,0,150))
 q=np.array(qq);crop=(max(0,int(q[:,0].min()-20)),max(0,int(q[:,1].min()-30)),min(768,int(q[:,0].max()+20)),min(768,int(q[:,1].max()+35)))
 board.paste(fit(clean.crop(crop),740,275),(870,y+35));board.paste(fit(over.crop(crop),740,275),(1630,y+35))
 dr.text((8,y+5),id+' SOURCE untouched',font=font,fill='black');dr.text((438,y+5),'VISIBLE ocular border / UNKNOWN magenta',font=font,fill='black');dr.text((878,y+5),'G2 clean-lid: ink/lash/brow/UV makeup OFF',font=font,fill='black');dr.text((1638,y+5),'G2 actual skin opening projection',font=font,fill='black')
 dr.text((10,y+312),'Source: covered canthus remains UNKNOWN. G2: shared lid seam is measured. Native camera axes retained; crop + uniform scale only, no chord alignment.',font=small,fill='black')
board.save(O/'upper-H-separated-source-G2-fourview.png')
print('H_STRICT_LAYER_SEPARATION_SAVED')
