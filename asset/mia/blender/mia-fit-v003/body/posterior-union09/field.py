"""Frozen E field implementation, only caller's constant parameter differs."""
from pathlib import Path
import sys,importlib.util
sys.dont_write_bytecode=True
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E/field.py')
spec=importlib.util.spec_from_file_location('posterior09_frozen_E_field',SOURCE);source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
make=source.make;ma=source.ma;evaluate=source.evaluate;nodes=source.nodes
