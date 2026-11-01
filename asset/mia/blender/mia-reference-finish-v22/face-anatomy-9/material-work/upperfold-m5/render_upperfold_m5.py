"""Actual material comparison: lit/color-only source views and half/full blink."""
import argparse,ast,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent;V22=ROOT.parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--output-dir',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir).resolve();assert not OUT.exists();OUT.mkdir(parents=True)
names={'render_visible','keys','hair_hide','material','aim','setup','camera_and_lights','record','routes','production_uv'}
rig=V22/'render_integrated_review.py';tree=ast.parse(rig.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(rig),'exec'))
package=V22/'parts/face-finish8-f2-review/reference-review.json';data=json.loads(package.read_text(encoding='utf-8-sig'));views={v['id']:v['baseline_camera'] for v in data['views']}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sources={'baseline':Path(a.source).resolve(),'candidate':Path(a.candidate).resolve()};hashes={r:sha(p) for r,p in sources.items()};records={}
def save(role,name,s,lamps,mode,blink):
    p=(OUT/role/(name+'.png')).resolve();s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    records[role+'/'+name]={'render':str(p),'sha256':sha(p),'camera':record(s,lamps),'mode':mode,'blink':blink}
    (OUT/'render-records.json').write_text(json.dumps(records,indent=2))
for role,path in sources.items():
    (OUT/role).mkdir();s,lamps=setup(path,'face')
    for view in ['front','left_oblique']:
        camera_and_lights(s,lamps,views[view],'face');save(role,'lit-'+view,s,lamps,'lit',0)
    hair_hide();skin=bpy.data.objects['MIA_V14_SculptedSkin'];close=next(k for k in skin.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'))
    camera_and_lights(s,lamps,views['front'],'face')
    for state,value in [('halfblink',.5),('fullblink',1)]:
        close.value=value;skin.data.shape_keys.update_tag();bpy.context.view_layer.update();save(role,state,s,lamps,'lit-hair-hidden',value)
    close.value=0;skin.data.shape_keys.update_tag();bpy.context.view_layer.update()
    for sl in skin.material_slots:
        if not sl.material or not sl.material.use_nodes:continue
        m=sl.material.copy();sl.material=m;n=m.node_tree.nodes;mul=n.get('PigmentTimesControlledLight')
        if mul and mul.inputs[1].is_linked:
            em=next((x for x in n if x.type=='EMISSION'),None)
            if em:m.node_tree.links.new(mul.inputs[1].links[0].from_socket,em.inputs[0])
    for view in ['front','left_oblique']:
        camera_and_lights(s,lamps,views[view],'face');save(role,'color_only-'+view,s,lamps,'skin-color-only-hair-hidden',0)
for name in ['lit-front','lit-left_oblique','color_only-front','color_only-left_oblique','halfblink','fullblink']:
    assert records['baseline/'+name]['camera']==records['candidate/'+name]['camera']
assert hashes=={r:sha(p) for r,p in sources.items()}
(OUT/'manifest.json').write_text(json.dumps({'sources':{r:{'path':str(p),'sha256':hashes[r]} for r,p in sources.items()},'face_package':{'path':str(package),'sha256':sha(package)},'same_conditions':True,'native_saved':False,'color_only_caveat':'Skin light bypassed; hair hidden. Other eye/accessory shaders native.','limits':['Neutral front/left oblique and front half/fullblink only. Not all facial keys or combinations.','No ART PASS.']},indent=2));print('M5_RENDER_DONE')
