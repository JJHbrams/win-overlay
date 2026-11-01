"""Prepare only declared frozen owners for static Finish8 REVIEW integration."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
V22=HERE.parent
config=json.loads((HERE/'adapter-smoke-inputs.json').read_text(encoding='utf-8-sig'))
for role,folder in [('face','face-finish8-f2-review'),('body','body23n-work'),('hair','hair24-painted-work')]:
    directory=V22/'parts'/folder
    package=directory/'reference-review.json'
    data=json.loads(package.read_text(encoding='utf-8-sig'))
    row=data['candidate_native']
    native=Path(row['path'])
    config[role].update(path=str((native if native.is_absolute() else directory/native).resolve()),
                        sha256=row['sha256'],review_package=str(package))
config['body']['provenance']=str(V22/'parts/body23n-work/supplements/patch-provenance-v23n.json')
hair=json.loads((V22/'parts/hair24-painted-work/supplements/handoff.json').read_text(encoding='utf-8-sig'))
for key in ('new_owners','replace_mesh_owners','hidden_retained_owners'):
    config['hair'][key]=hair[key]
config['hair']['material_owners']=[n for n in config['hair']['material_owners'] if n not in hair['hidden_retained_owners']]+hair['new_owners']
config['output_dir']=str(V22/'integration-wip-8-review')
config['status']='REVIEW ONLY / ART UNAPPROVED. F2 central cheek restoration, existing face pigment, body23n bounded thorax and hair24 local rear curl. High cheek band, complete source likeness, main hair extraction and body shape/UV remain open.'
out=HERE/'integration-inputs.json'
assert not out.exists(), 'Frozen configuration exists'
out.write_text(json.dumps(config,indent=2),encoding='utf-8')
print(out)
