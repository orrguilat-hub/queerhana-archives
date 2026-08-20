#!/usr/bin/env python3
"""Report-only orientation detection over every item in approved.csv (i.e.
every already-uploaded item). Never corrects, never rebuilds, never
re-uploads anything -- purely diagnostic, feeding a human decision.

For each file: dimensions, aspect ratio, EXIF orientation value, whether
it's auto-correctable (valid EXIF orientation 2-8) or needs a person's eyes
(missing/invalid EXIF orientation). For needs-eyes image files, also runs
face detection at 0/90/180/270 degrees as an orientation HINT (which
rotation(s) a face was found at) -- a hint only, never used to decide
anything here.

Usage:
  PYTHONWARNINGS=ignore python3 scripts/detect-orientation-issues.py [out.csv]
"""
import csv, os, sys
import cv2
from PIL import Image

APPROVED_CSV = "internal/review/full-batch/approved.csv"
STAGING_ROOT = os.path.expanduser("~/Documents/QHarchive-staging")
DEFAULT_OUT = "orientation-detection.csv"
ORIENTATION_TAG = 0x0112
IMAGE_EXT = {".jpg", ".jpeg", ".png"}

CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def identifier_for(filepath):
    import re
    def slugify(s):
        s = s.lower().strip()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return re.sub(r"-+", "-", s).strip("-")
    stem = os.path.splitext(os.path.basename(filepath))[0]
    return f"queerhana-{slugify(stem)}"


def face_orientation_hint(path):
    """Returns list of degrees (0/90/180/270) where a face was found, or
    None if the file isn't an image format this detector supports."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXT:
        return None
    img = cv2.imread(path)
    if img is None:
        return None
    hits = []
    for deg in (0, 90, 180, 270):
        rotated = img
        for _ in range(deg // 90):
            rotated = cv2.rotate(rotated, cv2.ROTATE_90_CLOCKWISE)
        gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
        faces = _cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) > 0:
            hits.append(deg)
    return hits


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT

    with open(APPROVED_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    results = []
    auto_correctable = 0
    needs_eyes = 0
    already_normal = 0
    missing_files = 0

    for i, row in enumerate(rows):
        rel = row["filepath"]
        full = os.path.join(STAGING_ROOT, rel)
        ident = identifier_for(rel)

        if not os.path.exists(full):
            missing_files += 1
            results.append({
                "archive_id": ident, "filepath": rel, "width": "", "height": "",
                "aspect_ratio": "", "exif_orientation": "", "face_hint_degrees": "",
                "status": "file not found locally",
            })
            continue

        ext = os.path.splitext(full)[1].lower()
        if ext not in IMAGE_EXT and ext not in {".mpg", ".mpeg", ".mp4", ".mov", ".pdf", ".odt", ".doc", ".docx"}:
            pass  # fall through, will just fail the Image.open below and get skipped

        try:
            with Image.open(full) as img:
                w, h = img.size
                orientation = img.getexif().get(ORIENTATION_TAG)
        except Exception:
            # Not an image PIL can open (video, pdf, doc) -- orientation is
            # not applicable to these formats at all.
            continue

        aspect = round(w / h, 3) if h else ""

        if orientation == 1:
            status = "already normal"
            already_normal += 1
            hint = ""
        elif orientation in range(2, 9):
            status = "auto-correctable"
            auto_correctable += 1
            hint = ""
        else:
            status = "needs eyes (missing or invalid EXIF orientation)"
            needs_eyes += 1
            hits = face_orientation_hint(full)
            hint = ",".join(str(d) for d in hits) if hits else ("n/a (no face detector support for this format)" if hits is None else "no face detected at any rotation")

        results.append({
            "archive_id": ident, "filepath": rel, "width": w, "height": h,
            "aspect_ratio": aspect, "exif_orientation": orientation if orientation is not None else "",
            "face_hint_degrees": hint, "status": status,
        })

        if (i + 1) % 50 == 0:
            print(f"  ...checked {i+1}/{len(rows)}", flush=True)

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["archive_id", "filepath", "width", "height", "aspect_ratio", "exif_orientation", "face_hint_degrees", "status"])
        w.writeheader()
        w.writerows(results)

    print()
    print(f"total rows: {len(results)}")
    print(f"already normal: {already_normal}")
    print(f"auto-correctable: {auto_correctable}")
    print(f"needs eyes: {needs_eyes}")
    print(f"missing local files: {missing_files}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
