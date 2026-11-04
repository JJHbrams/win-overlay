"""Data-only bridge from the supported MCP route to the scoped mesh guard.

No arbitrary expressions or imported candidate scripts in a job. This is a
workflow guard, not a sandbox for the user's full bpy-capable MCP server.
"""
from pathlib import Path
import hashlib,json,runpy
import numpy as np

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()

def cached(root,value):
    path=(root/Path(value)).resolve()
    if not path.is_relative_to((root/'.mia-cache').resolve()):
        raise ValueError('Edit job and array payload must stay in the current project cache')
    if not path.is_file():raise ValueError('Missing scoped edit input: '+str(path))
    return path

def load_apply_job(root,job_path,expected_job_sha256):
    root=Path(root).resolve();path=cached(root,job_path)
    if sha(path)!=expected_job_sha256:raise ValueError('Scoped edit job changed after dispatch')
    job=json.loads(path.read_text(encoding='utf8'))
    required={'schema','object_name','expected_before_sha256','expected_topology_sha256',
              'payload','payload_sha256','protected_regions','anatomical_declaration','selection_evidence'}
    if set(job)!=required or job['schema']!=1:raise ValueError('Unsupported scoped edit job schema')
    evidence=job['selection_evidence']
    if not isinstance(evidence,list) or len(evidence)<2:
        raise ValueError('Actual selection and corresponding source evidence are required')
    roles=set()
    for item in evidence:
        if set(item)!={'role','path','sha256'}:raise ValueError('Malformed selection evidence')
        image=(root/Path(item['path'])).resolve()
        if not image.is_relative_to(root) or not image.is_file() or sha(image)!=item['sha256']:
            raise ValueError('Selection/source evidence missing, outside project, or stale')
        roles.add(item['role'])
    if not {'actual_selection','source_art'}<=roles:
        raise ValueError('Both actual selection and source art roles are required')
    payload=cached(root,job['payload'])
    if sha(payload)!=job['payload_sha256']:raise ValueError('Scoped edit arrays changed after review')
    if payload.stat().st_size>64*1024**2:raise ValueError('Unexpected large scoped delta payload')
    with np.load(payload,allow_pickle=False) as arrays:
        kwargs={key:arrays[key].copy() for key in ('candidate','faces','editable_ids','transition_ids')}
        protected=job['protected_regions']
        if not isinstance(protected,dict) or not protected:raise ValueError('Named protected regions required')
        kwargs['protected_regions']={name:arrays[key].copy() for name,key in protected.items()}
    kwargs.update({key:job[key] for key in ('object_name','expected_before_sha256',
        'expected_topology_sha256','anatomical_declaration')})
    return root,kwargs

def execute(root,job_path,expected_job_sha256):
    root,kwargs=load_apply_job(root,job_path,expected_job_sha256)
    guard=runpy.run_path(str(root/'tools/mia/integrated_finish/scoped_mesh_edit.py'))
    return guard['apply'](root=root,**kwargs)
