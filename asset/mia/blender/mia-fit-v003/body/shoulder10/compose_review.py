"""Original-aspect source4 and actual saved-native09/10 paired boards."""
from common import *
from PIL import Image,ImageDraw,ImageFont
rows=read(P/'actual/render-records.json');assert len(rows)==16
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
source=Image.open(SOURCE).convert('RGB');assert source.size==(1536,1024)
records=[];source_views=[]
spec=read(P/'source-rails.json');reg=spec['registration'];mpp=reg['metres_per_pixel'];oldbox=reg['source_crop_front']
cy=(oldbox[1]+oldbox[3])/2.-(1.33-1.275)/mpp;width=.4/mpp
centers=dict(front=239.,profile=558.790253340589,back=935.,oblique=float(1326.-.035*np.sin(np.deg2rad(40))/mpp))
limits=dict(front='Exposed skin roof; straps omitted. Illustrated lowA differs from static09; no recovered joint positions.',
            profile='Near profile estimate85deg, uncertainty8deg; cap/arm overlap and strap remain local limits.',
            back='Exposed posterior roof; straps obscure short runs; no exact scapular relief inferred.',
            oblique='Front3/4 estimate40deg +/-10deg. Independent wholebody pelvis/crotch axis1326 +/-8px; nominal cropcenter1313.81. No shoulder fit or width scale.')
for mode,view in [(r['mode'],r['view']) for r in rows if r['state']=='09']:
    before=next(r for r in rows if r['state']=='09' and r['mode']==mode and r['view']==view)
    after=next(r for r in rows if r['state']=='10' and r['mode']==mode and r['view']==view)
    assert before['actual_semantic_state']==after['actual_semantic_state'] and before['camera']==after['camera']
    for r in [before,after]:assert sha(r['path'])==r['sha256'] and sha(r['native']['path'])==r['native']['sha256']
    old=Image.open(before['path']).convert('RGB');new=Image.open(after['path']).convert('RGB')
    paired=Image.new('RGB',(1280,718),'#202632');d=ImageDraw.Draw(paired)
    for i,(im,label) in enumerate([(old,'SAVED09 BASELINE / '+mode+' '+view),(new,'SAVED10 / ONE A32 / '+mode+' '+view)]):paired.paste(im,(640*i,36));d.text((640*i+8,7),label,font=font,fill='white')
    d.text((8,684),'Actual saved native pair; same camera/gray/light. Headless static guide only; no UV/rig/fullbody claim. Candidate UNSELECTED.',font=small,fill='white')
    path=P/('pair-'+mode+'-'+view+'.png');paired.save(path);records.append(dict(view=view,mode=mode,path=str(path),sha256=sha(path)))
    if mode=='gray' and view in ['front','profile','back','oblique']:
        cx=centers[view];box=[cx-width/2,cy-width/2,cx+width/2,cy+width/2]
        src=source.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC)
        board=Image.new('RGB',(1920,752),'#202632');dd=ImageDraw.Draw(board)
        labels=['TIED-HAIR v06 / ORIGINAL-ASPECT','SAVED09 BASELINE / ORTHO','SAVED10 ONE A32 / ORTHO']
        for i,(im,label) in enumerate(zip([src,old,new],labels)):board.paste(im,(640*i,36));dd.text((640*i+8,7),label+' / '+view,font=font,fill='white')
        dd.text((8,684),limits[view],font=small,fill='white');dd.text((8,707),'Frozen wholeheight uniform metric; no shoulder/neck normalization. Native pair is headless static upperbody, source face/cloth is context only.',font=small,fill='white')
        path=P/('source-09-10-'+view+'.png');board.save(path)
        reference=dict(path=str(SOURCE),sha256=sha(SOURCE),crop_xyxy=box,original_size=list(source.size))
        displayreg=dict(uniform_scale=640/width,rotation_degrees=0,translation_xy=[-box[0]*640/width,-box[1]*640/width],
                        normalization_basis='Frozen E/09 wholeheight metric; crop shift only for camera targetZ1.33. Shoulder proportions excluded from registration.',notes='Same original1536x1024 panel canvas. Oblique independent pelvis/crotchX1326 +/-8px, screenoffset+12.19px from heldyaw40/targetY-.035; cropcenter1313.81 +/-8px, never shoulder-fitted. This assumes inferred pelvis centreline corresponds to worldX0/Y0; visiblecrotch is not recovered3Dcentre/AP landmark. Bounded display registration only, not calibrated sourcecamera or exactshoulder residuals.')
        renderreg=dict(uniform_scale=1.,rotation_degrees=0,translation_xy=[0,0],normalization_basis='Actual native render640x640 pasted unchanged; no silhouette normalization.')
        source_views.append(dict(id=view,reference=reference,baseline_render=dict(path=before['path'],sha256=before['sha256']),candidate_render=dict(path=after['path'],sha256=after['sha256']),
            comparison_board=dict(path=str(path),sha256=sha(path)),baseline_camera=before['camera'],candidate_camera=after['camera'],
            reference_registration=displayreg,baseline_registration=renderreg,candidate_registration=renderreg,pose_uncertainty=limits[view],
            observed_differences='ART FAIL: root/fresh reviewer confirmed S10-AC1/AC2 failure. Lowered roof introduces outer cap lip/front shoulder bar and profile cap-neck step. No promotion.',
            unresolved='Shoulder10 unselected. Neckside pinch/shelf, cap ridge, APbulk and lowerfixed transition require actual review. No production UV/rig/fullMia scope.',material_mode='Actual simple gray PrincipledBSDF output; base.23,roughness.85; same inherited saved09 lights/world/display.'))
        records.append(dict(view=view,mode='source',path=str(path),sha256=sha(path),reference=reference))
package=dict(schema_version=1,part='body',required_views=['front','profile','back','oblique'],baseline_native=rows[0]['native'],candidate_native=next(r['native'] for r in rows if r['state']=='10'),
             views=source_views,scope='One headless static shoulder design hypothesis; not production body/UV/rig/fullMia.',art_acceptance='FAIL S10-AC1/AC2 confirmed by root/fresh reviewer; unselected failure checkpoint')
write(P/'reference-review.json',package);write(P/'board-records.json',dict(actuals=16,boards=records,source_original_aspect=True,geometry_variants=1,ART='FAIL S10-AC1/AC2; no promotion'))
# Numeric annotation only: source pixels retained, no new raster artwork.
overlay=source.copy();dd=ImageDraw.Draw(overlay)
for name,trace in spec['traces_original_pixels'].items():
    color='#f00050' if 'front' in name else '#1255ff'
    for x,y in trace:dd.ellipse((x-2,y-2,x+2,y+2),fill=color)
dd.rectangle((24,970,1515,1018),fill='#202632');dd.text((35,976),'NUMERIC SOURCE TRACE: red front skin / blue back skin. Strap-crossing stations omitted. Original1536x1024 aspect.',font=font,fill='white')
overlay.save(P/'source-rails-overlay.png')
print('SHOULDER10_SOURCE4_AND_PAIRED_BOARDS_READY',flush=True)
