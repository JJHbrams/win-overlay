"""Encode actual Blender PNGs with a common palette; no synthesized views."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();out=Path(a.output)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',23);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
settings={'head':('얼굴 · 헤어 360°',60),'bare':('헤어를 가린 얼굴 · 두상 360°',80),'body':('현재 전신 모델 360°',80)}
results=[]
for preset,(title,duration) in settings.items():
    folder=out/preset;meta=json.loads((folder/'manifest.json').read_text());frames=[]
    for r in meta['frames']:
        src=Image.open(folder/r['path']).convert('RGBA');bg=Image.new('RGBA',src.size,'#e6ebf1');bg.alpha_composite(src)
        frame=Image.new('RGB',(720,932),'#f5f7f9');frame.paste(bg.convert('RGB'),(0,52));draw=ImageDraw.Draw(frame)
        draw.text((18,10),title,font=font,fill='#172633');draw.text((18,903),f"정투영 · yaw {r['yaw']:05.1f}° · 현재 모델 e9c86541",font=small,fill='#344452');frames.append(frame)
    samples=Image.new('RGB',(360*6,466*2))
    for j in range(12):samples.paste(frames[j*len(frames)//12].resize((360,466)),((j%6)*360,(j//6)*466))
    palette=samples.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    quantized=[f.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    durations=[duration+250 if i%(len(frames)//4)==0 else duration for i in range(len(frames))]
    path=out/f'mia-v27-{preset}-360.gif';quantized[0].save(path,save_all=True,append_images=quantized[1:],loop=0,duration=durations,optimize=False,disposal=2)
    samples.save(out/f'{preset}-12views.png')
    with Image.open(path) as check:
        count=check.n_frames;total=sum(check.seek(i) or check.info.get('duration',0) for i in range(count))
        assert count==len(frames)
    results.append({'path':path.name,'frames':count,'duration_ms':total,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_native_sha256':meta['sha256']})
(out/'gif-manifest.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))
