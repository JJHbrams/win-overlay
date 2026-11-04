"""Encode the actual saved-WIP orbit; no interpolation or generated views."""
from pathlib import Path
import hashlib
import json
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3]


def main(root=ROOT):
    folder=Path(root)/'.mia-cache/production-resume-20261104'
    capture=json.loads((folder/'head-hair-orbit/capture.json').read_text())
    assert len(capture['frames'])==24
    frames=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
    for i,row in enumerate(capture['frames']):
        path=Path(row['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        assert row['yaw']==i*15 and row['fixture']['projection']=='ORTHO'
        assert row['fixture']['clip']==[.1,10.] or all(abs(a-b)<1e-7 for a,b in zip(row['fixture']['clip'],[.1,10.]))
        im=Image.open(path).convert('RGB')
        canvas=Image.new('RGB',(480,510),(32,34,36));canvas.paste(im,(0,30))
        ImageDraw.Draw(canvas).text((9,7),f'STATIC WIP | ORTHO | yaw {i*15:03d}',font=font,fill=(230,230,230))
        frames.append(canvas)
    output=folder/'head-hair-orbit.gif';assert not output.exists()
    frames[0].save(output,save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=False)
    with Image.open(output) as gif: assert gif.n_frames==24
    report=dict(path=str(output),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        bytes=output.stat().st_size,actual_rendered_frames=24,generated_interpolation_frames=0,
        source_native_sha256=capture['native_sha256'],camera='ORTHO0.1..10m,head/crown-centered',
        limits='Neutral camera orbit preview; long lower tips may be outside the head crop. Not final two-material FB64 or character motion/rig approval.',ART=False)
    (folder/'head-hair-orbit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__':main()
