#!/usr/bin/env python3
"""Generates grid contact sheets (40 thumbs/sheet) from the deduped staging
file set, split so faces.csv-flagged files and no-face files never share a
sheet. Reads staging-inventory.csv / duplicates.csv / faces.csv (all written
by earlier audit scripts) from the staging dir. Writes PNGs + index.csv
into <staging_dir>/review/ -- kept outside the git repo entirely, matching
where the other staging-derived audit CSVs already live.

Usage:
  python3 scripts/generate-contact-sheets.py [staging_dir]
  (defaults to ~/Documents/QHarchive-staging)
"""
import csv, os, sys
from PIL import Image, ImageDraw, ImageFont

PER_SHEET = 40
COLS, ROWS = 8, 5
THUMB_BOX = 150
LABEL_H = 18
PAD = 6
HEADER_H = 30
CELL_W = THUMB_BOX + PAD * 2
CELL_H = THUMB_BOX + LABEL_H + PAD * 2


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


def load_face_counts(staging_dir):
    faces_path = os.path.join(staging_dir, "faces.csv")
    counts = {}
    with open(faces_path, newline="") as f:
        for row in csv.DictReader(f):
            counts[row["filepath"]] = int(row["face_count"])
    return counts


def folder_of(relpath):
    parts = relpath.split(os.sep)
    return parts[0] if len(parts) > 1 else ""


def chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def draw_sheet(items, staging_dir, title, font):
    canvas = Image.new("RGB", (COLS * CELL_W, HEADER_H + ROWS * CELL_H), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((PAD, 6), title, fill="black", font=font)

    for idx, (index_id, relpath) in enumerate(items):
        r, c = divmod(idx, COLS)
        x = c * CELL_W
        y = HEADER_H + r * CELL_H
        try:
            with Image.open(os.path.join(staging_dir, relpath)) as im:
                im = im.convert("RGB")
                im.thumbnail((THUMB_BOX, THUMB_BOX))
                ox = x + PAD + (THUMB_BOX - im.width) // 2
                oy = y + PAD + (THUMB_BOX - im.height) // 2
                canvas.paste(im, (ox, oy))
        except Exception:
            draw.rectangle([x + PAD, y + PAD, x + PAD + THUMB_BOX, y + PAD + THUMB_BOX],
                            outline="red", width=2)
            draw.text((x + PAD + 4, y + PAD + THUMB_BOX // 2), "ERR", fill="red", font=font)

        draw.text((x + PAD, y + PAD + THUMB_BOX + 2), index_id, fill="black", font=font)

    return canvas


def main():
    staging_dir = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/Documents/QHarchive-staging")
    out_dir = os.path.join(staging_dir, "review", "sheets")
    index_path = os.path.join(staging_dir, "review", "index.csv")
    os.makedirs(out_dir, exist_ok=True)

    deduped = load_deduped_set(staging_dir)
    face_counts = load_face_counts(staging_dir)

    # only files that were actually run through face detection (images) are
    # eligible for a contact sheet -- non-image formats have no face verdict
    # to sort by and are excluded here, not guessed at.
    covered = [p for p in deduped if p in face_counts]
    skipped_no_face_data = len(deduped) - len(covered)

    covered.sort(key=lambda p: (folder_of(p), p))

    has_faces = [p for p in covered if face_counts[p] > 0]
    no_faces = [p for p in covered if face_counts[p] == 0]

    font = ImageFont.load_default()
    index_rows = []
    sheet_count = 0

    for group_name, group_files in (("face", has_faces), ("noface", no_faces)):
        for sheet_num, sheet_files in enumerate(chunk(group_files, PER_SHEET), start=1):
            sheet_count += 1
            sheet_name = f"{group_name}-{sheet_num:02d}"
            items = []
            for i, relpath in enumerate(sheet_files, start=1):
                global_i = len(index_rows) + 1
                index_id = f"{'F' if group_name == 'face' else 'N'}{global_i:04d}"
                items.append((index_id, relpath))
                index_rows.append([index_id, relpath, f"{sheet_name}.png", face_counts[relpath]])

            title = f"{sheet_name}  ({len(sheet_files)} items)"
            canvas = draw_sheet(items, staging_dir, title, font)
            canvas.save(os.path.join(out_dir, f"{sheet_name}.png"))

    with open(index_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["index_id", "filepath", "sheet", "face_count"])
        w.writerows(index_rows)

    face_sheets = len(list(chunk(has_faces, PER_SHEET)))
    noface_sheets = len(list(chunk(no_faces, PER_SHEET)))
    print(f"sheets={sheet_count} face_sheets={face_sheets} noface_sheets={noface_sheets} "
          f"face_files={len(has_faces)} noface_files={len(no_faces)} "
          f"skipped_no_face_data={skipped_no_face_data}")


if __name__ == "__main__":
    main()
