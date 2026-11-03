"""Official MCP entry for the one scoped early-look material prototype."""
from pathlib import Path
import importlib.util
import json
import bpy
path=Path(__file__).with_name('hair_tone_prototype.py')
spec=importlib.util.spec_from_file_location('mia_live_tone',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print(json.dumps(m.apply_to_live()))
bpy.app.driver_namespace['MIA_HairTonePrototypeModule']=m
