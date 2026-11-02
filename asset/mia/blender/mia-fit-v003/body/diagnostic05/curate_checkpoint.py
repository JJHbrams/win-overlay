"""Hash a small02–05/diagnostic checkpoint without changing historical01 files."""
from pathlib import Path
import ast,hashlib,json
O=Path(__file__).resolve().parent;P=O.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
top=['analyze_posed_sections.py','audit_crease_sharp_readonly.py','audit_patch_02_contact.py','audit_patch_04_contact.py','audit_patch_05_contact.py','audit_posed_control_topology.py','audit_private_normals_05.py','audit_source_support_04.py','audit_source_support_05.py','build_lowview_source_constraints.py','compose_patch_02.py','compose_source_lowviews_05.py','fit_posed_target_02.py','fit_posed_target_03.py','fit_source_bound_target_04.py','fit_source_bound_target_05.py','install_posed_target_02.py','install_posed_target_03.py','install_posed_target_04.py','install_posed_target_05.py','install_source_bound_guides_05.py','private_geometric_normals.py','render_posed_target_02.py','render_posed_target_03.py','render_source_bound_target_05.py','verify_posed_target_02.py','verify_posed_target_03.py','verify_posed_target_04.py','verify_posed_target_05.py']
files={P/f for f in top}
for name in ['target-02.npz','target-03.npz','target-04.npz','target-05.npz','control-topology.npz','private-normal-audit-05.json','crease-sharp-readonly.json','source-pose-mismatch-readonly.json','contact-orientation-02.json','contact-04.json','contact-05.json','actual01-02-comparisons.json','actual01-02-front.png','actual01-02-lowoblique.png']:
    files.add(P/'posed-target'/name)
for number in ['02','03','04','05']:
    for prefix in ['construction','fresh-guard','topology-audit']:
        files.add(P/'posed-target'/(prefix+'-'+number+'.json'))
for number in ['01','02','04','05']:
    files.add(P/'posed-target'/('evaluated-sections-'+number+'.png'))
    files.add(P/'posed-target'/('section-analysis-'+number+'.json'))
for folder in [P/'source-binding',P/'posed-target/actual-02',P/'posed-target/actual-05',O]:
    for f in folder.rglob('*'):
        if not f.is_file() or '__pycache__' in f.parts:continue
        if f.suffix not in ['.py','.md','.json','.png']:continue
        if f.name in ['checkpoint-02-05-files.json']:continue
        files.add(f)
for f in files:
    assert f.is_file(),str(f)
    assert f.suffix!='.blend' and 'evaluated-0' not in f.name
    if f.suffix=='.py':ast.parse(f.read_text(encoding='utf-8-sig'),filename=str(f))
completion=json.loads((O/'actual-four/completion.json').read_text())
assert completion['frames']==4 and completion['original_objects_exact']==620
guard=json.loads((O/'cpu-guard.json').read_text());assert guard['private_state_restore_bitexact']
assert guard['metadata']['target_sha256']==sha(P/'posed-target/target-05.npz')
for folder in [P/'posed-target/actual-02',P/'posed-target/actual-05',O/'actual-four']:
    records=json.loads((folder/'render-records.json').read_text())
    for row in records:
        file=folder/Path(row['path']).name
        assert file.is_file() and sha(file)==row['sha256'],str(file)
source=P/'source-binding/constraints.json'
can=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
dependencies=[dict(role='exact selected current native; read only',path=str(can/'blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'),sha256=guard['native_sha256']),
    dict(role='explicit upperbody/axilla reference; original aspect',path=str(can/'references/received/mia-low-view-axilla-reaffirmed-20261103.png'),sha256='31fa0da05c970e9b6d84a2569953b48636bd8d32df33d65901772f5664ad52b2'),
    dict(role='frozen historical01 checkpoint dependencies and runtime',commit='a9f385e72d3a9dfa49e07d945761e81676e1e969',manifest='checkpoint-files.json',dependencies='checkpoint-dependencies.json'),
    dict(role='local actualArmature inverse mapping',path='inputs/mapping-frame1.npz',sha256=sha(P/'inputs/mapping-frame1.npz'))]
manifest=[dict(path=f.relative_to(P).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(files)]
payload=dict(status='02/03/04/05 rejected; diagnostic only. R3b remains selected. No anatomy/garment/rig approval.',historical01_manifest_untouched=True,
    included='Frozen small target fields, producers/reproduction, selected actual failures, source binding and normals/pose/operator diagnostics.',
    excluded='All full natives/captions, pycache/log spam, new evaluated surface caches and repeated historical variants.',
    dependencies=dependencies,files=manifest,total_bytes=sum(row['bytes'] for row in manifest),source_constraints_sha256=sha(source))
(O/'checkpoint-02-05-files.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
repo=P.parents[4]
paths=[str(f.relative_to(repo)).replace('\\','/') for f in sorted(files|{O/'checkpoint-02-05-files.json'})]
(O/'checkpoint-pathspec.nul').write_bytes(('\0'.join(paths)+'\0').encode('utf-8'))
print('CURATED_02_05_DIAGNOSTIC',len(paths),payload['total_bytes'],flush=True)
