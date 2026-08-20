#!/usr/bin/env python3
"""Permanent ingestion step: bakes EXIF orientation into pixel data and
clears the orientation tag, so every downstream consumer (thumbnails,
contact sheets, review tool, upload queue) sees a correctly-oriented image
without having to interpret EXIF itself.

Runs BEFORE thumbnails, contact sheets, review, or upload -- insert it
first in the ingestion order, over the deduped file set (see
PIPELINE.md's ingestion order).

What this does NOT do: guess. A file with no EXIF orientation tag gives no
signal to correct from -- common for scans, screenshots, and some cameras.
Those files are never touched; they're listed in a CSV (dimensions +
aspect ratio) for visual confirmation by a person, same as
scripts/reconciliation-audit.py's "report, don't guess" pattern elsewhere
in this pipeline.

In-place and destructive to the file's EXIF orientation tag (the visual
result is unchanged -- what was previously "rotate on display" becomes
"rotate once, bake it in" -- but the tag itself is gone afterward, by
design, so nothing downstream can misinterpret it a second time). Back up
the staging directory before a real run if that matters to you; this
script does not make its own backup.

Usage:
  python3 scripts/normalize-orientation.py <staging_dir> [--dry-run]

Writes needs-review CSV to <staging_dir>/orientation-needs-review.csv.
"""
import argparse, csv, os, sys
from PIL import Image, ImageOps

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}

# EXIF orientation tag id (standard Exif spec, tag 0x0112)
ORIENTATION_TAG = 0x0112


def find_images(root):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in IMAGE_EXT:
                yield os.path.join(dirpath, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("staging_dir")
    ap.add_argument("--dry-run", action="store_true", help="report what would change, write nothing")
    args = ap.parse_args()

    corrected = []
    already_normal = []
    needs_review = []
    errors = []

    for path in find_images(args.staging_dir):
        rel = os.path.relpath(path, args.staging_dir)
        try:
            with Image.open(path) as img:
                exif = img.getexif()
                orientation = exif.get(ORIENTATION_TAG)

                if orientation == 1:
                    already_normal.append(rel)
                    continue

                if orientation is None or orientation not in range(2, 9):
                    # Missing tag, or a value outside the valid 1-8 range
                    # (seen in the wild as a stray 0) -- PIL's exif_transpose
                    # is a no-op for anything it doesn't recognise, which
                    # would silently report "corrected" while changing
                    # nothing. No usable signal either way -- don't guess.
                    w, h = img.size
                    reason = ("no EXIF orientation tag" if orientation is None
                              else f"invalid EXIF orientation value ({orientation}), not 1-8")
                    needs_review.append({
                        "filepath": rel, "width": w, "height": h,
                        "aspect_ratio": round(w / h, 3) if h else "",
                        "reason": reason + " -- cannot auto-correct, cannot rule out rotation",
                    })
                    continue

                if args.dry_run:
                    corrected.append((rel, orientation))
                    continue

                fixed = ImageOps.exif_transpose(img)  # bakes rotation/flip into pixels
                fixed_exif = fixed.getexif()
                if ORIENTATION_TAG in fixed_exif:
                    del fixed_exif[ORIENTATION_TAG]
                fixed.save(path, exif=fixed_exif)
                corrected.append((rel, orientation))
        except Exception as e:
            errors.append((rel, str(e)))

    review_path = os.path.join(args.staging_dir, "orientation-needs-review.csv")
    with open(review_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["filepath", "width", "height", "aspect_ratio", "reason"])
        w.writeheader()
        w.writerows(needs_review)

    print(f"{'would correct' if args.dry_run else 'corrected'}: {len(corrected)}")
    for rel, orientation in corrected:
        print(f"  {rel} (EXIF orientation was {orientation})")
    print(f"already normal (orientation=1): {len(already_normal)}")
    print(f"needs manual review (no EXIF orientation tag): {len(needs_review)} -- see {review_path}")
    print(f"errors: {len(errors)}")
    for rel, err in errors:
        print(f"  {rel}: {err}")


if __name__ == "__main__":
    main()
