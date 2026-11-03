"""CPU trace of actual recorded material-preflight defect pixels; no image edits."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from surface_api import load_surface, read_json, write_json, sha
from pattern_fields import seat, make_recipe
from bake_surface import paint_fields
from verify_surface_maps import bilinear

P=Path(__file__).resolve().parent
records=Path(sys.argv[1])
maps=Path(sys.argv[2]) if len(sys.argv)>2 else P/'maps-E'
surface=load_surface(P/'inputs/e8d4d505e661.npz')
row=next(r for r in read_json(records) if r['job']['name']=='clavicle-on')
assert row['geometry']['surface_file_sha256']==surface['input_sha256']
f=row['fixture']
camera=dict(projection=f['projection'],matrix=f['camera_matrix'],view_frame_local=f['view_frame_camera_local'],
            resolution=f['resolution'],clip_start=f['clip'][0],clip_end=f['clip'][1])
pixels=np.array([[166,644],[215,696],[640,696],[599,742],[107,785],[400,780],[195,450],[195,470]],float)
origins,directions,maximum=seat.pixel_rays(camera,pixels)
ids=np.arange(len(surface['triangles']))
caster=seat.SurfaceCaster(surface,cast_triangle_ids=ids)
hits=[caster.first_hit(o,d,maximum,allowed_triangle_ids=ids,min_facing_cos=.025,uv_seam_tolerance=2.) for o,d in zip(origins,directions)]
if not all(h['accepted'] for h in hits):raise ValueError(hits)
uv=np.array([h['uv'] for h in hits]);world=np.array([h['world'] for h in hits]);regions=np.array([surface['face_region'][h['triangle_id']] for h in hits])
config=read_json(maps/'authoring-config.json');curves,_,_=make_recipe(config)
clav=read_json(maps/'seated-boundaries.json')['clavicles'];straps=read_json(maps/'seated-straps.json')['straps']
expected,_=paint_fields(dict(valid=np.ones((len(hits),1),bool),world=world[:,None,:],region=regions[:,None]),config,curves,clav,straps)
coverage=bilinear(np.array(Image.open(maps/'UnderwearCoverage.png')),uv)
actual=np.array(Image.open(records.parent/'clavicle-on.png'))
samples=[]
for i,h in enumerate(hits):
 samples.append(dict(pixel=pixels[i].tolist(),actual_RGB_u8=actual[int(pixels[i,1]),int(pixels[i,0]),:3].tolist(),
                     body_triangle=h['triangle_id'],meshfaceid=int(surface['meshfaceid'][h['triangle_id']]),region=int(regions[i]),
                     world=world[i].tolist(),UV=uv[i].tolist(),analytic_fixed_world_coverage=float(expected['UnderwearCoverage'][i,0]),
                     final_PNG_bilinear_coverage=float(coverage[i])))
report=dict(surface_sha256=surface['input_sha256'],actual_records=str(records),actual_records_sha256=sha(records),
            actual_image_sha256=sha(records.parent/'clavicle-on.png'),samples=samples,
            sampled_map_dir=str(maps.resolve()),sampled_coverage_sha256=sha(maps/'UnderwearCoverage.png'),
            limit='Actual RGB belongs to the recorded baseline material10 image; candidate PNG coverage is CPU prediction until actual recapture.',
            GPU_used=False,geometry_or_images_changed=False)
write_json(P/(maps.name+'-actual-pixel-diagnosis.json'),report)
print(report)
