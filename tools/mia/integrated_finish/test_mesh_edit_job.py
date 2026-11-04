"""Data-job binding tests; no production assets or Blender mutation."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile,unittest
import numpy as np

spec=importlib.util.spec_from_file_location('mia_mesh_job',Path(__file__).with_name('mesh_edit_job.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class JobTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.cache=self.root/'.mia-cache';self.cache.mkdir()
        (self.cache/'selection.png').write_bytes(b'actual selection fixture')
        (self.root/'source.png').write_bytes(b'source art fixture')
        payload=self.cache/'delta.npz'
        np.savez(payload,candidate=np.zeros((4,3),np.float32),faces=np.array([[0,1,2]],np.int32),
            editable_ids=np.array([0],np.int32),transition_ids=np.array([],np.int32),fixed=np.array([1,2,3],np.int32))
        self.job=dict(schema=1,object_name='fixture',expected_before_sha256='a'*64,
            expected_topology_sha256='b'*64,payload=str(payload),payload_sha256=m.sha(payload),
            protected_regions={'retained_body':'fixed'},anatomical_declaration={'editable':'arm','transition':'none','basis':'test'},
            selection_evidence=[dict(role=role,path=str(path),sha256=m.sha(path)) for role,path in [
                ('actual_selection',self.cache/'selection.png'),('source_art',self.root/'source.png')]])
        self.path=self.cache/'job.json'
    def save(self):
        self.path.write_text(json.dumps(self.job),encoding='utf8');return m.sha(self.path)
    def test_loads_data_without_executing_geometry(self):
        digest=self.save();root,kwargs=m.load_apply_job(self.root,self.path,digest)
        self.assertEqual(root,self.root.resolve());self.assertEqual(kwargs['object_name'],'fixture')
        np.testing.assert_array_equal(kwargs['protected_regions']['retained_body'],[1,2,3])
    def test_changed_job_payload_and_selection_rejected(self):
        digest=self.save();self.path.write_text('{}',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'job changed'):m.load_apply_job(self.root,self.path,digest)
        digest=self.save();(self.cache/'delta.npz').write_bytes(b'stale')
        with self.assertRaisesRegex(ValueError,'arrays changed'):m.load_apply_job(self.root,self.path,digest)
        self.job['payload_sha256']=m.sha(self.cache/'delta.npz');digest=self.save()
        (self.cache/'selection.png').write_bytes(b'changed selection')
        with self.assertRaisesRegex(ValueError,'evidence'):m.load_apply_job(self.root,self.path,digest)
    def test_external_jobs_and_arbitrary_job_fields_rejected(self):
        digest=self.save();outside=self.root/'job.json';outside.write_bytes(self.path.read_bytes())
        with self.assertRaisesRegex(ValueError,'cache'):m.load_apply_job(self.root,outside,digest)
        self.job['code']='unexpected arbitrary Python';digest=self.save()
        with self.assertRaisesRegex(ValueError,'schema'):m.load_apply_job(self.root,self.path,digest)
    def test_missing_source_role_rejected(self):
        self.job['selection_evidence'][1]['role']='another_selection';digest=self.save()
        with self.assertRaisesRegex(ValueError,'Both actual selection'):m.load_apply_job(self.root,self.path,digest)

if __name__=='__main__':unittest.main()
