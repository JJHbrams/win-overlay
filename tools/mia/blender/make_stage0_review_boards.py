"""Arrange unchanged evidence frames; no image synthesis or geometry edits."""
from pathlib import Path
import argparse
from PIL import Image, ImageDraw, ImageOps

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
sources = ['pixal_single', 'pixal_mv', 'pixal_full', 'previous0240', 'latest0416']
views = ['front', 'side', 'back', 'three_quarter_right', 'three_quarter_left']
for mode in ('actual', 'clay'):
    board = Image.new('RGB', (320 * len(views), 344 * len(sources)), '#20252a')
    draw = ImageDraw.Draw(board)
    for row, source in enumerate(sources):
        for col, view in enumerate(views):
            path = a.directory / f'{source}_{view}_{mode}.png'
            with Image.open(path) as im:
                tile = ImageOps.contain(im.convert('RGB'), (320, 320))
            board.paste(tile, (col * 320, row * 344 + 24))
            draw.text((col * 320 + 5, row * 344 + 5), f'{source} / {view}', fill='white')
    board.save(a.directory / f'head-review-{mode}.png')

views = ['front', 'side', 'back']
sources = ['pixal_full', 'previous0240', 'latest0416']
board = Image.new('RGB', (384 * 3, 408 * 3), '#20252a')
draw = ImageDraw.Draw(board)
for row, source in enumerate(sources):
    for col, view in enumerate(views):
        with Image.open(a.directory / f'{source}_full_{view}_actual.png') as im:
            tile = ImageOps.contain(im.convert('RGB'), (384, 384))
        board.paste(tile, (col * 384, row * 408 + 24))
        draw.text((col * 384 + 5, row * 408 + 5), f'{source} / {view}', fill='white')
board.save(a.directory / 'full-review-actual.png')
