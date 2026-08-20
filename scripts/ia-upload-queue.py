#!/usr/bin/env python3
"""Uploads approved.csv rows to Internet Archive one at a time, with backoff,
resumable state, and a full run log. Matches internal/review/test-15/upload_batch.sh
conventions (ia binary path, config file, subject tags).

Usage:
  PYTHONWARNINGS=ignore python3 scripts/ia-upload-queue.py approved.csv [--delay 240]
  PYTHONWARNINGS=ignore python3 scripts/ia-upload-queue.py approved.csv --only "path/to/file.jpg"

--only <filepath>: restricts the run to the single row whose filepath column
exactly matches the given value, and skips every other row -- same code
path, same license/rights handling, same state/log files, as a batch run.
This is the supported way to upload one item by hand; it exists so there is
no reason left to call `ia upload` directly and bypass these guards.

approved.csv columns (header required):
  filepath,title,description,creator,license,subject_tags,event,location,created_year,rights_owner,rights_statement
  subject_tags: semicolon-separated, e.g. "Queerhana;queer activism;Tel Aviv"
  license: required per row. Recognised values:
    - one of the 7 CC 4.0 labels (e.g. "CC BY-NC-SA 4.0") -- mapped to its
      real CC URL via LICENSE_URL_BY_LABEL and sent as IA's licenseurl. The
      literal label text is never sent to IA as licenseurl.
    - "all rights reserved" -- no licenseurl is sent; instead IA's `rights`
      field is set from the row's rights_statement column. If rights_statement
      is empty on such a row, the row is skipped and logged -- never uploaded
      with a bare rights-reserved claim and no statement.
    Any other value (including empty/missing) is skipped and logged as an
    error -- there is no default license and nothing is guessed.
  rights_owner: optional per row; sent to IA as the rights_owner metadata
  field verbatim when present.
  rights_statement: required only when license is "all rights reserved";
  ignored otherwise. Sent to IA as the `rights` metadata field verbatim.

Safe to kill and rerun: progress is tracked in upload-state.json (same
directory as approved.csv) and every attempt is appended to upload-log.csv.
Items already marked "done" or "failed" are never re-attempted. Items marked
"deferred" (all retries within a run were throttled, not a genuine error)
ARE re-attempted on the next run -- a throttle is temporary, so it must never
be treated as permanent.
"""
import argparse, csv, json, os, re, subprocess, sys, time
from datetime import datetime, timezone

IA_BIN = os.path.expanduser("~/Library/Python/3.9/bin/ia")
IA_CFG = "internal/ia.ini"
MAX_RETRIES = 6
BACKOFF_BASE = 60  # seconds; exponential: 60, 120, 240, 480, 960 -- IA's spam
                    # heuristic needs real cooling time, not a quick retry

# Inverse of build-catalog.py's LICENSE_LABELS -- keep the two in sync.
LICENSE_URL_BY_LABEL = {
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-ND 4.0": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-NC 4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-SA 4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-NC-ND 4.0": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}

# Separate recognised value, handled outside LICENSE_URL_BY_LABEL on purpose --
# it sends no licenseurl at all, so it must never be merged into that map.
ALL_RIGHTS_RESERVED_LABEL = "all rights reserved"

