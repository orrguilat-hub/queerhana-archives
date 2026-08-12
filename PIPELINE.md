# Upload Pipeline — QueeRhaNA Archives

Tracked in git (alongside `EVENTS.md` and `POLICIES.md`) so this survives
across machines/sessions.

## Rule: never call `ia upload` by hand

Every upload — batch or single item — goes through
`scripts/ia-upload-queue.py`. It is the only code path that maps a
CC 4.0 label to a real `licenseurl`, handles `all rights reserved` rows via
`rights_statement`, and sends `rights_owner`. A manual `ia upload` call
bypasses all of it silently: the item still uploads, but with no license URL
and no rights owner, and nothing warns you.

This happened once already: `queerhana-logo` was uploaded by hand as a
one-off (to append it to an already-running batch without restarting the
queue) and sat with malformed metadata, unmerged into `catalog.json`, until
an audit caught it.

**To upload a single item, use `--only`:**

```bash
PYTHONWARNINGS=ignore python3 scripts/ia-upload-queue.py approved.csv \
    --only "path/to/file.jpg"
```

This runs the one matching row through the exact same license/rights
handling, state tracking, and logging as a full batch run — there is no
longer a reason to call `ia` directly for a single file.

## Rule: audit before every push

Before pushing any commit that touches `data/catalog.json`, run:

```bash
PYTHONWARNINGS=ignore python3 scripts/audit-ia-metadata.py
```

It scans every `archive_id` currently in `data/catalog.json`, fetches its
live IA metadata, and reports (never modifies) any item with:

- a missing or malformed `licenseurl` (and no `rights` statement either)
- a missing `rights_owner`
- missing subject tags

This is the safety net for anything that reached IA outside the queue —
including old items uploaded before these guards existed. A clean run is
required before pushing; if it reports anything, fix the underlying item's
metadata (via `scripts/ia-correct-license-rights.py` or a targeted
`ia metadata --modify`) before the push, not after.
