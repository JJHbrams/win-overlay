"""Own11 artifact paths; saved09 baseline, canonicalizedFINAL11 only."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;BASE=P.parent/'posterior-union09'
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
SOURCE=CAN/'references/body-foundation/v06/mia-body-visibility-guide-v06.png'
NATIVE09=BASE/'native/Mia_PosteriorUnion09_STATIC_ShapeGuide.blend'
NATIVE11=P/'native/Mia_Shoulder11_STATIC_ShapeGuide.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8',newline='\n')
