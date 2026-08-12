#!/usr/bin/env python3
"""Safety net for anything that bypassed ia-upload-queue.py (e.g. a manual
`ia upload` call): scans every archive_id in data/catalog.json, fetches its
live IA metadata, and reports items with a missing/malformed licenseurl, a
missing rights_owner, or missing subject tags.

Report only. Never modifies catalog.json, never modifies anything on IA.

Usage:
  PYTHONWARNINGS=ignore python3 scripts/audit-ia-metadata.py [catalog.json]

Run this before any push that includes new or corrected catalog entries.
"""
import json, subprocess, sys

IA_BIN = "/Users/ohohoh/Library/Python/3.9/bin/ia"
IA_CFG = "internal/ia.ini"
CATALOG_PATH = "data/catalog.json"

# Same set ia-upload-queue.py and build-catalog.py recognise -- keep in sync.
KNOWN_CC_URLS = {
    "https://creativecommons.org/licenses/by/4.0/",
    "https://creativecommons.org/licenses/by-sa/4.0/",
    "https://creativecommons.org/licenses/by-nd/4.0/",
    "https://creativecommons.org/licenses/by-nc/4.0/",
    "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "https://creativecommons.org/publicdomain/zero/1.0/",
}


def normalize_license_url(url):
    url = (url or "").strip().lower()
    url = url.replace("http://", "https://").replace("://www.", "://")
    if url and not url.endswith("/"):
        url += "/"
    return url


def fetch_metadata(identifier):
    proc = subprocess.run(
        [IA_BIN, "--config-file", IA_CFG, "metadata", identifier],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def main():
    catalog_path = sys.argv[1] if len(sys.argv) > 1 else CATALOG_PATH
    with open(catalog_path) as f:
        catalog = json.load(f)

    problems = []
    for entry in catalog:
        identifier = entry.get("archive_id")
        if not identifier:
            problems.append((identifier, ["catalog entry has no archive_id"]))
            continue

        meta = fetch_metadata(identifier)
        if meta is None:
            problems.append((identifier, ["could not fetch IA metadata (item missing or unreachable)"]))
            continue

        md = meta.get("metadata", {})
        issues = []

        license_url = md.get("licenseurl", "")
        rights = md.get("rights", "")
        if not license_url and not rights:
            issues.append("no licenseurl and no rights statement")
        elif license_url and normalize_license_url(license_url) not in KNOWN_CC_URLS:
            issues.append(f"licenseurl not a recognised CC 4.0/CC0 URL: {license_url!r}")

        if not (md.get("rights_owner") or "").strip():
            issues.append("missing rights_owner")

        subjects = md.get("subject")
        has_subjects = bool(subjects) if not isinstance(subjects, list) else any(s.strip() for s in subjects if s)
        if not has_subjects:
            issues.append("missing subject tags")

        if issues:
            problems.append((identifier, issues))

    print(f"audited {len(catalog)} catalog entries")
    print(f"problems found: {len(problems)}")
    for identifier, issues in problems:
        print(f"  {identifier}: {'; '.join(issues)}")


if __name__ == "__main__":
    main()
