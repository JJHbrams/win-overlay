"""Original-aspect source context and actual before/current shader diagnostics.

Reuses root's frozen v06 registration. v22 is a separately labelled grooming
authority at uniform whole-height display scale, not a substituted body target.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT=ROOT/'.mia-cache/face-live/curved-rear03/target-diagnostic'
spec=importlib.util.spec_from_file_location('mia_existing_boards',ROOT/'tools/mia/review_h/gray_boards.py')
boards=importlib.util.module_from_spec(spec);spec.loader.exec_module(boards)
base=json.loads((ROOT/'.mia-cache/body-h/ratio-baseline/capture.json').read_text())
master=ROOT/'asset/mia/references/mia-clean-master-v22.png'
records=[]
for view in ['back','profile']:
    before=next(r for r in base['frames'] if r['name']==view)
    after=json.loads((OUT/(view+'.json')).read_text())
    a=np.array(before['fixture']['camera_matrix']);b=np.array(after['fixture']['camera_matrix'])
    delta=float(abs(a-b).max());assert delta<2e-6,(view,delta)
    for key in ('ortho_scale','resolution','pixel_aspect','shift','frame','pose_sha256','lights','world','color_management'):
        assert before['fixture'][key]==after['fixture'][key],(view,key)
    matrix,reg=boards.registration(before,view)
    main=boards.source_panel(boards.SOURCES[0],view)
    # The master plate's source proportions differ. Only one disclosed scalar
    # and translation fit its whole figure to this display height; no local warp.
    axis,crop=(835,(700,0,1000,660)) if view=='back' else (580,(470,0,705,660))
    scale=879/629;translation=np.array([250-axis*scale,45.])
    original=Image.open(master).convert('RGB')
    isolated=Image.new('RGB',original.size,(225,234,240));isolated.paste(original.crop(crop),crop[:2])
    master_tile=isolated.transform((500,1024),Image.Transform.AFFINE,
                    (1/scale,0,-translation[0]/scale,0,1/scale,-translation[1]/scale),
                    Image.Resampling.BICUBIC,fillcolor=(225,234,240))
    tiles=[boards.label(master_tile,'MASTER v22 / uniform height only'),
           boards.label(main,'BODY v06 / original source pixels'),
           boards.label(boards.actual(before,matrix),'R3b hair + D body / actual'),
           boards.label(boards.actual(after,matrix),'Working03 / TEMP material / actual')]
    board=Image.new('RGB',(2000,1104),(230,236,240))
    for i,tile in enumerate(tiles):board.paste(tile,(i*500,0))
    ImageDraw.Draw(board).text((12,1072),'WIP only. v22 is grooming authority; v06 is body target. Source aspects preserved. New-lock pigment is temporary; no ART acceptance.',
                              fill=(25,35,45),font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18))
    path=OUT/('source-'+view+'.png');assert not path.exists();board.save(path)
    records.append(dict(view=view,board=str(path),board_sha256=boards.sha(path),
                        baseline=before,candidate=after,camera_matrix_max_abs_delta=delta,
                        matrix_delta_note='Sub-microradian float decomposition residue, below0.001 output pixel. Actual matrices retained, not silently relabelled exact.',
                        v06_render_registration=reg,v22_display=dict(uniform_scale=scale,translation_xy=translation.tolist(),
                         crop=list(crop),normalization_basis='Whole figure display height only; not independent proportion verification or a shared body-design target.'),
                        source_art_unchanged=True,ART=False))
(OUT/'source-board-records.json').write_text(json.dumps(dict(scope='Preliminary two-view source context, not complete required source4 gate',
                    records=records,required_remaining=['front','oblique','target material prototype','part/body contacts'],ART=False),indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(boards=[r['board'] for r in records],ART=False)))
