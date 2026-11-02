"""Rebuild diagnostic source traces and samples; never edits source/model/UV."""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCE = Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png')
COARSE = Path(r'C:/Users/antio/.codex/worktrees/mia-v002-body/win-overlay/asset/mia/blender/mia-fit-v003/body/scaffold-D/source-contours.json')
EXPECTED = '6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1'
CROPS = {'front': [150,175,325,500], 'profile': [490,200,640,510],
         'back': [845,300,1015,515], 'oblique': [1220,165,1400,505]}
COLORS = {'bra.neckline': '#00d8ff', 'bra.band_top': '#ffe35b', 'bra.band_bottom': '#72ff67',
          'bra.strap': '#73a6ff', 'bra.side_return': '#c8a0ff', 'bra.outer': '#3dedbf',
          'brief.waist': '#ffb04a', 'brief.leg': '#ff70de', 'brief.crotch': '#ff8eaf',
          'brief.fold': '#d4c5ff', 'neck.line': '#9bf5e6', 'neck.shadow': '#ff8d79'}
paths = []


def add(name, role, view, points, limit, confidence='high', uncertainty=(1,3), closed=False):
    component = 'neck_clavicle' if role.startswith('neck.') else ('bra' if role.startswith('bra.') else 'briefs')
    kind = 'illustrated_graphic_line' if role == 'neck.line' else ('illustrated_shadow_boundary' if role == 'neck.shadow' else ('cloth_internal_transition' if role in ('bra.band_top','brief.fold') else 'observed_cloth_edge'))
    paths.append({'id': name, 'label': f'P{len(paths)+1:02d}', 'component': component, 'role': role,
                  'view': view, 'kind': kind, 'points_px': points, 'closed': closed,
                  'crop_xyxy': CROPS[view], 'confidence': {'level': confidence,
                  'pixel_uncertainty_range': list(uncertainty), 'interpretation': 'Manual visible-pixel tracing; qualitative confidence, not calibrated probability'},
                  'observed_limits': limit, 'seating_target':
                  ('FINAL posed neck/clavicle skin; cosmetic line/shadow channels after geometry fit' if component == 'neck_clavicle' else
                   'FINAL posed supported torso/shoulder surface; garment edge/seam paths' if component == 'bra' else
                   'FINAL posed pelvis/upper-thigh/crotch surface; garment coverage boundaries'),
                  'anatomical_root_claim': False})


# Original-pixel manual samples, refined by actual crop inspection. No hidden arcs are filled.
add('front.bra.scoop', 'bra.neckline', 'front', [[194,263],[200,272],[210,280],[220,285],[230,288],[240,290],[250,289],[260,286],[270,281],[280,275],[286,267]], 'Visible scoop only. Both upper strap continuations enter hair/braid; do not extend across occlusion.')
add('front.bra.cup_band_transition', 'bra.band_top', 'front', [[180,313],[188,319],[198,321],[210,320],[224,316],[235,313],[244,313],[257,316],[270,320],[284,321],[296,317]], 'Drawn cup-to-band transition. Sewing construction is not uniquely established; this is not an anatomical inframammary fold.', 'medium', (2,4))
add('front.bra.band_lower_edge', 'bra.band_bottom', 'front', [[190,333],[200,331],[210,329],[220,327],[230,326],[240,325],[250,325],[260,326],[270,328],[280,330],[290,333]], 'Visible cloth-to-skin edge. Lateral ends are hair-occluded; separate from the upper cup/band line.')
add('front.bra.left_inner_strap_fragment', 'bra.strap', 'front', [[193,248],[192,255],[194,263]], 'Short visible inner strap edge only. Shoulder attachment and outer boundary are hidden by hair.', 'medium', (2,4))
add('front.bra.right_inner_strap_fragment', 'bra.strap', 'front', [[289,256],[289,260],[286,267]], 'Short visible edge at braid overlap; do not infer hidden strap width or shoulder route.', 'medium', (2,4))
add('front.briefs.dipped_waist', 'brief.waist', 'front', [[164,413],[179,416],[195,421],[211,425],[226,428],[241,429],[256,427],[272,424],[289,420],[306,415],[314,412]], 'Upper cloth edge dips centrally. Different from the leg openings; trace does not prescribe body hip width.')
add('front.briefs.left_leg_opening', 'brief.leg', 'front', [[159,425],[173,430],[188,438],[201,447],[214,459],[226,473],[236,485]], 'High curved visible cloth/skin boundary, ending at narrow front crotch. Body-side left/right is not inferred from screen labels.')
add('front.briefs.right_leg_opening', 'brief.leg', 'front', [[319,425],[304,431],[290,440],[276,451],[263,464],[250,479],[245,485]], 'Visible high curved leg boundary. No hidden underbody return is supplied.')
add('front.briefs.crotch_turn_visible', 'brief.crotch', 'front', [[236,485],[239,483],[242,483],[245,485]], 'Only the tiny visible crotch turn above the inter-leg opening; underside pattern and seam remain unobserved.', 'medium', (2,3))
add('front.neck.left_clavicle_line', 'neck.line', 'front', [[211,221],[219,221],[225,220],[231,222],[236,225]], 'Thin illustrated clavicle cue, partly emerging from hair. Not a measured bone or a geometric groove.', 'medium', (1,3))
add('front.neck.right_clavicle_line', 'neck.line', 'front', [[249,225],[255,221],[263,220],[272,221],[280,220]], 'Thin source graphic cue; right continuation under braid/hair is unobserved.', 'medium', (1,3))
add('front.neck.under_chin_shadow', 'neck.shadow', 'front', [[218,185],[230,188],[249,181],[247,190],[237,199],[226,204],[218,208]], 'Approximate illustrated shadow region below chin. Soft boundary, lighting/paint mixture; not physical albedo, anatomy or a medical model.', 'medium', (3,6), True)

