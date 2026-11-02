"""Frozen numeric/verification inputs for this scoped checkpoint only."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent
MAPPING = ROOT / 'inputs/mapping-frame1.npz'
MAPPING_SHA256 = 'c36230677c7491af3ec35f1cd0dce579647ce3bad9e4c5db5495304fbd567045'

def frozen_mapping():
    assert hashlib.sha256(MAPPING.read_bytes()).hexdigest() == MAPPING_SHA256
    return MAPPING
