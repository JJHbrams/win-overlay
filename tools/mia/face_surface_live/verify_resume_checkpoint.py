"""Read-only fresh Blender verification of the one retained WIP copy."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parents[3]


def verify(root=ROOT):
    import bpy
    root = Path(root).resolve()
    folder = root/'.mia-cache/production-resume-20261104'
    expected = json.loads((folder/'checkpoint.json').read_text(encoding='utf8'))
    helper = runpy.run_path(str(root/'tools/mia/face_surface_live/lock_look01.py'),
        init_globals={'MIA_LOCK_LOOK01_LIBRARY_ONLY':True})
    assert Path(bpy.data.filepath).resolve()==Path(expected['path']).resolve()
    assert helper['file_sha'](expected['path'])==expected['sha256']
    mismatches=[]
    for name,row in expected['objects'].items():
        ob=bpy.data.objects[name]
        actual=dict(fingerprint=helper['fingerprint'](ob),hide_render=bool(ob.hide_render),
            hidden=bool(ob.hide_get()),materials=[(s.link,s.material.name if s.material else None) for s in ob.material_slots])
        # JSON represents tuples as lists; compare semantic values, not Python types.
        if json.loads(json.dumps(actual))!=row:mismatches.append(name)
    assert not mismatches, mismatches
    ma=bpy.data.materials['MIA_v003_CurrentRemainingMain_StaticPigment_WIP']
    images={n.image.name:dict(size=list(n.image.size),colorspace=n.image.colorspace_settings.name,
        packed=[__import__('hashlib').sha256(p.packed_file.data).hexdigest() for p in n.image.packed_files])
        for n in ma.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    assert images==expected['pigment_images']
    assert len(bpy.data.objects['MIA_Hair_CurvedRear03Base_RemainingMain'].data.uv_layers)==7
    report=dict(status='FRESH_REOPEN_MATCHES_SAVED_RETAINED_WIP',path=expected['path'],
        sha256=expected['sha256'],objects_verified=len(expected['objects']),
        geometry_topology_UV_corner_normals_material_slots_visibility_exact=True,
        connected_pigment_images_size_space_packed_bytes_exact=True,
        render_verified=False,ART=False,native_saved=False)
    (folder/'fresh-reopen.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__': verify()
