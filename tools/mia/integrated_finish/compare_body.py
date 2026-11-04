"""Original-aspect source / actual baseline / actual candidate whole-height boards."""
from pathlib import Path
import argparse,importlib.util,json
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--capture',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('mia_existing_source_boards',ROOT/'tools/mia/review_h/gray_boards.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    base=json.loads((ROOT/'.mia-cache/body-h/live/integrated01-gray/after-v2/capture.json').read_text())
    candidate=json.loads(Path(args.capture).read_text())
    rows0={x['name']:x for x in base['frames']};rows1={x['name']:x for x in candidate['frames']}
    records=[]
    for name in ('front','profile','back','oblique','opposite','high','low'):
        old,new=rows0[name],rows1[name]
        for key in ('projection','camera_matrix','resolution','pixel_aspect','shift','clip','world','color_management'):
            assert old['fixture'][key]==new['fixture'][key],(name,key)
        lights=lambda f:sorted([dict(matrix=x['matrix'],energy=x['energy'],size=x['size']) for x in f['lights']],key=lambda x:json.dumps(x,sort_keys=True))
        assert lights(old['fixture'])==lights(new['fixture'])
        if name in b.PANELS:
            matrix,registration=b.registration(old,name)
            tiles=[b.label(b.source_panel(b.SOURCES[0],name),'BODY v06 / original pixels'),
                   b.label(b.source_panel(b.SOURCES[1],name),'Visibility / pose uncertainty'),
                   b.label(b.actual(old,matrix),'BEFORE695 / actual gray'),
                   b.label(b.actual(new,matrix),'ARM CHAIN01 / actual gray')]
            board=Image.new('RGB',(2000,1100),(230,236,240))
            for i,tile in enumerate(tiles):board.paste(tile,(500*i,0))
            note='Same frozen uniform SRT. Source pose uncertainty retained. Actual head and lower body unchanged.'
        else:
            registration=None
            images=[Image.open(row['path']).convert('RGB') for row in (old,new)]
            assert images[0].size==images[1].size
            width,height=images[0].size
            board=Image.new('RGB',(width*2,height+64),(230,236,240))
            for i,im in enumerate(images):board.paste(im,(width*i,32))
            note='BEFORE695 (left) / ARM CHAIN01 (right); continuity diagnostic, no matched source panel.'
        ImageDraw.Draw(board).text((10,board.height-27),note,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17),fill=(30,40,50))
        path=out/(name+'.png');board.save(path)
        records.append(dict(name=name,source=[b.art(p) for p in b.SOURCES] if registration else [],
            registration=registration,baseline=old,candidate=new,board=b.art(path),
            limit='Nominal drawing camera/pose estimates; no exact skeletal recovery. No ART conclusion from board generation.'))
    (out/'records.json').write_text(json.dumps(dict(records=records,baseline_sha256=base['world_sha256'],
        candidate_sha256=candidate['world_sha256'],ART=False),indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(boards=len(records),output=str(out),ART=False)))

if __name__=='__main__':main()
