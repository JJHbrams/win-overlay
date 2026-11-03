from pathlib import Path
import copy,json,hashlib
P=Path(__file__).resolve().parent;CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');E=CAN/'blender/mia-fit-v003/body/design-sculpt07/E';OLD=P.parent/'posterior-continuity08'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (P/'posterior09.npz').exists(),'One reconstruction only; no sweep'
original=json.loads((E/'parameters.json').read_text(encoding='utf-8'));candidate=copy.deepcopy(original)
assert original['posterior_wall']['blend']==.010;candidate['posterior_wall']['blend']=.014
def difference(a,b,path=''):
    if isinstance(a,dict):return sum([difference(a[k],b[k],path+'.'+k) for k in a],[])
    if isinstance(a,list):return sum([difference(x,y,path+'['+str(i)+']') for i,(x,y) in enumerate(zip(a,b))],[])
    return [] if a==b else [dict(path=path,before=a,after=b)]
diff=difference(original,candidate);assert diff==[dict(path='.posterior_wall.blend',before=.010,after=.014)]
(P/'parameters.json').write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf-8',newline='\n')
protected=json.loads((OLD/'protected-input-hashes.json').read_text(encoding='utf-8'))
for f in OLD.rglob('*'):
    if f.is_file() and '__pycache__' not in f.parts:protected[str(f)]=sha(f)
for f in [E/'parameters.json',E/'field.py',E/'build_breast.py',E.parent/'field.py']:protected[str(f)]=sha(f)
for f,h in protected.items():assert sha(f)==h,('Frozen input changed',f)
(P/'protected-input-hashes.json').write_text(json.dumps(protected,indent=2)+'\n',encoding='utf-8',newline='\n')
(P/'parameter-diff.json').write_text(json.dumps(dict(source_E_parameters_sha256=sha(E/'parameters.json'),candidate_parameters_sha256=sha(P/'parameters.json'),only_change=diff,field_implementation_sha256=sha(E/'field.py'),accumulation='Exact frozen E make(p) order; posterior wall joins the accumulated trunk/breast/shoulder/upper-arm/anterior-fan union, followed by unchanged trapezius.'),indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_PARAMETERS_READY',diff)
