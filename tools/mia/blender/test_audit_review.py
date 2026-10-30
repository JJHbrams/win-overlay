import json
import tempfile
import unittest
from pathlib import Path

from audit_review import ReviewError, load_review, review_summary, sha256


class AuditReviewTests(unittest.TestCase):
    def test_review_is_bound_to_exact_source_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.blend"
            source.write_bytes(b"first version")
            review = Path(directory) / "review.json"
            review.write_text(json.dumps({
                "source_sha256": sha256(source),
                "gates": {"geometry": "FAIL", "artistic": "UNVERIFIED"},
            }), encoding="utf-8")
            self.assertEqual(review_summary(load_review(review, sha256(source)))["geometry"], "FAIL")
            source.write_bytes(b"second version")
            with self.assertRaises(ReviewError):
                load_review(review, sha256(source))


if __name__ == "__main__":
    unittest.main()