MEDIATYPE_BY_EXT = {
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".mpg": "movies", ".mpeg": "movies", ".mp4": "movies", ".mov": "movies",
    ".pdf": "texts", ".odt": "texts", ".doc": "texts", ".docx": "texts",
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


def load_state(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_state(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    os.replace(tmp, path)  # atomic, safe against being killed mid-write


def append_log(path, row):
    is_new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["identifier", "status", "timestamp", "response"])
        w.writerow(row)


def build_upload_cmd(identifier, row):
    ext = os.path.splitext(row["filepath"])[1].lower()
    mediatype = MEDIATYPE_BY_EXT.get(ext, "data")
    cmd = [
        IA_BIN, "--config-file", IA_CFG, "upload", identifier, row["filepath"],
        "-m", f"mediatype:{mediatype}",
        "-m", f"title:{row['title']}",
    ]
    if row.get("license"):
        # Real CC URL only -- rows using "all rights reserved" leave this
        # unset and carry a rights_statement instead (see below).
        cmd += ["-m", f"licenseurl:{row['license']}"]
    if row.get("rights_statement"):
        cmd += ["-m", f"rights:{row['rights_statement']}"]
    if row.get("description"):
        cmd += ["-m", f"description:{row['description']}"]
    if row.get("creator"):
        cmd += ["-m", f"creator:{row['creator']}"]
    if row.get("rights_owner"):
        cmd += ["-m", f"rights_owner:{row['rights_owner']}"]
    if row.get("event"):
        cmd += ["-m", f"event:{row['event']}"]
    if row.get("location"):
        cmd += ["-m", f"location:{row['location']}"]
    if row.get("created_year"):
        cmd += ["-m", f"year:{row['created_year']}"]
    for tag in (row.get("subject_tags") or "").split(";"):
        tag = tag.strip()
        if tag:
            cmd += ["-m", f"subject:{tag}"]
    return cmd


def is_throttle_error(output):
    signals = ("spam", "reduce your request rate", "rate limit", "503", "slow down")
    low = output.lower()
    return any(s in low for s in signals)


def upload_one(identifier, row, log_path):
    last_was_throttle = False
    for attempt in range(1, MAX_RETRIES + 1):
        cmd = build_upload_cmd(identifier, row)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            append_log(log_path, [identifier, "success", now_iso(), output.strip()[:500]])
            return "done", None
        last_was_throttle = is_throttle_error(output)
        status = "throttled" if last_was_throttle else "error"
        append_log(log_path, [identifier, f"retry_{attempt}_{status}", now_iso(), output.strip()[:500]])
        if attempt < MAX_RETRIES:
            backoff = BACKOFF_BASE * (2 ** (attempt - 1))
            time.sleep(backoff)
    if last_was_throttle:
        # Temporary, not a real error -- deferred so a later run retries it,
        # never silently treated as permanently failed.
        append_log(log_path, [identifier, "deferred_final", now_iso(), "max retries exhausted, all throttled"])
        return "deferred", output.strip()[:500]
    append_log(log_path, [identifier, "failed_final", now_iso(), "max retries exhausted"])
    return "failed", output.strip()[:500]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--delay", type=float, default=240.0,
                     help="seconds to wait between successful uploads (default 240)")
    ap.add_argument("--only", metavar="FILEPATH",
                     help="upload only the row whose filepath column exactly matches this value")
    args = ap.parse_args()

    base_dir = os.path.dirname(os.path.abspath(args.csv_path)) or "."
    state_path = os.path.join(base_dir, "upload-state.json")
    log_path = os.path.join(base_dir, "upload-log.csv")

    state = load_state(state_path)

    with open(args.csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    if args.only:
        rows = [r for r in rows if r["filepath"] == args.only]
        if not rows:
            sys.exit(f"--only {args.only!r} matched no row in {args.csv_path}")

    for row_index, row in enumerate(rows):
        identifier = identifier_for(row["filepath"])
        entry = state.get(identifier)

        if entry and entry.get("status") in ("done", "failed"):
            continue

        # Consent gate. Only enforced when the column is actually present
        # in this CSV -- upload-input.csv (the translated copy fed to a
        # normal batch run) doesn't carry it, only approved.csv does. Was
        # previously enforced only by human review judgment before a row
        # ever reached approved.csv; this is the code-level backstop.
        if "consent_status" in row and (row.get("consent_status") or "").strip().lower() != "yes":
            state[identifier] = {"status": "failed", "error": "consent_status not yes", "timestamp": now_iso()}
            save_state(state_path, state)
            append_log(log_path, [identifier, "failed_final", now_iso(),
                                   f"consent_status={row.get('consent_status')!r} -- skipped, never uploaded without cleared consent"])
            continue

        license_val = (row.get("license") or "").strip()
        if not license_val:
            state[identifier] = {"status": "failed", "error": "missing license", "timestamp": now_iso()}
            save_state(state_path, state)
            append_log(log_path, [identifier, "failed_final", now_iso(),
                                   "empty/missing license in approved.csv row -- skipped, no default applied"])
            continue

        if license_val in LICENSE_URL_BY_LABEL:
            row["license"] = LICENSE_URL_BY_LABEL[license_val]
            row["rights_statement"] = ""  # CC row -- never send a rights field alongside licenseurl
        elif license_val.lower() == ALL_RIGHTS_RESERVED_LABEL:
            rights_statement = (row.get("rights_statement") or "").strip()
            if not rights_statement:
                state[identifier] = {"status": "failed", "error": "all rights reserved with no rights_statement", "timestamp": now_iso()}
                save_state(state_path, state)
                append_log(log_path, [identifier, "failed_final", now_iso(),
                                       "license='all rights reserved' but rights_statement column is empty -- skipped, nothing guessed"])
                continue
            row["license"] = ""  # no licenseurl for a rights-reserved row
            row["rights_statement"] = rights_statement
        else:
            state[identifier] = {"status": "failed", "error": "unrecognized license label", "timestamp": now_iso()}
            save_state(state_path, state)
            append_log(log_path, [identifier, "failed_final", now_iso(),
                                   f"license label {license_val!r} not in LICENSE_URL_BY_LABEL and not {ALL_RIGHTS_RESERVED_LABEL!r} -- skipped, nothing guessed"])
            continue

        if not os.path.exists(row["filepath"]):
            state[identifier] = {"status": "failed", "error": "file not found", "timestamp": now_iso()}
            save_state(state_path, state)
            append_log(log_path, [identifier, "failed_final", now_iso(), "file not found: " + row["filepath"]])
            continue

        status, error = upload_one(identifier, row, log_path)
        state[identifier] = {"status": status, "error": error, "timestamp": now_iso()}
        save_state(state_path, state)

        # No point pacing after the last row -- including the common
        # single-item / --only case, which used to wait out the full
        # --delay for nothing after its one upload finished.
        if status == "done" and row_index < len(rows) - 1:
            time.sleep(args.delay)

    done = sum(1 for v in state.values() if v.get("status") == "done")
    failed = sum(1 for v in state.values() if v.get("status") == "failed")
    deferred = sum(1 for v in state.values() if v.get("status") == "deferred")
    print(f"done={done} failed={failed} deferred={deferred} total_tracked={len(state)}")


if __name__ == "__main__":
    main()