add('profile.bra.scoop_visible', 'bra.neckline', 'profile', [[505,281],[516,278],[529,273],[541,267],[552,260]], 'Skin/cloth neckline in profile, terminating under braid. Does not reveal the hidden opposite cup or root.')
add('profile.bra.cup_outer_silhouette', 'bra.outer', 'profile', [[505,281],[500,286],[498,294],[499,303],[502,311],[508,317],[516,320],[523,321]], 'Observed clothed outer projection; cannot be imposed as naked skin or increase-depth instruction.')
add('profile.bra.cup_band_transition_fragment', 'bra.band_top', 'profile', [[520,320],[530,320],[540,318],[547,316]], 'Only visible anterior cup/band line before hair occlusion. Do not join through braid shadow.', 'medium', (2,4))
add('profile.bra.band_lower_edge', 'bra.band_bottom', 'profile', [[520,328],[532,328],[545,329],[559,332],[571,335],[577,337]], 'Band skin edge follows sloped torso perspective and ends at arm occlusion.')
add('profile.bra.side_return_upper_fragment', 'bra.side_return', 'profile', [[562,298],[567,303],[573,306],[577,307]], 'Small side-return top edge between hair and upper arm; hidden back/strap topology is not recovered.', 'medium', (2,4))
add('profile.briefs.front_waist', 'brief.waist', 'profile', [[513,437],[522,430],[532,422],[544,416],[555,412],[566,410],[575,409]], 'Visible anterior-to-near-side upper edge, ending at foreground arm. Same garment as front dipped waist, different projection.')
add('profile.briefs.front_outer_turn', 'brief.crotch', 'profile', [[513,437],[515,451],[519,466],[523,477]], 'Visible anterior cloth silhouette/turn only; does not determine underbody thickness or hidden crotch seam.')
add('profile.briefs.near_leg_opening', 'brief.leg', 'profile', [[523,477],[524,462],[528,449],[535,438],[545,430],[557,425],[567,422],[575,421]], 'High leg opening rising toward side hip, interrupted by arm.')
add('profile.briefs.rear_waist_fragment', 'brief.waist', 'profile', [[609,422],[615,430],[620,437]], 'Small posterior fragment beyond foreground arm. Connection behind arm is unobserved.', 'medium', (2,4))
add('profile.briefs.rear_leg_fragment', 'brief.leg', 'profile', [[608,432],[617,438],[625,447]], 'Short posterior cloth/skin edge only. Do not reconstruct full back coverage from this fragment.', 'medium', (2,4))

