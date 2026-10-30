#!/usr/bin/env python3
"""Version-bound manual review support for :mod:`audit_multiview`.

This module deliberately contains no Blender dependency, so a stale review can
be rejected before a render farm or an artist spends time inspecting it.
"""
import hashlib
import json
from pathlib import Path


class ReviewError(ValueError):
    """A manual review cannot be used as evidence for this source file."""


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_review(path, source_sha):
    review = json.loads(Path(path).read_text(encoding="utf-8"))
    bound = str(review.get("source_sha256", "")).upper()
    if bound != source_sha.upper():
        raise ReviewError(
            "manual review source_sha256 does not match the audited source "
            "(stale reviews are not evidence)"
        )
    if not isinstance(review.get("gates"), dict):
        raise ReviewError("manual review must contain a gates object")
    return review


def review_summary(review):
    """Keep unreviewed gates explicit; do not manufacture a pass."""
    gates = {name: str(value).upper() for name, value in review["gates"].items()}
    allowed = {"PASS", "FAIL", "UNVERIFIED"}
    invalid = {name: value for name, value in gates.items() if value not in allowed}
    if invalid:
        raise ReviewError("invalid gate values: %s" % invalid)
    return gates
