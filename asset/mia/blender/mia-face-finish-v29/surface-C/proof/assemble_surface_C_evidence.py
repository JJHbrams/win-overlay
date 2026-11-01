"""Boards and correspondence checks from actual frozen C probe images."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,math
P=Path(__file__).parent;O=P/'surface-C';N=O/'Mia_FaceSurface_v29_C.blend';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();native_sha=sha(N)
def art(p):return {'path':str(p.resolve()),'sha256':sha(p)}
allrecords={};metrics={};verified=0
for preset in ['first','features','response','map-controls','blink','headfollow']:
 folder=O/('probes-'+preset+'-hair-off');data=json.loads((folder/'probe-records.json').read_text());assert data['native_sha256']==native_sha;allrecords[preset]=data['records'];metrics[preset]=json.loads((folder/'actual-linear-response-deltas.json').read_text())
 for name,r in data['records'].items():
  assert sha(r['path'])==r['sha256'];assert sha(r['actual_linear_render_result']['path'])==r['actual_linear_render_result']['sha256'];verified+=1
def board(name,preset,keys,cols,size=384):
 rows=math.ceil(len(keys)/cols);out=Image.new('RGB',(cols*size,rows*(size+36)+28),(32,32,32));d=ImageDraw.Draw(out)
 for i,key in enumerate(keys):
  r=allrecords[preset][key];im=Image.open(r['path']).convert('RGBA');bg=Image.new('RGBA',im.size,(32,32,32,255));bg.alpha_composite(im);tile=bg.convert('RGB').resize((size,size),Image.Resampling.LANCZOS);x=(i%cols)*size;y=(i//cols)*(size+36);d.text((x+8,y+8),key,font=font,fill='white');out.paste(tile,(x,y+36))
 d.text((8,rows*(size+36)+5),'Actual saved-native C probes; display scaling uniform; other owners retain production shaders.',font=font,fill='white');path=O/(name+'.png');out.save(path);return art(path)
boards={}
boards['production_and_pigment']=board('paired-production-and-pigment','first',['before_color','after_color','before_production','after_production'],2,512)
boards['feature_gain_pairs']=board('individual-feature-gains','features',['fatigue_0.0','fold_0.0','makeup_0.0','fatigue_1.0','fold_1.0','makeup_1.0'],3)
boards['actual_light_reflection']=board('actual-light-reflection-probes','response',['diffuse_original','diffuse_control','diffuse_moved','spec_flat0','spec_flat1','spec_moved','rough_low','rough_high'],4)
boards['native_vs_flat_maps']=board('native-vs-flat-reflection-controls','map-controls',['native_spec_and_roughness','flat_spec_native_roughness','native_spec_flat_roughness','flat_spec_and_roughness'],2,512)
boards['closure']=board('surface-closure-probes','blink',['Close_0.5','Close_R_0.5','Close_L_0.5','Close_1.0','Close_R_1.0','Close_L_1.0'],3)
boards['headfollow']=board('surface-headfollow-probes','headfollow',['head_-12.0_front','head_12.0_front','head_-12.0_left_oblique','head_12.0_left_oblique'],2,512)
checks=[]
for preset,data in metrics.items():
 for pair in data['comparisons']:
  pair['preset']=preset;pair['nonzero_actual_response']=pair['rms_linear_RGB']>1e-7 and pair['pixels_with_delta_above1e-8']>100;checks.append(pair)
driver_checks=[]
for name,r in allrecords['blink'].items():
 values=next(iter(r['actual_material_values'].values()));active=r['active_keys']['MIA_V27_SharedHeadBody'];v=.5 if name.endswith('0.5') else 1.;right=1-v if name.startswith(('Close_','Close_R_')) else 1.;left=1-v if name.startswith(('Close_','Close_L_')) else 1.
 # 'Close_' is also a prefix of unilateral names, so derive exact side label.
 side=name.rsplit('_',1)[0];right=1-v if side in ['Close','Close_R'] else 1.;left=1-v if side in ['Close','Close_L'] else 1.;assert abs(values['V29_FoldOpen_R']-right)<1e-6 and abs(values['V29_FoldOpen_L']-left)<1e-6
 driver_checks.append({'probe':name,'actual_fold_open_R':values['V29_FoldOpen_R'],'actual_fold_open_L':values['V29_FoldOpen_L'],'actual_keys':active})
report={'native':art(N),'verified_png_and_linear_pairs':verified,'boards':boards,'linear_response_checks':checks,'all_expected_actual_response_nonzero':all(c['nonzero_actual_response'] for c in checks),'actual_blink_fold_driver_checks':driver_checks,'preservation':art(O/'surface-candidate-guard.json'),'source_art_actual_size':[1254,1254],'native_numeric_maps_size':[2048,2048],'resolution_note':'Generated B art remains1254-square sRGB;2048 native control bakes do not add imagegen paint detail.','status':'Actual probe correspondence/response checks only; independent local surface/style/source review and final integrated-native approval remain separate'}
(O/'surface-probe-evidence.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('SURFACE_C_EVIDENCE',verified,'actualframes','responses_nonzero',report['all_expected_actual_response_nonzero'],flush=True)
