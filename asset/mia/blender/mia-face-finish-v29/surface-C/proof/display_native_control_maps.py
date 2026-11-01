"""Native read-only display copies of baked numeric EXRs, not new maps."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).parent;O=P/'native-control-maps-v02';scene=bpy.context.scene;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';records=[]
for name in ['V29_FeatureControls_RGB','V29_LightReflectControls_RGB']:
 path=O/(name+'.exr');before=hashlib.sha256(path.read_bytes()).hexdigest();im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';out=O/(name+'-DISPLAY.png');im.save_render(str(out),scene=scene);assert hashlib.sha256(path.read_bytes()).hexdigest()==before;records.append({'source':str(path.resolve()),'source_sha256':before,'native_float_depth':im.depth,'display_copy':str(out.resolve()),'display_note':'Native save_render display encoding of unchanged baked numeric channels. PNG is for inspection only; EXR remains the consumed scalar/control asset.'})
(O/'display-manifest.json').write_text(json.dumps(records,indent=2));print('NATIVE_CONTROL_DISPLAYS_READY')
