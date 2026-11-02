"""Contact sheets of actual immutable PNGs; layout only, no image correction."""
from pathlib import Path
import argparse,hashlib,json,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--tag',required=True);a=ap.parse_args()
R=P/'review'/a.tag;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
for suite,cols,width in [('orbit',6,256),('critical',4,320),('intermediates',4,320)]:
    file=R/suite/'render-records.json'
    if not file.exists():continue
    rows=json.loads(file.read_text());h=width+25
    board=Image.new('RGB',(cols*width,math.ceil(len(rows)/cols)*h),(237,242,246));d=ImageDraw.Draw(board)
    for i,row in enumerate(rows):
        assert sha(row['path'])==row['sha256']
        im=Image.open(row['path']).convert('RGB');assert im.width==im.height
        x,y=(i%cols)*width,(i//cols)*h
        board.paste(im.resize((width,width),Image.Resampling.LANCZOS),(x,y+25))
        d.text((x+4,y+4),row['id'],font=font,fill=(24,38,49))
    out=R/(suite+'-actual-contact.png');assert not out.exists();board.save(out)
    print('ACTUAL_CONTACT_SHEET',suite,len(rows),out)