add('back.bra.left_band_lower_fragment', 'bra.band_bottom', 'back', [[879,335],[884,335],[889,334]], 'Tiny cloth/skin lower-edge fragment only; upper boundary/straps hidden by rear hair.', 'low', (2,5))
add('back.bra.right_band_lower_fragment', 'bra.band_bottom', 'back', [[971,334],[977,335],[984,335]], 'Tiny visible lower band edge, heavily occluded. Does not authorize invented back strap topology.', 'low', (2,5))
add('back.briefs.dipped_waist', 'brief.waist', 'back', [[860,414],[878,415],[898,418],[919,419],[939,419],[961,417],[982,415],[994,413]], 'Observed back upper edge with shallow central dip. Hair obscures upper back, not this brief edge.')
add('back.briefs.left_leg_opening', 'brief.leg', 'back', [[856,426],[867,429],[880,434],[892,440],[903,449],[914,461],[923,474],[930,486]], 'High cut rear coverage narrowing into central crotch. Glute shading below is not a garment boundary.')
add('back.briefs.right_leg_opening', 'brief.leg', 'back', [[999,426],[987,429],[974,435],[962,442],[949,454],[939,468],[931,486]], 'Visible rear cloth/skin boundary; do not replace with front triangle coverage.')
add('back.briefs.crotch_visible_bridge', 'brief.crotch', 'back', [[930,486],[926,491],[923,494],[940,494],[935,490],[931,486]], 'Tiny rear cloth bridge above inter-leg opening; lower underbody continuation is hidden.', 'medium', (2,4))
add('back.briefs.center_fold_cue', 'brief.fold', 'back', [[930,442],[929,455],[930,468],[931,481]], 'Illustrated central cloth fold/cleft cue; stitching is not established. Cosmetic detail only.', 'low', (2,5))

add('oblique.bra.scoop', 'bra.neckline', 'oblique', [[1252,268],[1251,279],[1260,285],[1270,288],[1280,288],[1290,286],[1300,282],[1310,275],[1320,268],[1330,259]], 'Observed scoop including foreshortening. Both strap continuations meet hair/braid; no symmetry-normalized reconstruction.')
add('oblique.bra.cup_outer_silhouette', 'bra.outer', 'oblique', [[1252,268],[1243,281],[1235,292],[1234,301],[1237,311],[1244,318],[1254,321]], 'Visible near/far combined cloth silhouette, partly adjacent to hair; it is an outer support bound.', 'medium', (2,4))
add('oblique.bra.cup_band_transition', 'bra.band_top', 'oblique', [[1244,315],[1255,320],[1267,320],[1277,316],[1284,313],[1292,314],[1304,318],[1318,320],[1330,320],[1341,318]], 'Drawn cup/band transition, with hair-interrupted lateral end; not a naked breast-root curve.', 'medium', (2,4))
add('oblique.bra.band_lower_edge', 'bra.band_bottom', 'oblique', [[1255,332],[1267,329],[1280,326],[1291,326],[1304,328],[1320,331],[1336,333],[1352,337]], 'Observed lower band cloth/skin edge, clipped at lateral hair intersection. No continuation across hair.')
add('oblique.bra.near_inner_strap_fragment', 'bra.strap', 'oblique', [[1330,259],[1335,252],[1338,246]], 'Visible short inner strap fragment below braid; shoulder connection hidden.', 'medium', (2,4))
add('oblique.bra.side_return_upper_fragment', 'bra.side_return', 'oblique', [[1346,300],[1355,305],[1364,308],[1369,309]], 'Upper side-return segment beneath axilla, with braid and arm occlusion; does not mark skin axillary root.', 'medium', (2,4))
add('oblique.briefs.dipped_waist', 'brief.waist', 'oblique', [[1252,420],[1260,427],[1270,433],[1280,436],[1288,436],[1298,433],[1310,427],[1323,420],[1338,413],[1352,408],[1364,407],[1375,409]], 'Observed waist dip with strong near/far projection. No per-view width or feature normalization.')
add('oblique.briefs.far_leg_opening', 'brief.leg', 'oblique', [[1252,429],[1261,443],[1272,456],[1284,470],[1296,482],[1305,487]], 'Visible far/front cloth boundary narrowing into crotch; depth behind leg remains unknown.')
add('oblique.briefs.near_leg_opening', 'brief.leg', 'oblique', [[1380,420],[1368,420],[1354,423],[1340,429],[1327,439],[1317,450],[1310,463],[1307,479],[1307,490]], 'High curved near leg opening. Final path must sit on final pelvis/thigh topology, not a z-height mask.')
add('oblique.neck.left_clavicle_line', 'neck.line', 'oblique', [[1288,225],[1295,224],[1300,224],[1305,228]], 'Short illustrated cue emerging from hair; not a physical furrow.', 'medium', (1,3))
add('oblique.neck.right_clavicle_line', 'neck.line', 'oblique', [[1310,228],[1316,223],[1322,221],[1330,221]], 'Visible clavicle graphic stopping beneath braid.', 'medium', (1,3))
add('oblique.neck.under_chin_shadow', 'neck.shadow', 'oblique', [[1301,181],[1323,169],[1331,168],[1321,185],[1310,196],[1303,200]], 'Broad illustrated under-chin shadow, soft/painted boundary; not physical albedo or a geometry contour.', 'medium', (3,6), True)

