"""Actual source/D/E diagnostic boards and this namespace's small manifest."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=P.parent;D=E.parent/'D';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
rows=json.loads((P/'render-records.json').read_text());assert len(rows)==4
for row in rows:assert sha(P/Path(row['path']).name)==row['sha256']
boards=[]
for view,size in [('front',640),('F2lowoblique',887)]:
    original=Image.open(E/('source-'+view+'.png')).convert('RGB').crop((0,34,size,size+34));board=Image.new('RGB',(size*3,size+105),'#202632');draw=ImageDraw.Draw(board)
    for i,(image,title) in enumerate([(original,'Source / original aspect'),(Image.open(P/('D-bra-'+view+'.png')).convert('RGB'),'HELD D / partial front cloth'),(Image.open(P/('E-bra-'+view+'.png')).convert('RGB'),'Frozen E / SAME fixed coverage')]):
        assert image.size==(size,size);board.paste(image,(i*size,34));draw.text((i*size+8,7),title,font=font,fill='white')
    draw.text((8,size+42),'Observed front P01 scoop + P03 lower edge; side connectors are artificial diagnostic clips INSIDE cloth, not seams.',font=small,fill='white')
    draw.text((8,size+63),'One fixed actual-surface attribute per D/E; F2 side/underside and hidden straps/closure UNCALIBRATED. No UV/cloth force.',font=small,fill='white')
    draw.text((8,size+84),'Gray shape review remains primary. Temporary context seams, head unchanged; not garment or whole-body acceptance.',font=small,fill='white');out=P/('source-D-E-bra-'+view+'.png');board.save(out);boards.append(dict(path=out.name,sha256=sha(out),source_image_crop_from=str(E/('source-'+view+'.png')),source_image_sha256=sha(E/('source-'+view+'.png'))))
report=json.loads((P/'coverage-report.json').read_text());source=Image.open('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png').convert('RGB').crop((150,230,325,355)).resize((700,500),Image.Resampling.NEAREST);draw=ImageDraw.Draw(source);poly=report['polygon_original_source_pixels'];mapped=[((x-150)*4,(y-230)*4) for x,y in poly]
for i,(a,b) in enumerate(zip(mapped,mapped[1:]+mapped[:1])):draw.line([a,b],fill='#ffac4a' if i in [10,21] else '#00e4e4',width=3)
out=Image.new('RGB',(700,550),'#202632');out.paste(source,(0,25));d=ImageDraw.Draw(out);d.text((7,4),'Original source x4 equal scale / cyan observed, orange diagnostic clips',font=small,fill='white');d.text((7,530),'No inferred outer seams/strap widths. No source or model shape edit.',font=small,fill='white');out.save(P/'observed-front-polygon.png')
frozen=json.loads((E/'manifest.json').read_text());assert all(sha(E/k)==v for k,v in frozen['files'].items());protected=json.loads((E/'D-protected-hashes.json').read_text());assert all(sha(D/k)==v for k,v in protected.items())
files={str(f.relative_to(P)).replace('\\','/'):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.name!='manifest.json'}
(P/'manifest.json').write_text(json.dumps(dict(status='Partial front-observed fixed3Dcoverage diagnostic; no garment/body acceptance',first15_checkpoint='c5275f7',first15_manifest_sha256=sha(E/'manifest.json'),first15_files_exact=True,D_protected_files_exact=True,actual_frames=4,actual_images=[dict(path=Path(r['path']).name,sha256=r['sha256'],view=r['view'],state=r['state']) for r in rows],boards=boards,files=files,limits=report['limits']),indent=2)+'\n',encoding='utf-8');print('BRA_DIAGNOSTIC_FOUR_BOARDS_FROZEN',len(files))
