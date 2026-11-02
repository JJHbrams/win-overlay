"""One bounded B hypothesis: independently vary breast width/depth/center."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;A=P.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((A/'parameters.json').read_text());s=p['source_consumed_before_geometry'];assert len(s['section_support_bands'])==4
assert sha(Path(p['sources']['v06_path']))==p['sources']['v06_sha256'] and sha(Path(p['sources']['low_path']))==p['sources']['low_sha256']
p['version']='design-sculpt07-B';p['parent_failed_A_parameters_sha256']=sha(A/'parameters.json')
p['hypothesis']='Independent RX(z),RY(z),CY(z): broad upper/lower breast attachment returns inside the curved thorax before capped volume ends. Bury shoulder/root masses; no global blend inflation.'
z=[1.160,1.180,1.195,s['section_support_bands'][3]['world_z'],s['section_support_bands'][2]['world_z'],s['section_support_bands'][1]['world_z'],s['section_support_bands'][0]['world_z'],1.340,1.365,1.385]
rx=[.048,.059,.065,.069,.071,.070,.067,.063,.055,.045]
cy=[.025,.010,-.005,-.043,-.055,-.040,-.030,-.005,.010,.020]
front=[-.025,-.072,-.110]+[r['v06_front_profile_y']-off for r,off in zip(reversed(s['section_support_bands']),[.014,.007,.008,.008])]+[-.090,-.065,-.040]
ry=[c-f for c,f in zip(cy,front)]
p['breast']=dict(center_x=p['breast']['center_x'],z_min=z[0],z_max=z[-1],x_radius=list(map(list,zip(z,rx))),y_radius=list(map(list,zip(z,ry))),center_y=list(map(list,zip(z,cy))),posterior_cap_y=.012,interbreast_blend=.003,thorax_blend=.016,
   manual_justification='Same observed v06 station heights and explicit front allowances as A. Independent broad RX is an anatomical root hypothesis; upper/lower CY returns posteriorly so terminal caps are inside thorax. RY=CY−declared front. No shared shrinking radial factor. Posterior cap is an internal primitive closure buried inside thorax, not an axillary cut or external membrane.')
p['thorax']['x_radius']=[[1.035,.105],[1.12,.108],[1.18,.120],[1.25,.134],[1.32,.145],[1.35,.155],[1.38,.153],[1.40,.108],[1.435,.055],[1.47,.037],[1.525,.034]]
p['shoulder']=dict(center=[.146,.008,1.361],radii=[.037,.043,.054],angle_y_degrees=-12.,blend=.014)
p['upper_arm']=dict(center=[.195,.007,1.255],radii=[.032,.036,.133],angle_y_degrees=-25.,blend=.012)
p['anterior_fan']=dict(center=[.128,-.014,1.336],radii=[.050,.025,.049],angle_y_degrees=-24.,blend=.012)
p['posterior_wall']=dict(center=[.126,.016,1.321],radii=[.048,.022,.064],angle_y_degrees=-27.,blend=.010)
p['trapezius']=dict(center=[.080,.010,1.405],radii=[.076,.040,.035],angle_y_degrees=12.,blend=.016)
p['construction_limits'].append('B root/shoulder widths are manual anatomical hypotheses checked against source actuals, not exact recovered shoulder/hidden root dimensions. Positive posterior cap must remain buried; report any exposed cap.')
p['context_mask_B']='Private source polygon arms use semantic arm/hand bone weights and resume belowZ1.18; torso context resumes belowZ1.075. Face690 excluded. Context seams remain UNVERIFIED.'
(P/'parameters.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8');print('SCULPT07_B_PARAMETERS_FROZEN',flush=True)