PATCHES = [
    ('front.bra.midcup', 'front', [213,299,220,306], 'cloth shaded midtone, away from line/seam'),
    ('front.bra.lower_band', 'front', [235,318,242,323], 'band illustrated tone, below cup/band line'),
    ('profile.bra.front_cup', 'profile', [509,293,516,300], 'cloth illustrated shade under profile lighting'),
    ('front.briefs.front_panel', 'front', [219,435,226,442], 'brief illustrated midtone away from opening'),
    ('back.briefs.back_panel', 'back', [915,430,922,437], 'rear brief illustrated tone; compare rather than force equal front/back colors'),
    ('front.skin.abdomen', 'front', [217,345,224,352], 'illustrated skin tone; light and pigment are mixed'),
    ('front.neck.lit', 'front', [238,207,243,213], 'lit neck illustration, not measured albedo'),
    ('front.neck.shadow', 'front', [221,190,227,196], 'illustrated under-chin shadow'),
    ('front.clavicle.line_mixed', 'front', [222,220,228,223], 'thin antialiased graphic line plus underlying skin; mixed patch, not pure ink'),
    ('oblique.neck.shadow', 'oblique', [1307,183,1313,189], 'illustrated neck-shadow interior')]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def draw_paths(image, view=None, crop=None, scale=1):
    d = ImageDraw.Draw(image)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', max(12, int(8*scale)))
    ox, oy = crop[:2] if crop else (0,0)
    for p in paths:
        if view is not None and p['view'] != view:
            continue
        pts = [((x-ox)*scale,(y-oy)*scale) for x,y in p['points_px']]
        col = COLORS[p['role']]
        d.line(pts + ([pts[0]] if p['closed'] else []), fill=col, width=max(1,int(scale)))
        for x,y in pts:
            r=max(1,scale*.65);d.ellipse((x-r,y-r,x+r,y+r),fill=col)
        x,y=pts[len(pts)//2]
        d.text((x+3,y-12),p['label'],font=font,fill=col,stroke_width=2,stroke_fill='#14212b')
    return image


def main():
    assert sha(SOURCE) == EXPECTED
    source = Image.open(SOURCE).convert('RGB')
    assert source.size == (1536,1024)
    coarse = json.loads(COARSE.read_text(encoding='utf-8'))
    assert coarse['sha256'] == EXPECTED and coarse['size'] == [1536,1024]
    for p in paths:
        x0,y0,x1,y1=p['crop_xyxy']
        assert all(x0<=x<x1 and y0<=y<y1 for x,y in p['points_px']), p['id']
    manifest = {'schema_version':1,'source': {'path':str(SOURCE),'sha256':EXPECTED,'size_px':[1536,1024],
        'authority':'Exact user-confirmed v06; quantitative garment design anchor',
        'coordinates':'Original full-sheet pixels, x right/y down; crop bounds XYXY, upper inclusive/lower exclusive'},
        'body_source_contours':{'path':str(COARSE),'sha256':sha(COARSE),'source_sha256':coarse['sha256'],
        'relationship':'Read as coarser context only. These visible-pixel garment/graphic fragments refine coverage; old coarse endpoints do not override observed hair occlusion.'},
        'view_crops_xyxy':CROPS,'paths':paths,
        'unobserved':[
            {'region':'bra rear neckline/straps/central band construction','reason':'rear hair occludes it','points_px':[],'policy':'No invented path, symmetry completion, or generated-view dimensional substitution'},
            {'region':'strap shoulder attachment and outer edges beneath front hair/braid','reason':'hair occlusion','points_px':[],'policy':'Keep endpoints open; reconcile only after final body and evidence review'},
            {'region':'anatomical breast root/inframammary fold behind bra','reason':'clothing occludes skin anatomy','points_px':[],'policy':'Cloth neckline/band edges are not naked skin roots'},
            {'region':'brief underbody gusset/hidden crotch seam','reason':'not visible in v06','points_px':[],'policy':'Visible turns constrain coverage only; underside remains construction inference'}],
        'integration_order':[
            'Wait for selected FINAL POSED whole-body target; this pack does not approve or advance garment production.',
            'Seat corresponding scoop/strap/side-return/band and waist/leg/crotch paths onto final posed surfaces using source camera correspondence and local surface constraints.',
            'Keep cup-to-band transition and lower band edge distinct; preserve front and back brief coverage differences.',
            'Record each seated path as mesh triangle ID plus barycentric weights; transfer to final UV through that same surface correspondence.',
            'Use path-relative distances/coverage on the actual surface for later garment/color/normal/roughness work; do not use world-height thresholds or raw T-pose coordinates.',
            'Seat neck/clavicle graphic and illustrated shadow cues after shoulder/trapezius/neck fit; keep graphic ink, pigment and scene-light shadow roles explicit.',
            'Review actual source4/high-low and bounded poses after fitting; original arrays, face form and unrelated materials remain protected.'],
        'supplements_policy':'Generated 8-view/E2F2 supplements are qualitative construction aids only; none supplied dimensions, points or colors in this pack.',
        'status':'SOURCE_PREPARATION_ONLY; body/garment/UV/shader/ART acceptance NOT_EVALUATED'}
    write_json(HERE/'source-paths.json',manifest)
    arr=np.asarray(source)
    samples=[]
    for name,view,bounds,meaning in PATCHES:
        x0,y0,x1,y1=bounds;patch=arr[y0:y1,x0:x1];med=np.median(patch.reshape(-1,3),axis=0)
        samples.append({'id':name,'view':view,'patch_xyxy':bounds,'pixel_count':int(patch.shape[0]*patch.shape[1]),
                        'srgb_encoded_median_u8':med.tolist(),'srgb_encoded_median_0_1':(med/255).tolist(),
                        'srgb_encoded_p10_u8':np.percentile(patch.reshape(-1,3),10,axis=0).tolist(),
                        'srgb_encoded_p90_u8':np.percentile(patch.reshape(-1,3),90,axis=0).tolist(),
                        'interpretation':meaning})
    write_json(HERE/'appearance-samples.json',{'source_sha256':EXPECTED,'source_size_px':[1536,1024],
        'encoding':'PNG RGB byte values interpreted as sRGB illustration; no inverse lighting or physical albedo recovery',
        'use':'Illustrated appearance references only, not physical albedo, calibrated reflectance or medical model',
        'samples':samples})
    draw_paths(source.copy()).save(HERE/'source-overlay-original-aspect.png')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
    boards=[]
    for view,bounds in CROPS.items():
        crop=source.crop(bounds);scale=2
        original=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
        overlay=draw_paths(original.copy(),view,bounds,scale)
        ps=[p for p in paths if p['view']==view]
        board=Image.new('RGB',(original.width*2+24,original.height+72+len(ps)*22),'#12202c')
        board.paste(original,(0,48));board.paste(overlay,(original.width+24,48))
        d=ImageDraw.Draw(board);d.text((8,8),view.upper()+' | original crop / diagnostic trace | uniform 2x; no aspect warp',font=font,fill='white')
        y=original.height+60
        for p in ps:
            d.text((8,y),p['label']+' '+p['id']+' ['+p['confidence']['level']+']',font=small,fill=COLORS[p['role']]);y+=22
        name=f'{view}-pattern-board.png';board.save(HERE/name)
        boards.append({'path':name,'sha256':sha(HERE/name),'source_crop_xyxy':bounds,
                       'source_crop_size_px':list(crop.size),'uniform_scale':scale,'two_panels_same_crop':True,
                       'board_size_px':list(board.size),'labels':[p['label'] for p in ps]})
    proof={'schema_version':1,'status':'PASS','source_sha256_before':EXPECTED,'source_sha256_after':sha(SOURCE),
        'source_size_px':list(source.size),'source_unchanged':sha(SOURCE)==EXPECTED,'path_count':len(paths),
        'all_points_in_declared_original_crop':True,'all_points_integer_original_pixels':all(isinstance(c,int) for p in paths for xy in p['points_px'] for c in xy),
        'all_paths_have_confidence_and_observed_limits':all(p['confidence'] and p['observed_limits'] for p in paths),
        'sample_count':len(samples),'hidden_regions_have_no_invented_points':all(not u['points_px'] for u in manifest['unobserved']),
        'original_aspect_preserved':True,'boards':boards,
        'source_paths_sha256':sha(HERE/'source-paths.json'),'appearance_samples_sha256':sha(HERE/'appearance-samples.json'),
        'overlay_sha256':sha(HERE/'source-overlay-original-aspect.png'),
        'visual_overlay_review':'PENDING; must inspect generated PNGs before handoff',
        'body_garment_uv_shader_art_acceptance':'NOT_EVALUATED','native_render_or_model_edits':False}
    write_json(HERE/'verification.json',proof)
    print(json.dumps({'status':proof['status'],'paths':len(paths),'samples':len(samples),'boards':len(boards),'source_unchanged':proof['source_unchanged']}))


if __name__=='__main__':
    main()
