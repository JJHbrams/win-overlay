"""Eight read-only actual Blender renders, using frozen source review cameras."""
import argparse,ast,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parent
V22=ROOT.parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--source',required=True)
ap.add_argument('--candidate',required=True)
ap.add_argument('--output-dir',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=Path(a.output_dir).resolve()
assert not OUT.exists(),str(OUT)
OUT.mkdir(parents=True)
names={'render_visible','keys','hair_hide','material','aim','setup','camera_and_lights','record','routes','production_uv'}
rig=V22/'render_integrated_review.py'
tree=ast.parse(rig.read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(rig),'exec'))
package=V22/'parts/face-finish8-f2-review/reference-review.json'
data=json.loads(package.read_text(encoding='utf-8-sig'))
views={v['id']:v['baseline_camera'] for v in data['views']}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source={r:Path(p).resolve() for r,p in [('baseline',a.source),('candidate',a.candidate)]}
initial_hashes={r:sha(p) for r,p in source.items()}
records={}
for role,path in source.items():
    s,lamps=setup(path,'face')
    folder=OUT/role
    folder.mkdir()
    for mode in ['lit','color_only']:
        if mode=='color_only':
            hair_hide()
            for sl in bpy.data.objects['MIA_V14_SculptedSkin'].material_slots:
                if not sl.material or not sl.material.use_nodes:
                    continue
                m=sl.material.copy()
                sl.material=m
                n=m.node_tree.nodes
                mul=n.get('PigmentTimesControlledLight')
                if mul and mul.inputs[1].is_linked:
                    em=next((x for x in n if x.type=='EMISSION'),None)
                    if em:
                        m.node_tree.links.new(mul.inputs[1].links[0].from_socket,em.inputs[0])
        for view in ['front','left_oblique']:
            camera_and_lights(s,lamps,views[view],'face')
            p=(folder/(mode+'-'+view+'.png')).resolve()
            s.render.filepath=str(p)
            bpy.ops.render.render(write_still=True)
            records[role+'/'+mode+'/'+view]={'render':str(p),'sha256':sha(p),'camera':record(s,lamps),'mode':mode,'hair_hidden':mode=='color_only','skin_color_only':mode=='color_only'}
            (OUT/'render-records.json').write_text(json.dumps(records,indent=2))
for mode in ['lit','color_only']:
    for view in ['front','left_oblique']:
        assert records['baseline/'+mode+'/'+view]['camera']==records['candidate/'+mode+'/'+view]['camera']
assert initial_hashes=={r:sha(p) for r,p in source.items()}
(OUT/'manifest.json').write_text(json.dumps({'sources':{r:{'path':str(p),'sha256':initial_hashes[r]} for r,p in source.items()},'face_package':{'path':str(package),'sha256':sha(package)},'same_conditions':True,'native_saved':False,'color_only_caveat':'Skin pigment bypasses controlled light; hair is hidden. Other eye and accessory materials keep their native shader.','art_status':'NOT_EVALUATED'},indent=2))
print('COMBINED_MATERIAL_REVIEW_DONE')
