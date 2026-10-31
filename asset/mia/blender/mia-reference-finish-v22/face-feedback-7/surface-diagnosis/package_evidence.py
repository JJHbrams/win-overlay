"""Package existing renders only: discrete yaw GIFs and portable provenance audit."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
H=Path(__file__).resolve().parent
def artifact(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
records=json.loads((H/'render-records.json').read_text())
checks=[]
for item in records['records']:
    p=H/Path(item['render']['path']).name
    assert artifact(p)['sha256']==item['render']['sha256'],p
    checks.append(artifact(p))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
yaws=list(range(-90,91,15))+list(range(75,-90,-15))
for el,name in [(-10,'low'),(0,'level'),(10,'high')]:
    frames=[]
    for yaw in yaws:
        im=Image.open(H/('matte_yaw%+03d_elev%+03d.png'%(yaw,el))).convert('RGBA')
        tile=Image.new('RGBA',im.size,(205,205,205,255));tile.alpha_composite(im)
        fr=Image.new('RGB',(700,742),(236,236,236));fr.paste(tile.convert('RGB'),(0,42))
        d=ImageDraw.Draw(fr);d.text((10,3),'Face6 matte | yaw %+d | elevation %+d | discrete 15-degree samples'%(yaw,el),font=font,fill='black')
        frames.append(fr.quantize(colors=128))
    frames[0].save(H/('yaw-ping-pong-'+name+'.gif'),save_all=True,append_images=frames[1:],duration=320,loop=0,disposal=2)
original=Path(records['source']['path']);archived=H.parents[1]/'parts/face-finish6/native/f5d17264e07f-Mia_FaceFinish6_v22.blend'
assert artifact(original)['sha256']==records['source']['sha256']==artifact(archived)['sha256']
deps=[]
producer=original.parents[2]/'finish-4/replay'
for name in ['review_setup.py','shape_evidence.py']:
    frozen=H/'dependencies'/name;old=producer/name
    assert artifact(frozen)['sha256']==artifact(old)['sha256']
    deps.append({'frozen':artifact(frozen),'original':artifact(old),'byte_identical':True})
manifest={'source_original':artifact(original),'source_canonical_archive':artifact(archived),'source_unchanged':True,'historical_executed_recipe':artifact(H/'inspect_continuous_surface.executed.py'),'portable_recipe':artifact(H/'inspect_continuous_surface.py'),'dependencies':deps,'portable_validation':'Blender 5.2.3 --validate-only succeeded; canonical archive and frozen helper hashes checked, no native opened or new render produced. Rendering logic unchanged from historical recipe; only CLI/path handling and overwrite guard added.','fresh_render_count':len(checks),'fresh_render_hashes_unchanged':True,'fresh_render_metadata':artifact(H/'render-records.json'),'artifacts':[artifact(p) for p in sorted(H.iterdir()) if p.suffix in ['.png','.gif','.md','.py']],'limitations':'GIFs are discrete actual orthographic render samples with palette quantization, no interpolation or geometry animation. Lossless original PNGs/contact sheets remain primary. This is surface diagnosis, not ART PASS.'}
(H/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2))
print('PACKAGED',len(checks),'unchanged render hashes; native hashes unchanged')
