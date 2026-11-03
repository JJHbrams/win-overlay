"""Explicit official-MCP entry point (MCP exec is not Python __main__)."""
from pathlib import Path
import importlib.util
import json
import bpy
path=Path(__file__).with_name('rear_part.py')
spec=importlib.util.spec_from_file_location('mia_live_rear_part01',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
report=module.apply(runtime='live_mcp')
bpy.app.driver_namespace['MIA_RearPart01Module']=module
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=False
print(json.dumps(report))
