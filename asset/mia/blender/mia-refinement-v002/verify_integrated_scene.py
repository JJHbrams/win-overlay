"""Fresh reopen verification of saved component data and neutral runtime defaults."""
from pathlib import Path
import argparse, hashlib, json, sys
import bpy
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import scene_fingerprint as sfp
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
native=Path(a.native).resolve();meta=json.loads(native.with_suffix('.integration.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(native)==meta['native_sha256']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);s=bpy.context.scene;s.frame_set(2);s.frame_set(1);bpy.context.view_layer.update()
assert meta['fingerprint_version']==sfp.FINGERPRINT_VERSION
assert meta['fingerprint_helper_sha256']==sha(Path(sfp.__file__))
actual=sfp.snapshot_scene();expected=meta['final_owners'];errors=[]
if set(expected)!=set(actual['objects']):errors.append('Saved scene object inventory differs')
for name in sorted(set(expected)&set(actual['objects'])):
    old,now=expected[name],actual['objects'][name]
    for field in sorted(set(old)|set(now)):
        if old.get(field)!=now.get(field):errors.append(name+': saved '+field+' differs')
if meta['final_scene']!=actual['scene']:errors.append('Saved scene envelope differs')
checked=sorted(set(expected)&set(actual['objects']))
c=bpy.data.objects['Mia_FacialControls_v002'];neutral={n:c[n] for n in c.keys() if (n.startswith('P') and n[:3][1:].isdigit()) or n.startswith('Manual') or n in ['HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY']};assert all(v==0 for v in neutral.values())
invalid=[]
for block in list(bpy.data.objects)+list(bpy.data.shape_keys):
    ad=block.animation_data
    if not ad:continue
    for f in ad.drivers:
        if ('v002' in block.name.lower() or 'Mia.Gaze' in f.data_path or 'MIA_ToothyGrin' in f.data_path or any(t.id==c for v in f.driver.variables for t in v.targets)) and not f.driver.is_valid:invalid.append((block.name,f.data_path))
new_images=[]
for im in bpy.data.images:
    if im.name.startswith(('MIA_V002','MIA_v002')):
        row=dict(name=im.name,size=list(im.size),space=im.colorspace_settings.name,source=im.source,packed=bool(im.packed_file),packed_sha256=hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None)
        new_images.append(row)
        if im.source=='FILE' and not im.packed_file:errors.append(im.name+': new external-only image')
active=[dict(name=o.name,watts=o.data.energy) for o in s.objects if o.type=='LIGHT' and not o.hide_render]
assert len(active)==3 and all(x['name'].startswith('Mia_v002_SourceLight_') for x in active)
assert not invalid,invalid
report=dict(native=str(native),sha256=sha(native),checked_owners=len(checked),errors=errors,invalid_drivers=invalid,neutral_controls=neutral,new_images=new_images,active_lights=active,
    scene_saved=False,technical_preservation_pass=not errors,art_approved=False,scope='Fresh saved arrays/UVs/weights/material assignments/transforms/neutral controls and packed new maps. Actual per-view art/deformation remains separate.')
Path(a.out).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert not errors,errors[:20]
assert sha(native)==meta['native_sha256'];print('V002_FRESH_REOPEN_DATA_OK',len(checked),len(new_images),flush=True)
