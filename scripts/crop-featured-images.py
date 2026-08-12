#!/usr/bin/env python3
"""Batch-resizes and centre-crops a folder of images to a fixed 3:2 pixel
size, for the featured-reference section's image pools. Optional -- the
site already handles mismatched source sizes at display time via CSS
(aspect-ratio + object-fit: cover), so this is only for shrinking large
files before dropping them in, never required for the section to work.

Never distorts: each image is scaled up (if needed) so it fully covers the
target box, then centre-cropped to it -- same result CSS cover produces,
done once at file level instead of in the browser on every load.

Originals are never modified. Output goes to a separate folder, filenames
preserved, always written as .jpg.

Usage (not run automatically):
  python3 scripts/crop-featured-images.py <input_dir> <output_dir> \
      [--width 1200] [--height 800] [--quality 85]

Example, for one of the featured pools:
  python3 scripts/crop-featured-images.py \
      "assets/Book Frames" "assets/Book Frames/cropped"
"""
import argparse, os, sys
from PIL import Image, ImageOps

VALID_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")


def center_crop_cover(img, target_w, target_h):
    img = ImageOps.exif_transpose(img)  # respect camera/scan rotation metadata
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        # source is relatively wider -- scale to match height, crop width
        scale_h = target_h
        scale_w = round(src_w * (target_h / src_h))
    else:
        scale_w = target_w
        scale_h = round(src_h * (target_w / src_w))

    resized = img.resize((max(scale_w, target_w), max(scale_h, target_h)), Image.LANCZOS)
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir")
    ap.add_argument("output_dir")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--height", type=int, default=800)  # 1200x800 = 3:2
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()

    if not os.path.isdir(args.input_dir):
        sys.exit(f"not a directory: {args.input_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    done = skipped = 0
    for name in sorted(os.listdir(args.input_dir)):
        if not name.lower().endswith(VALID_EXTS):
            continue
        src_path = os.path.join(args.input_dir, name)
        if not os.path.isfile(src_path):
            continue
        try:
            with Image.open(src_path) as img:
                img = img.convert("RGB")
                cropped = center_crop_cover(img, args.width, args.height)
                out_name = os.path.splitext(name)[0] + ".jpg"
                out_path = os.path.join(args.output_dir, out_name)
                cropped.save(out_path, "JPEG", quality=args.quality)
                done += 1
                print(f"{name} -> {out_name} ({args.width}x{args.height})")
        except Exception as e:
            skipped += 1
            print(f"skipped {name}: {e}", file=sys.stderr)

    print(f"done={done} skipped={skipped} output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
