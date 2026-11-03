"""Original-aspect source/visibility/before/after, sharing the frozen global SRT."""
from pathlib import Path
import importlib.util,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'.mia-cache/body-connected/actual-gray'
spec=importlib.util.spec_from_file_location('common_gray_boards',ROOT/'tools/mia/review_h/gray_boards.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
capture=json.loads((OUT/'capture.json').read_text());rows={(r['state'],r['view']):r for r in capture['records']}
views=[]
for name in ['front','profile','back','oblique']:
 before,after=rows['before',name],rows['after',name]
 assert common.camera(before['fixture'])==common.camera(after['fixture'])
 matrix,registration=common.registration(after,name)
 tiles=[common.label(common.source_panel(common.SOURCES[0],name),'MAIN / original aspect'),
        common.label(common.source_panel(common.SOURCES[1],name),'VISIBILITY / uncertain pose'),
        common.label(common.actual(before,matrix),'R3b original cage / before'),
        common.label(common.actual(after,matrix),'Connected DESIGN / after / FAIL')]
 # Identical source-coordinate crop and identical uniform enlargement.
 detail=Image.new('RGB',(2000,540))
 for j,tile in enumerate(tiles):
  crop=tile.crop((100,205,400,505)).resize((500,500),Image.Resampling.LANCZOS)
  detail.paste(common.label(crop,['MAIN','VISIBILITY','R3b before','ONE broad proposal / FAIL'][j]),(j*500,0))
 path=OUT/('source-'+name+'.png');detail.save(path)
 views.append(dict(view=name,path=str(path),source=[common.art(p)for p in common.SOURCES],
     shared_model_registration=registration,reference_aspect_changed=False,
     source_camera_uncertainty='Nominal source front/profile/back/30degree; drawing cameras and pose are not calibrated CT',
     crop_source_coordinates=[100,205,400,505],uniform_enlargement=500/300,
     before=common.art(before['path']),after=common.art(after['path'])))
for name in ['high','low']:
 before,after=rows['before',name],rows['after',name]
 board=Image.new('RGB',(1440,760))
 for j,row in enumerate([before,after]):board.paste(common.label(Image.open(row['path']).convert('RGB'),row['state']+' / '+name),(720*j,0))
 board.save(OUT/('before-after-'+name+'.png'))
(OUT/'reference-review.json').write_text(json.dumps(dict(scope='ONE broad design trial rejected; source original aspect and shared SRT held',views=views,ART=False),indent=2)+'\n',encoding='utf8')
print('CONNECTED_ORIGINAL_ASPECT_BOARDS_READY_FAIL')
