#!/usr/bin/env python3
"""Face detection only, no judgment. Runs over the deduped file set produced
by the staging audit (staging-inventory.csv + duplicates.csv) and writes
faces.csv with filepath, face count, confidence per detection.

Deduped set = every inventoried file, minus duplicate-cluster members that
were NOT marked as the suggested keeper in duplicates.csv.

Detection: OpenCV Haar cascade (bundled with opencv-python, no external
model download). Confidence is the cascade's rejectLevel weight, not a
calibrated probability -- treat it as a relative score only.

Only image formats (jpg/jpeg/png) are supported by this detector; other
formats in the deduped set are skipped and reported as a count, not guessed at.

Usage:
  python3 scripts/flag-faces.py [staging_dir]
  (defaults to ~/Documents/QHarchive-staging)
"""
import csv, os, sys
import cv2

IMAGE_EXT = {".jpg", ".jpeg", ".png"}
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


def load_deduped_set(staging_dir):
    inventory_path = os.path.join(staging_dir, "staging-inventory.csv")
    dupes_path = os.path.join(staging_dir, "duplicates.csv")

    with open(inventory_path, newline="") as f:
        all_paths = [row["path"] for row in csv.DictReader(f)]

    excluded = set()
    if os.path.exists(dupes_path):
        with open(dupes_path, newline="") as f:
            for row in csv.DictReader(f):
                if row.get("suggested_keeper") != "KEEP":
                    excluded.add(row["path"])

    return [p for p in all_paths if p not in excluded]


def detect_faces(cascade, abs_path):
    img = cv2.imread(abs_path)
    if img is None:
        return None  # unreadable/corrupt, not this script's job to judge -- just skip
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    boxes, _, weights = cascade.detectMultiScale3(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), outputRejectLevels=True
    )
    return list(weights)


def main():
    staging_dir = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/Documents/QHarchive-staging")
    out_path = os.path.join(staging_dir, "faces.csv")

    deduped = load_deduped_set(staging_dir)
    cascade = cv2.CascadeClassifier(CASCADE_PATH)

    rows = []
    skipped_unsupported = 0
    skipped_unreadable = 0

    for rel_path in deduped:
        ext = os.path.splitext(rel_path)[1].lower()
        if ext not in IMAGE_EXT:
            skipped_unsupported += 1
            continue
        abs_path = os.path.join(staging_dir, rel_path)
        weights = detect_faces(cascade, abs_path)
        if weights is None:
            skipped_unreadable += 1
            continue
        confidence = ";".join(f"{w:.3f}" for w in weights)
        rows.append([rel_path, len(weights), confidence])

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filepath", "face_count", "confidence"])
        w.writerows(rows)

    print(f"processed={len(rows)} skipped_unsupported_format={skipped_unsupported} "
          f"skipped_unreadable={skipped_unreadable} wrote={out_path}")


if __name__ == "__main__":
    main()
