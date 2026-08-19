#!/usr/bin/env python3
"""Standing check: compares approved.csv against live IA metadata for every
item that appears in both. Report only -- never writes to IA, never edits
catalog.json or approved.csv.

Run this after any batch of IA metadata writes (corrections, backfills, the
correction sweep) and before pushing a catalog rebuild. A correction applied
to approved.csv does not reach IA on its own -- only a write via
ia-upload-queue.py or a direct `ia metadata --modify` does. This script is
the way to find out whether one side has drifted from the other.

Also reports corpus membership gaps: an archive_id in approved.csv with no
live IA item (never uploaded, or upload failed), and an archive_id on IA/in
catalog.json with no approved.csv row (entered the corpus outside the normal
review pipeline -- e.g. a pilot-era item, or a one-off upload).

Usage:
  PYTHONWARNINGS=ignore python3 scripts/reconciliation-audit.py [out.csv]
"""
import csv, json, os, re, subprocess, sys

IA_BIN = os.path.expanduser("~/Library/Python/3.9/bin/ia")
IA_CFG = "internal/ia.ini"
APPROVED_CSV = "internal/review/full-batch/approved.csv"
CATALOG_JSON = "data/catalog.json"
DEFAULT_OUT = "reconciliation-audit.csv"

LICENSE_LABELS = {
    "https://creativecommons.org/licenses/by/4.0/": "CC BY 4.0",
    "https://creativecommons.org/licenses/by-sa/4.0/": "CC BY-SA 4.0",
    "https://creativecommons.org/licenses/by-nd/4.0/": "CC BY-ND 4.0",
    "https://creativecommons.org/licenses/by-nc/4.0/": "CC BY-NC 4.0",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/": "CC BY-NC-SA 4.0",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/": "CC BY-NC-ND 4.0",
    "https://creativecommons.org/publicdomain/zero/1.0/": "CC0 1.0",
}
LICENSE_URL_BY_LABEL = {v: k for k, v in LICENSE_LABELS.items()}


def normalize_license_url(url):
    url = (url or "").strip().lower()
    url = url.replace("http://", "https://").replace("://www.", "://")
    if url and not url.endswith("/"):
        url += "/"
    return url


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def identifier_for(filepath):
    stem = os.path.splitext(os.path.basename(filepath))[0]
    return f"queerhana-{slugify(stem)}"


def norm_tags(s):
    if not s:
        return ""
    parts = s if isinstance(s, list) else str(s).split(";")
    parts = sorted(p.strip().lower() for p in parts if p and p.strip())
    return "; ".join(parts)


def norm_text(v):
    return "" if v is None else str(v).strip()


def fetch_metadata(identifier):
    proc = subprocess.run(
        [IA_BIN, "--config-file", IA_CFG, "metadata", identifier],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None, f"ia metadata exited {proc.returncode}"
    try:
        return json.loads(proc.stdout), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT

    with open(APPROVED_CSV, newline="") as f:
        approved_rows = list(csv.DictReader(f))
    approved_by_id = {identifier_for(r["filepath"]): r for r in approved_rows}

    with open(CATALOG_JSON) as f:
        catalog = json.load(f)
    catalog_ids = {e["archive_id"] for e in catalog}
    approved_ids = set(approved_by_id.keys())

    only_in_approved = sorted(approved_ids - catalog_ids)
    only_in_catalog = sorted(catalog_ids - approved_ids)
    both = sorted(approved_ids & catalog_ids)

    print(f"approved.csv rows: {len(approved_rows)} (unique identifiers: {len(approved_ids)})")
    print(f"catalog.json entries: {len(catalog)}")
    print(f"in both: {len(both)}")
    print(f"only in approved.csv (no live IA item found via catalog): {len(only_in_approved)}")
    for i in only_in_approved:
        print("  ", i, "->", approved_by_id[i]["filepath"])
    print(f"only in catalog.json (no approved.csv row): {len(only_in_catalog)}")
    for i in only_in_catalog:
        print("  ", i)

    FIELD_COMPARISONS = [
        ("title", "title", lambda md: norm_text(md.get("title"))),
        ("description", "description", lambda md: norm_text(md.get("description"))),
        ("event", "event", lambda md: norm_text(md.get("event"))),
        ("location", "location", lambda md: norm_text(md.get("location"))),
        ("created_year", "created_year", lambda md: norm_text(md.get("year"))),
        ("credit_text", "credit_text", lambda md: norm_text(md.get("creator"))),
        ("rights_owner", "rights_owner", lambda md: norm_text(md.get("rights_owner"))),
        ("subject_tags", "subject_tags", lambda md: norm_tags(md.get("subject"))),
    ]

    rows_out = []
    fetch_errors = []
    field_counts = {}

    for i, ident in enumerate(both):
        meta, err = fetch_metadata(ident)
        if err:
            fetch_errors.append((ident, err))
            continue
        md = meta.get("metadata", {})
        approved_row = approved_by_id[ident]

        for report_field, csv_key, extractor in FIELD_COMPARISONS:
            csv_val = norm_tags(approved_row.get(csv_key)) if report_field == "subject_tags" else norm_text(approved_row.get(csv_key))
            ia_val = extractor(md)
            if csv_val != ia_val:
                rows_out.append({"archive_id": ident, "field": report_field, "approved_csv_value": csv_val, "ia_value": ia_val})
                field_counts[report_field] = field_counts.get(report_field, 0) + 1

        csv_license_label = norm_text(approved_row.get("cc_license"))
        csv_license_url = LICENSE_URL_BY_LABEL.get(csv_license_label, "")
        ia_license_url_raw = norm_text(md.get("licenseurl"))
        ia_license_label = LICENSE_LABELS.get(normalize_license_url(ia_license_url_raw), "")

        if csv_license_label != ia_license_label:
            rows_out.append({"archive_id": ident, "field": "cc_license", "approved_csv_value": csv_license_label, "ia_value": ia_license_label})
            field_counts["cc_license"] = field_counts.get("cc_license", 0) + 1

        if normalize_license_url(csv_license_url) != normalize_license_url(ia_license_url_raw):
            rows_out.append({"archive_id": ident, "field": "cc_license_url", "approved_csv_value": csv_license_url, "ia_value": ia_license_url_raw})
            field_counts["cc_license_url"] = field_counts.get("cc_license_url", 0) + 1

        if (i + 1) % 50 == 0:
            print(f"  ...checked {i+1}/{len(both)}", flush=True)

    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["archive_id", "field", "approved_csv_value", "ia_value"])
        w.writeheader()
        w.writerows(rows_out)

    print()
    print(f"fetch errors: {len(fetch_errors)}")
    for ident, err in fetch_errors:
        print("  ", ident, err)
    print()
    print(f"total divergence rows: {len(rows_out)}")
    for field, count in sorted(field_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {field}: {count}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
