#!/usr/bin/env python3
"""Reads upload-log.csv, pulls metadata from IA for every successfully
uploaded identifier, and merges new entries into data/catalog.json.

Idempotent: an archive_id already present in catalog.json is never touched
again (existing hand-edited fields are never overwritten), and re-running
against the same log adds nothing new the second time.

Usage:
  PYTHONWARNINGS=ignore python3 scripts/build-catalog.py [upload-log.csv]
"""
import csv, json, os, subprocess, sys

IA_BIN = os.path.expanduser("~/Library/Python/3.9/bin/ia")
CATALOG_PATH = "data/catalog.json"
DEFAULT_LOG = "upload-log.csv"

MEDIATYPE_TO_FILE_TYPE = {"image": "image", "movies": "video", "texts": "pdf"}
SKIP_FILE_SUFFIXES = ("_meta.xml", "_files.xml", "_archive.torrent", "_reviews.xml", "_meta.sqlite")
# IA's own generated thumbnail. It's frequently tagged source="original" (not
# "derivative") when no OCR/derivative pipeline ran on the item, which made
# pick_remote_file() below pick it over the real uploaded file -- the modal's
# "full resolution" swap was then downloading this same small thumbnail a
# second time. Must be excluded by exact name, not a suffix.
SKIP_FILE_NAMES = ("__ia_thumb.jpg",)

# licenseurl -> short label, matching the format already used by the 12
# existing catalog.json entries (e.g. "CC BY-NC-SA 4.0"). Only the standard
# CC 4.0 URLs + CC0 are mapped; anything else is left unrecognized rather
# than guessed at.
LICENSE_LABELS = {
    "https://creativecommons.org/licenses/by/4.0/": "CC BY 4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/": "CC BY-SA 4.0",
    "https://creativecommons.org/licenses/by-nd/4.0/": "CC BY-ND 4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/": "CC BY-NC 4.0",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/": "CC BY-NC-SA 4.0",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/": "CC BY-NC-ND 4.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
}


def normalize_license_url(url):
    url = (url or "").strip().lower()
    url = url.replace("http://", "https://").replace("://www.", "://")
    if url and not url.endswith("/"):
        url += "/"
    return url


def license_label(url):
    return LICENSE_LABELS.get(normalize_license_url(url), "")


def extract_subject_tags(md):
    subj = md.get("subject")
    if not subj:
        return ""
    if isinstance(subj, list):
        return "; ".join(s.strip() for s in subj if s and s.strip())
    return str(subj).strip()


def successful_identifiers(log_path):
    ids = []
    seen = set()
    with open(log_path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "success" and row["identifier"] not in seen:
                ids.append(row["identifier"])
                seen.add(row["identifier"])
    return ids


def fetch_metadata(identifier):
    proc = subprocess.run([IA_BIN, "metadata", identifier], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def pick_remote_file(meta):
    for f in meta.get("files", []):
        name = f.get("name", "")
        if name in SKIP_FILE_NAMES or any(name.endswith(sfx) for sfx in SKIP_FILE_SUFFIXES):
            continue
        if f.get("source") == "original":
            return name
    # fallback: first non-derivative, non-thumbnail file
    for f in meta.get("files", []):
        name = f.get("name", "")
        if name not in SKIP_FILE_NAMES and not any(name.endswith(sfx) for sfx in SKIP_FILE_SUFFIXES):
            return name
    return ""


def extract_rights_statement(md):
    rights = md.get("rights")
    if not rights:
        return ""
    if isinstance(rights, list):
        return "; ".join(r.strip() for r in rights if r and r.strip())
    return str(rights).strip()


def build_entry(identifier, meta, next_id):
    md = meta.get("metadata", {})
    mediatype = md.get("mediatype", "")
    license_url = md.get("licenseurl", "")
    cc_license = license_label(license_url)
    rights_statement = extract_rights_statement(md)
    rights_owner = md.get("rights_owner", "")
    flags = []
    if not license_url:
        if rights_statement:
            # Rights-reserved item -- no CC license, but a real rights
            # statement exists. Surface it in cc_license's spot rather than
            # leaving the field blank.
            cc_license = rights_statement
        else:
            flags.append("cc_license missing in IA metadata (no licenseurl)")
    elif not cc_license:
        flags.append(f"unrecognized licenseurl ({license_url}) -- cc_license left blank, not guessed")
    if not rights_owner:
        flags.append("rights_owner missing in IA metadata")
    entry = {
        "id": str(next_id),
        "archive_id": identifier,
        "ia_file": pick_remote_file(meta),
        "file_type": MEDIATYPE_TO_FILE_TYPE.get(mediatype, mediatype or "file"),
        "title": md.get("title", ""),
        "description": md.get("description", ""),
        "created_year": md.get("year", "") or md.get("created_year", ""),
        "credit_text": md.get("creator", ""),
        "event": md.get("event", ""),
        "location": md.get("location", ""),
        "cc_license": cc_license,
        "cc_license_url": license_url,
        "rights_owner": rights_owner,
        "subject_tags": extract_subject_tags(md),
        # archivist-supplied historical context, filled in a later stage,
        # after upload; never populated from IA metadata.
        "context_note": "",
    }
    return entry, flags


def next_numeric_id(catalog):
    max_id = 0
    for item in catalog:
        try:
            max_id = max(max_id, int(item.get("id", 0)))
        except (TypeError, ValueError):
            pass
    return max_id + 1


def main():
    log_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOG

    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH) as f:
            catalog = json.load(f)
    else:
        catalog = []

    existing_ids = {item["archive_id"] for item in catalog if "archive_id" in item}

    added = 0
    flagged = []  # (archive_id, [flag messages]) -- entry still written, values never invented
    for identifier in successful_identifiers(log_path):
        if identifier in existing_ids:
            continue  # never clobber a hand-edited or already-cataloged entry
        meta = fetch_metadata(identifier)
        if meta is None:
            print(f"warn: could not fetch metadata for {identifier}, skipped", file=sys.stderr)
            continue
        entry, flags = build_entry(identifier, meta, next_numeric_id(catalog))
        catalog.append(entry)
        existing_ids.add(identifier)
        added += 1
        if flags:
            flagged.append((identifier, flags))

    if added:
        with open(CATALOG_PATH, "w") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
            f.write("\n")

    print(f"added={added} total_catalog_items={len(catalog)}")
    if flagged:
        print(f"flagged={len(flagged)} (written with blank field(s), not invented):")
        for identifier, flags in flagged:
            print(f"  {identifier}: {'; '.join(flags)}")


if __name__ == "__main__":
    main()
