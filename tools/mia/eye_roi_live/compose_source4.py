"""Source | actual R3b | existing lower-only | existing lower+creaseC.

Reuses the saved R3b package's frozen global uniform SRT. No per-eye warping,
source repaint, generated pixels, pose refinement or artistic approval.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import math

from PIL import Image, ImageDraw, ImageFont


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transformed(image, registration):
    # Same similarity transform as refinement-v002/compose_source_review.py.
    scale = registration['uniform_scale']
    angle = math.radians(registration['rotation_degrees'])
    c, s = math.cos(angle), math.sin(angle)
    x, y = registration['translation_xy']
    return image.convert('RGBA').transform((640,640), Image.Transform.AFFINE,
        (c/scale,s/scale,-(c*x+s*y)/scale,-s/scale,c/scale,(s*x-c*y)/scale),
        Image.Resampling.BICUBIC, fillcolor=(237,242,246,255))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--capture', type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    capture = args.capture.resolve()
    assert (root/'.mia-cache/eye-roi').resolve() in capture.parents
    out = capture/'paired'
    assert not out.exists(), 'Do not overwrite review evidence'
    out.mkdir()
    pkg_path = root/'asset/mia/blender/mia-refinement-v002/review/integrated-R3b/paired-source/reference-review.json'
    pkg = json.loads(pkg_path.read_text(encoding='utf8'))
    records = json.loads((capture/'render-records.json').read_text(encoding='utf8'))
    component = json.loads((capture/'component-evidence.json').read_text(encoding='utf8'))
    assert component['GPU_used'] and len(records) == 12
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
    variants = ('saved_R3b','lower_only','lower_plus_crease_C')
    labels = ('SOURCE / original aspect','R3b / existing saved eyes',
              'Existing lower corrective only','Existing lower + creaseC')
    rows = []
    for view in pkg['views']:
        name = view['id']
        reference = copy.deepcopy(view['reference'])
        old = Path(reference['path'])
        if old.is_absolute():
            pieces = old.as_posix().split('/asset/mia/', 1)
            source = root/'asset/mia'/pieces[1] if len(pieces) == 2 else old
        else:
            source = (pkg_path.parent/old).resolve()
        assert sha(source) == reference['sha256']
        source_image = Image.open(source).convert('RGBA')
        crop = reference['crop_xyxy']
        canvas = Image.new('RGBA', source_image.size, (237,242,246,255))
        canvas.paste(source_image.crop(crop), crop[:2])
        selected = [next(r for r in records if r['id'] == v+'-'+name+'-hairOFF') for v in variants]
        assert all(sha(Path(r['path'])) == r['sha256'] for r in selected)
        assert selected[0]['camera'] == selected[1]['camera'] == selected[2]['camera'], name
        registration = copy.deepcopy(view['candidate_registration'])
        tiles = [transformed(canvas, view['reference_registration'])]
        tiles.extend(transformed(Image.open(r['path']), registration) for r in selected)
        board = Image.new('RGB', (2560,740), (237,242,246))
        draw = ImageDraw.Draw(board)
        for i, (tile,label) in enumerate(zip(tiles,labels)):
            board.paste(tile.convert('RGB'), (i*640,50))
            draw.text((i*640+8,12), label, font=font, fill=(24,38,49))
        draw.text((10,700), name+' | frozen global uniform SRT; pose uncertainty retained; existing-recipe diagnostic, not current live final or ART PASS.', font=small, fill=(24,38,49))
        board_path = out/(name+'-source-components.png')
        board.save(board_path)
        # One shared global-coordinate crop for all columns; no local eye alignment.
        roi = (80,150,560,380)
        eye_board = Image.new('RGB', (1920,285), (237,242,246))
        d = ImageDraw.Draw(eye_board)
        for i,(tile,label) in enumerate(zip(tiles,labels)):
            eye_board.paste(tile.crop(roi).convert('RGB'), (i*480,35))
            d.text((i*480+5,8), label, font=small, fill=(24,38,49))
        d.text((8,268), 'Identical crop from globally registered tiles. Red markup identifies aperture; lashes, liner, crease, brow and shadow are separate.', font=small, fill=(24,38,49))
        eye_path = out/(name+'-eye-ROI.png')
        eye_board.save(eye_path)
        reference['path'] = str(source)
        for stale in ('crop_artifact',):
            reference.pop(stale, None)
        rows.append(dict(id=name, reference=reference,
            baseline_render=dict(path=selected[0]['path'],sha256=selected[0]['sha256']),
            candidate_render=dict(path=selected[2]['path'],sha256=selected[2]['sha256']),
            lower_only_render=dict(path=selected[1]['path'],sha256=selected[1]['sha256']),
            comparison_board=dict(path=str(board_path),sha256=sha(board_path)),
            eye_ROI_board=dict(path=str(eye_path),sha256=sha(eye_path),shared_tile_crop=list(roi)),
            baseline_camera=selected[0]['camera'],candidate_camera=selected[2]['camera'],
            reference_registration=view['reference_registration'],
            baseline_registration=registration,candidate_registration=registration,
            pose_uncertainty=view['pose_uncertainty'],
            observed_differences='PENDING actual independent eye-ROI review. Existing components only; do not infer success from capture.',
            unresolved=['Source aperture upper/lower/corner correspondence not yet accepted.',
                        'Profile/oblique drawings retain documented pose/gaze/occlusion uncertainty.',
                        'hairON/matte/high-low/turn and expression visual gates remain open.'],
            material_mode='Actual savedR3b or declared scoped crease copies under the same three source lights. HairOFF.',
            apply_lists={v['composition']:v['apply_list'] for v in component['variants']}))
    result = dict(schema_version=1, part='face',
        required_views=['front','profile','left_oblique','right_oblique'],
        baseline_native=dict(path=component['source_native'],sha256=component['native_sha256']),
        candidate_native=dict(path=component['source_native'],sha256=component['native_sha256']),
        runtime_component_receipt=dict(path=str(capture/'component-evidence.json'),sha256=sha(capture/'component-evidence.json')),
        views=rows, scope='Existing deterministic components, actual source4 eye ROI diagnosis only; no new saved model or ART pass.')
    (out/'reference-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(output=str(out),boards=8,uniform_SRT_only=True,ART=False)))


if __name__ == '__main__':
    main()
