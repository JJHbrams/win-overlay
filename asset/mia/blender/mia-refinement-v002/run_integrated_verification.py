"""One sequential immutable-native CPU/GPU review; run with root GPU ownership."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--tag',required=True);ap.add_argument('--resume',action='store_true');a=ap.parse_args()
native=Path(a.native).resolve();meta=json.loads(native.with_suffix('.integration.json').read_text());digest=hashlib.sha256(native.read_bytes()).hexdigest();assert digest==meta['native_sha256']
B='C:/Program Files/Blender Foundation/Blender 5.2/blender.exe';flags=getattr(subprocess,'CREATE_NO_WINDOW',0);done=[];start=time.time()
def assert_clean_shader_log(log):
    text=log.read_text(encoding='utf-8',errors='replace')
    failures=[line for line in text.splitlines() if any(x in line.lower() for x in ['shader compilation error','shader compile error','too many vertex attributes','shader compilation failed','failed to compile'])]
    assert not failures,('Actual shader compilation failed despite possible PNG/marker output',str(log),failures)
def run(script,args,log,marker):
    with log.open('w',encoding='utf-8') as out:
        r=subprocess.run([B,'-b','--python-exit-code','2','--python',str(script),'--']+args,stdout=out,stderr=subprocess.STDOUT,creationflags=flags)
    text=log.read_text(encoding='utf-8',errors='replace');assert r.returncode==0 and marker in text,(log,r.returncode,text[-2000:])
    assert_clean_shader_log(log)
    assert hashlib.sha256(native.read_bytes()).hexdigest()==digest
    print(marker,flush=True)
fresh_path=native.with_suffix('.fresh-reopen.json')
if a.resume and fresh_path.exists():
    fresh=json.loads(fresh_path.read_text());assert fresh['sha256']==digest and not fresh['errors'] and fresh['technical_preservation_pass']
    print('RETAINED_COMPLETED_FRESH_REOPEN',flush=True)
else:
    run(P/'verify_integrated_scene.py',['--native',str(native),'--out',str(fresh_path)],P/(a.tag+'-fresh.log'),'V002_FRESH_REOPEN_DATA_OK')
for suite,count in [('source',20),('expressions',41),('intermediates',4),('critical',12),('orbit',24)]:
    records_path=P/'review'/a.tag/suite/'render-records.json';log=P/(a.tag+'-'+suite+'.log');marker=f'V002_INTEGRATED_REVIEW_DONE {suite} {count}'
    retained=False
    if a.resume and records_path.exists() and marker in log.read_text(encoding='utf-8',errors='replace'):
        assert_clean_shader_log(log)
        rs=json.loads(records_path.read_text());assert len(rs)==count and all(r['native_sha256']==digest and hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in rs)
        retained=True;print('RETAINED_COMPLETED_SUITE',suite,count,flush=True)
    else:
        run(P/'render_integrated_review.py',['--native',str(native),'--sha256',digest,'--tag',a.tag,'--suite',suite],log,marker)
    rs=json.loads(records_path.read_text());assert len(rs)==count and all(r['native_sha256']==digest and hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in rs)
    done.append(dict(suite=suite,frames=count,retained_previously_completed=retained))
report=dict(native=str(native),sha256=digest,suites=done,actual_frames=sum(r['frames'] for r in done),elapsed_seconds=time.time()-start,native_saved=False,
            art_approved=False,scope='Fresh reopen plus actual source,16expression pairs and bounded gaze/head/closure, critical and orbit. Render completion is not visual ART approval.')
(P/'review'/a.tag/'verification-completion.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('V002_INTEGRATED_VERIFICATION_DONE',report['actual_frames'],flush=True)
