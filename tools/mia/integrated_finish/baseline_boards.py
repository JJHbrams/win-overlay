"""Source pixels plus current actual full-height views, one frozen uniform SRT."""
from pathlib import Path
import importlib.util,json
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.mia-cache/body-h/live/integrated01'
spec=importlib.util.spec_from_file_location('existing_mia_boards',ROOT/'tools/mia/review_h/gray_boards.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
hair=json.loads((OUT/'baseline/capture.json').read_text())
gray=json.loads((ROOT/'.mia-cache/body-h/live/integrated01-gray/after-v2/capture.json').read_text())
hrows={r['name']:r for r in hair['frames']};grows={r['name']:r for r in gray['frames']}
records=[]
for name in ('front','profile','back','oblique'):
    h,g=hrows[name],grows[name]
    for key in ('projection','camera_matrix','resolution','pixel_aspect','shift','clip','world','color_management'):
        assert h['fixture'][key]==g['fixture'][key],(name,key)
    # Gray capture borrows copied light objects, so their names differ. The
    # illumination-defining matrices, energy and size must still match exactly.
    light_values=lambda f: sorted([dict(matrix=x['matrix'],energy=x['energy'],size=x['size']) for x in f['lights']],key=lambda x:json.dumps(x,sort_keys=True))
    assert light_values(h['fixture'])==light_values(g['fixture']),name
    matrix,reg=b.registration(h,name)
    tiles=[b.label(b.source_panel(b.SOURCES[0],name),'BODY v06 / original pixels'),
           b.label(b.source_panel(b.SOURCES[1],name),'Visibility / pose uncertainty'),
           b.label(b.actual(g,matrix),'CURRENT695 / actual gray'),
           b.label(b.actual(h,matrix),'CURRENT integrated / actual')]
    canvas=Image.new('RGB',(2000,1100),(230,236,240))
    for i,t in enumerate(tiles):canvas.paste(t,(i*500,0))
    ImageDraw.Draw(canvas).text((10,1072),'Frozen whole-height uniform SRT. Crown/sole normalization is not an independently verified height. Source pose differs.',
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18),fill=(30,40,50))
    path=OUT/('source-'+name+'.png');assert not path.exists();canvas.save(path)
    records.append(dict(name=name,source=[b.art(p) for p in b.SOURCES],
        source_crop=b.PANELS[name][1],current_gray=g,current_hair=h,registration=reg,
        board=b.art(path),pose_limit='Nominal0/90/180/30, source drawing pose and artistic asymmetry not calibrated cameras.',
        geometry_limit='Standalone currentbody has0keys/0mods; gray private scene lacks old hidden rig but exact same world coordinates.'))
(OUT/'baseline-source-records.json').write_text(json.dumps(dict(records=records,ART=False,
    scope='Baseline diagnosis only; no candidate and no source-likeness approval'),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(source_boards=4,uniform_SRT=True,ART=False)))
