"""Same unselected G parameters; isolate its internal upper fade in RAM.

No fit/candidate/geometry output. The unfaded field is queried only below the
tentative guide cut1.445; a fresh loft to unchanged actual head is not built.
"""
from pathlib import Path
import sys,json,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parents[3]
A=C/'asset/mia/blender/mia-fit-v003';P=A/'body/surface-review12'

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
    guard=load('H_window_storage',A/'integration/workspace-storage-20261103/storage_guard.py');receipt=guard.inspect(10*1024*1024)
    if receipt['violations']:raise RuntimeError(json.dumps(receipt))
    g=load('H_old_G_diagnostic',P/'probe_proportion_G.py');source=P/'proportion-G-probe/RAM-calibration.json';params=json.loads(source.read_text(encoding='utf-8'))['parameters'];old,_,_=g.build_g(params)
    # Only the internal window changes, in this imported module's RAM. No
    # source file or source parameter is mutated. Infinity makes upper fade0.
    g.ZHEAD=float('inf');unfaded,_,_=g.build_g(params)
    z=np.array([1.42,1.435,1.445,1.455,1.465]);q=np.column_stack((np.zeros(len(z)),np.zeros(len(z)),z))
    out=[]
    for zz in z:
        row=dict(z=float(zz),inside_tentative_guide_domain=bool(zz<=1.445),cases={})
        for label,expr in [('frozen11',g.F11),('G_chosen_upper_fade',old),('same_G_fourparams_no_upper_fade',unfaded)]:
            # Root of each actual field along positive and negative axes atZ.
            roots=[]
            for axis in [0,1]:
                values=[]
                for sign in [-1,1]:
                    lo,hi=0.,.15
                    for _ in range(32):
                        mid=(lo+hi)/2;pt=np.array([[0.,0.,zz]]);pt[0,axis]=sign*mid;v=g.evaluate(expr,pt)[0]
                        if v<=0:lo=mid
                        else:hi=mid
                    values.append(sign*(lo+hi)/2)
                roots.append(values)
            row['cases'][label]=dict(x_roots_at_y0=roots[0],X_width_m=roots[0][1]-roots[0][0],y_roots_at_x0=roots[1],AP_width_m=roots[1][1]-roots[1][0])
        out.append(row)
    report=dict(status='RAM_WINDOW_ATTRIBUTION_NOT_A_NEW_CANDIDATE',source_calibration_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_fourparams=params,only_change='Disable oldG upper fade in RAM; relevant field queries only belowguide1.445. No profile solve or new body.',sections=out,headcut='Actual retained donor123-edge cutZ1.465, X53.39155mm/AP62.95353mm must stay exact; old guide field atZ1.465 is not a protected head.',unfaded_above_guide_cut='Diagnostic numbers only; MUST NOT use this field as upper-neck/head geometry. Fresh measured-tangent loft is required.',capacity=receipt,mesh_created=False,GPU_used=False,native_saved=False)
    d=C/'.mia-cache/body-h/shape';d.mkdir(parents=True,exist_ok=True);path=d/'upper-window-diagnostic.json';assert not path.exists();path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('H_UPPER_WINDOW',str(path),path.stat().st_size,flush=True)
    for row in out:print('SECTION_MM',row['z'],{k:[round(v['X_width_m']*1000,3),round(v['AP_width_m']*1000,3)] for k,v in row['cases'].items()},flush=True)

if __name__=='__main__':main()
