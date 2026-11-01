"""Analytical contact sheet; display-only SRT, no retouch or feature-height fit."""
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'references/received/mia-face-reaffirmed-20261031.png'
BASE=Path(__file__).resolve().parents[1]/'integrated-review-wip-8/candidate/face/front.png'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--output',required=True);ap.add_argument('--label',default='Working candidate');a=ap.parse_args()
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    records=[('Concept',SOURCE,[(450,324),(582,310)],(518,412),(520,463)),('WIP8 baseline',BASE,[(383,539),(614,513)],(522,688),(525,765)),(a.label,Path(a.candidate),[(383,539),(614,513)],None,None)]
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    canvas=Image.new('RGB',(1500,1050),'#20242b');draw=ImageDraw.Draw(canvas)
    draw.text((30,25),'Face proportions - eye-spacing calibration only',font=font,fill='white')
    report={'method':'Display-only SRT: translate pupil midpoint, de-roll pupil line, uniform scale by pupil distance; no face warp or eye-to-chin fit.','limits':['Manual landmarks are approximate, not ground truth.','Concept/model pose, perspective and hidden hair boundary remain uncertain.','Candidate pupils inherited only for a jaw-only pass; update after eye change.'],'images':[]}
    scale=210.;left=-1.1;top=-.55;width=462;height=750
    for i,(label,path,eyes,mouth,chin) in enumerate(records):
        pic=Image.open(path).convert('RGB');cx=sum(e[0] for e in eyes)/2;cy=sum(e[1] for e in eyes)/2
        dx=eyes[1][0]-eyes[0][0];dy=eyes[1][1]-eyes[0][1];ipd=math.hypot(dx,dy);ang=math.atan2(dy,dx);c=math.cos(ang);s=math.sin(ang)
        # Inverse mapping of calibrated display coordinates into original pixels.
        coeff=(ipd*c/scale,-ipd*s/scale,cx+ipd*(c*left-s*top),ipd*s/scale,ipd*c/scale,cy+ipd*(s*left+c*top))
        panel=pic.transform((width,height),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC,fillcolor='#20242b')
        x0=27+i*492;y0=115;canvas.paste(panel,(x0,y0));draw.text((x0,78),label,font=font,fill='white')
        for value in [0,.4,.8,1.,1.2]:
            y=round(y0+(value-top)*scale);draw.line((x0,y,x0+width,y),fill='#619095',width=1);draw.text((x0+4,y+3),str(value),font=small,fill='#64dddd')
        for value in [-.5,.5]:
            x=round(x0+(value-left)*scale);y=round(y0-top*scale);draw.ellipse((x-3,y-3,x+3,y+3),fill='#64dddd')
        rec={'label':label,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'manual_pupils_px':eyes,'pupil_distance_px':ipd}
        if mouth:
            m=(-s*(mouth[0]-cx)+c*(mouth[1]-cy))/ipd;ch=(-s*(chin[0]-cx)+c*(chin[1]-cy))/ipd
            rec.update(approx_eye_to_chin_over_ipd=ch,approx_mouth_to_chin_over_ipd=ch-m)
        report['images'].append(rec)
    draw.text((30,900),'Unretouched source and actual Blender renders; uniform scale, translation and roll only.',font=small,fill='#cbd6e3')
    draw.text((30,930),'Cyan numbers: distance below pupil line / pupil spacing. Manual anchors are approximate.',font=small,fill='#cbd6e3')
    draw.text((30,960),'Jaw height is deliberately NOT fitted. This is a diagnostic, not an art-acceptance score.',font=small,fill='#cbd6e3')
    canvas.save(out);out.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if __name__=='__main__':main()
