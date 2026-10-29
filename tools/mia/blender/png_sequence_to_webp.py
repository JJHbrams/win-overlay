"""Create a transparent animated WebP from one rendered 30fps PNG sequence."""
import argparse
from pathlib import Path

from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frames-dir", action="append", required=True, help="repeat to concatenate clips")
    p.add_argument("--output", required=True)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--method", type=int, choices=range(7), default=0)
    ns = p.parse_args()
    paths = [path for directory in ns.frames_dir for path in sorted(Path(directory).glob("*.png"))]
    if not paths:
        raise RuntimeError("No PNG frames found")
    images = [Image.open(path).convert("RGBA") for path in paths]
    # 33,33,34ms repeated is an exact 100ms per three-frame 30fps cadence.
    durations = [33 + (1 if i % 3 == 2 else 0) for i in range(len(images))] if ns.fps == 30 else round(1000 / ns.fps)
    # Fast proof packaging; source PNG sequences remain the authoritative frames.
    images[0].save(ns.output, save_all=True, append_images=images[1:], duration=durations, loop=0,
                   lossless=False, quality=70, method=ns.method)


if __name__ == "__main__":
    main()
