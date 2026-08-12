#!/usr/bin/env python3
"""Corrects licenseurl and rights_owner metadata on IA items that were
already uploaded before ia-upload-queue.py's fix for those two fields
(licenseurl was sent as label text instead of a URL; rights_owner was never
sent at all). Reads correct values from approved.csv per item, and touches
ONLY those two metadata keys via `ia metadata --modify` -- no other field
is ever written.

Scope: only items marked "done" in the main run's upload-state.json at the
time this script starts (a static snapshot -- rerun it later to pick up
items the main queue finishes afterward). Does not read or write the main
queue's state.json, and never calls anything that uploads a file.

Usage (do not run until told to):
  PYTHONWARNINGS=ignore python3 scripts/ia-correct-license-rights.py \
      internal/review/full-batch/upload-state.json \
      internal/review/full-batch/approved.csv \
      [--delay 45]

Resumable: progress tracked in correction-state.json next to this script's
own log (internal/review/full-batch/correction/), separate from the main
queue's files. Items already marked "done" here are skipped on rerun.
"""
import argparse, csv, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

IA_BIN = os.path.expanduser("~/Library/Python/3.9/bin/ia")
IA_CFG = "internal/ia.ini"
MAX_RETRIES = 5
BACKOFF_BASE = 30

OUT_DIR = "internal/review/full-batch/correction"
STATE_PATH = os.path.join(OUT_DIR, "correction-state.json")
LOG_PATH = os.path.join(OUT_DIR, "correction-log.csv")

LICENSE_URL_BY_LABEL = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-ND 4.0": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-NC 4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA 4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-NC-ND 4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def identifier_for(filepath):
    stem = os.path.splitext(os.path.basename(filepath))[0]
    return f"queerhana-{slugify(stem)}"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_state(state):
    os.makedirs(OUT_DIR, exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, STATE_PATH)


def append_log(row):
    os.makedirs(OUT_DIR, exist_ok=True)
    is_new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["identifier", "status", "timestamp", "response"])
        w.writerow(row)


def is_throttle_error(output):
    signals = ("spam", "reduce your request rate", "rate limit", "503", "slow down")
    low = output.lower()
    return any(s in low for s in signals)


def correct_one(identifier, license_url, rights_owner):
    cmd = [IA_BIN, "--config-file", IA_CFG, "metadata", identifier,
           "-m", f"licenseurl:{license_url}",
           "-m", f"rights_owner:{rights_owner}"]
    for attempt in range(1, MAX_RETRIES + 1):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            append_log([identifier, "success", now_iso(), output.strip()[:500]])
            return "done", None
        status = "throttled" if is_throttle_error(output) else "error"
        append_log([identifier, f"retry_{attempt}_{status}", now_iso(), output.strip()[:500]])
        if attempt < MAX_RETRIES:
            time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
    append_log([identifier, "failed_final", now_iso(), "max retries exhausted"])
    return "failed", output.strip()[:500]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("upload_state_path", help="main queue's upload-state.json (read-only snapshot)")
    ap.add_argument("approved_csv_path")
    ap.add_argument("--delay", type=float, default=45.0)
    args = ap.parse_args()

    upload_state = load_json(args.upload_state_path, {})
    done_identifiers = {k for k, v in upload_state.items() if v.get("status") == "done"}

    with open(args.approved_csv_path, newline="") as f:
        approved_rows = list(csv.DictReader(f))

    by_identifier = {}
    for row in approved_rows:
        by_identifier[identifier_for(row["filepath"])] = row

    correction_state = load_json(STATE_PATH, {})

    done = failed = skipped = 0
    for identifier in sorted(done_identifiers):
        entry = correction_state.get(identifier)
        if entry and entry.get("status") == "done":
            skipped += 1
            continue

        row = by_identifier.get(identifier)
        if not row:
            correction_state[identifier] = {"status": "failed", "error": "no matching approved.csv row", "timestamp": now_iso()}
            save_state(correction_state)
            append_log([identifier, "failed_final", now_iso(), "identifier not found in approved.csv"])
            failed += 1
            continue

        license_label = (row.get("cc_license") or "").strip()
        license_url = LICENSE_URL_BY_LABEL.get(license_label)
        rights_owner = (row.get("rights_owner") or "").strip()

        if not license_url or not rights_owner:
            correction_state[identifier] = {"status": "failed", "error": f"license_url={license_url!r} rights_owner={rights_owner!r}", "timestamp": now_iso()}
            save_state(correction_state)
            append_log([identifier, "failed_final", now_iso(), "missing/unrecognized license or rights_owner in approved.csv -- nothing guessed"])
            failed += 1
            continue

        status, error = correct_one(identifier, license_url, rights_owner)
        correction_state[identifier] = {"status": status, "error": error, "timestamp": now_iso(),
                                         "licenseurl": license_url, "rights_owner": rights_owner}
        save_state(correction_state)

        if status == "done":
            done += 1
            time.sleep(args.delay)
        else:
            failed += 1

    print(f"done={done} failed={failed} skipped_already_done={skipped}")


if __name__ == "__main__":
    main()
