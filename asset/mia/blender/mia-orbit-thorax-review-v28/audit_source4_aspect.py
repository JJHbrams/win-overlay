"""Forensic replay of historical SOURCE-only aspect distortion; no model edits."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

OLD=Path(r'C:/Users/antio/.codex/worktrees/mia-reference-recovery/win-overlay/asset/mia/blender/mia-body-finish-v23')
OUT=Path(__file__).parent/'source4-v23n-aspect-audit';OUT.mkdir(exist_ok=True)
SOURCE=Path(__file__).resolve().parents[2]/'references/body-foundation/v06/mia-body-turnaround-v06.png'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
oldmeta=json.loads((OLD/'source4-v23n/reference-review.json').read_text())
source=Image.open(SOURCE).convert('RGB');assert source.size==(1536,1024)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',23);small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)

def similarity(matrix):
    sig=np.linalg.svd(np.asarray(matrix,float)[:2,:2],compute_uv=False)
    return {'singular_scales':sig.tolist(),'anisotropy_ratio':float(sig.max()/sig.min()),'uniform':bool(np.allclose(sig[0],sig[1],rtol=1e-8,atol=1e-10))}

assert not similarity([[4/3,0,0],[0,1,0],[0,0,1]])['uniform']
assert similarity([[1,0,64],[0,1,31],[0,0,1]])['uniform']
records=[]
for index,name in enumerate(['front','profile','back','oblique']):
    row=next(r for r in oldmeta['views'] if r['id']==name)
    assert sha(SOURCE)==row['reference']['sha256']
    crop=[index*384,0,(index+1)*384,1024];tile=source.crop(crop)
    old=Image.open(OLD/'source4-v23n'/f'source_candidate_{name}.png').convert('RGB')
    wrong=tile.resize((512,1024),Image.Resampling.LANCZOS)
    # Bottom label overlaps the historical board, so compare the first1000px only.
    pixel_error=int(np.abs(np.asarray(old.crop((0,31,512,1031)),int)-np.asarray(wrong.crop((0,0,512,1000)),int)).max())
    candidate=Image.open(OLD/'review-v23n'/('clay_body_three_quarter.png' if name=='oblique' else f'clay_body_{name}.png')).convert('RGB').crop((256,0,768,1024))
    board=Image.new('RGB',(1536,1140),'#edf1f5');d=ImageDraw.Draw(board)
    d.text((16,10),f'{name}: 원본 비율 / 과거 잘못된 표시 / 당시 모델',font=font,fill='#172633')
    for i,label in enumerate(['원화384x1024 · 좌우여백만 추가','과거원화512x1024 · 가로133.3%','당시 v23n 모델 · 원래512x1024']):d.text((i*512+12,48),label,font=small,fill='#172633')
    board.paste(tile,(64,85));board.paste(wrong,(512,85));board.paste(candidate,(1024,85))
    d.text((12,1116),'원본 파일 불변. 가운데 비교판은 가로/세로 비율 오류로 폐기 대상. 왼쪽은 crop 후 재배율 없이 여백만 추가.',font=small,fill='#172633')
    path=OUT/f'{name}-aspect-audit.png';board.save(path)
    records.append({'view':name,'reference_crop':crop,'source_crop_size':[384,1024],'old_display_size':[512,1024],'old_source_transform':similarity([[4/3,0,0],[0,1,0],[0,0,1]]),'old_actual_source_pixels_match_reproduction_max_error':pixel_error,'correct_display_transform':similarity([[1,0,64],[0,1,85],[0,0,1]]),'candidate_crop_size':[512,1024],'audit_board':{'path':path.name,'sha256':sha(path)},'old_comparison':{'path':str(OLD/'source4-v23n'/f'source_candidate_{name}.png'),'sha256':sha(OLD/'source4-v23n'/f'source_candidate_{name}.png')}})
assert all(r['old_actual_source_pixels_match_reproduction_max_error']==0 for r in records)
report={'producer':{'path':str(OLD/'assemble_source4_v23n.py'),'sha256':sha(OLD/'assemble_source4_v23n.py'),'error_line':32},'original_reference':{'path':str(SOURCE),'sha256':sha(SOURCE),'size':list(source.size)},'old_package':{'path':str(OLD/'source4-v23n/reference-review.json'),'sha256':sha(OLD/'source4-v23n/reference-review.json')},'conclusion':'Old source4-v23n boards stretch SOURCE horizontally by4/3 while leaving model crop unchanged. They are invalid for proportion/anatomy acceptance. Original art bytes are unchanged. Corrected displays use original crop pixels and padding only; they do not claim pose/scale matching.','views':records}
(OUT/'aspect-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'views':len(records),'source_x_scale':4/3,'source_y_scale':1,'historical_pixels_reproduced_exactly':True}))
