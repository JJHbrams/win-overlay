"""One approved nested-trapezius accumulated field with lower sampling collar."""
from pathlib import Path
import sys,copy,importlib.util
sys.dont_write_bytecode=True
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E/field.py')
spec=importlib.util.spec_from_file_location('shoulder11_frozen_E_field',SOURCE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
ma=base.ma;evaluate=base.evaluate;nodes=base.nodes
def make(p):
    original=copy.deepcopy(p);original['trapezius']=p['shoulder11']['old_trapezius'];fold,reg=base.make(original);fhom,_=base.make(p)
    z=base.E('POS',2);s=p['shoulder11'];weight=base.smooth01((z-s['gate_zero_z'])/(s['gate_full_z']-s['gate_zero_z']))
    return fold+weight*(fhom-fold),dict(reg,original_final_union=fold,homothetic_final_union=fhom,vertical_gate=weight)
