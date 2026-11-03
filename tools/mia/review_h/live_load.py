"""Open the protected source in a verified unused live Blender, through MCP."""
import bpy
import hashlib
from pathlib import Path

p = Path('D:/MiaWorkCache/mia-reference-work/win-overlay/asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend')
assert bpy.data.filepath == '' and not bpy.data.is_dirty, 'Do not overwrite another working scene'
assert hashlib.sha256(p.read_bytes()).hexdigest() == '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
bpy.ops.wm.open_mainfile(filepath=str(p), load_ui=False)
print('MIA_PROTECTED_R3B_OPENED_LIVE', bpy.data.filepath)
