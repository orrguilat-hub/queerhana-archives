# Lessons — QueeRhaNA Archives

Hard-won conclusions from building and maintaining this archive. Each entry exists because something went wrong or was nearly missed. Read this before touching the pipeline; re-deriving these costs hours.

Add to it when something new is learned. Do not remove entries because they seem obvious — they seemed obvious to whoever caused them, too.

---

## Identity

**`archive_id` is the stable identity. `id` is not.**
`id` is a sequence number assigned at build time by `build-catalog.py` and re-assigned on rebuild. Correcting two entries once moved them from 171/172 to 236/237 with no change in total count. Never use `id` for permalinks, cross-references, external links, or anything that must survive a rebuild. `archive_id` is the IA identifier: populated on all entries, globally unique, never reassigned.

**IA identifiers are permanent and cannot be renamed.**
`queerhana-coalition-statement-2009` holds a Pink Communities Coalition document — the prefix is an artifact of one IA account holding the whole archive, not a claim that a "Queerhana coalition" existed. Changing it would mean a new item and a dead URL. Display titles carry the correction instead.

**Never infer an IA identifier from a filename.**
`identifier_for()` derived identifiers from local filenames. Scratch files named `<archive_id>__<ia_file>` slugified into `queerhana-queerhana-dscn0663-dscn0663`, and `ia upload` silently created six new public items instead of replacing the intended ones. Replacements must state their target identifier explicitly. Replace mode must verify the identifier already exists and abort if it does not — an operation that can create when replacement was intended is a bug waiting for a distracted moment.

---

## Data flow

**IA metadata is the source of truth. `catalog.json` is a build artifact.**
`build-catalog.py` builds from IA. Any hand edit to `catalog.json` is erased by the next rebuild, silently. An `event` value hand-added to `queerhana-haritz-aali` survived until it didn't. An `excerpt` field hand-authored for two PDF items was wiped the same way and is still missing.

**`approved.csv` is pre-upload staging. Corrections made after upload stop there.**
Three separate corrections — the Nath Rogea spelling, an event value, a photographer credit — were made in `approved.csv` after their items were already on IA and never propagated. Each surfaced only because something adjacent was being touched. The reconciliation audit (`scripts/`, run post-write) is the only systematic way to find these. Run it after any batch of IA writes, not only when something looks wrong.

**Pilot-era items predate the description and tagging pass.**
Items uploaded before the pipeline matured carry generic boilerplate on IA — "Photograph from the QueeRhaNA Archives, Tel Aviv" — while `approved.csv` holds the real per-item text. For these, `approved.csv` is the *fresher* side, reversing the usual direction. Check which side is stale before syncing.

---

## Google Drive

**Every file exists twice.** A contributor original and a canonical copy in the archive account. Identical folder names in both trees (`This is a Free Zone`, `Historical visual materials`, `Visions`, `movie`, `Exhibition References`, `THIS IS FREE ZONE ngbk`), so an unfiltered scan catalogs everything twice.

**Dedupe on filename + byte size, not ownership.** Ownership works today — canonical copies are owned by `qharchives@gmail.com`, originals by contributor accounts — but breaks the moment a contributor transfers ownership or a new contributor arrives. Identical filename and identical byte count is what actually proves a copy. Never use the Drive file ID prefix (`1...` vs `0B...`); that reflects creation era, not canonicality.

**Drive timestamps are never a date source.** Canonical copies all carry `createdTime: 2026-07-06` — the copy date. `modifiedTime` preserves the original but is timezone-shifted and is a file mtime, not a capture date. EXIF is authoritative for dating.

---

## Images

**EXIF orientation catches only flag-based rotation.** Images rotated in the pixels carry no flag and are undetectable programmatically. An EXIF pass flagged five items that turned out correct and missed nineteen that were genuinely wrong. Face-detection hints across four rotations produced noise, not signal. The only reliable detector is a human looking at a contact sheet — build a click-to-mark review page rather than trying harder to automate it.

**IA auto-generates files that look like originals.** `pick_remote_file()` selected `__ia_thumb.jpg` and `<id>_meta.sqlite` as the source file for 13 items, because IA sometimes tags them `source: "original"`. The modal then served a 180px thumbnail as the full-resolution image. Exclude `__ia_thumb.jpg` by name and `_meta.sqlite` by suffix.

**IA caches derivatives.** After replacing a file, confirm `__ia_thumb.jpg` regenerated and that the live grid and modal show the new version. Use a cache-busting request. This is the step most likely to look done and not be.

---

## Display

**Internal review flags leak into public display.** The modal filters *falsy* values out of its field list, so `""` disappears but `"UNCONFIRMED"` renders as "Rights holder: UNCONFIRMED" — which it did, publicly, on two items. Review vocabulary and catalog vocabulary must stay separate. Scan for flag-shaped strings after any bulk metadata change.

**Absence is not data.** Never render "unknown", "n/a", or a placeholder for a missing field — omit the row. (Exception: `credit_text: "n/a"` on 46 items is a deliberate archivist decision, not a leak. Leave it.)

**Check new vocabulary against existing values before writing it.** "Queerhana Archive" was nearly introduced as a `rights_owner` value alongside an established `archive` used on 83 items. Near-duplicates fragment filtering and are hard to unpick later. Report distinct values with counts before adding a new one.

**Non-CC licences must survive the licence machinery.** One item is `In copyright — used by permission of nGbK`, with no `cc_license_url`. The empty-licence skip rule must not fire — the licence isn't missing, it has no URL. Never adjust licence text to fit the code; fix the code. Publishing a CC value on material whose rightholder never agreed to redistribution is the specific failure the per-item licence field exists to prevent.

---

## Working method

**Verify before asserting internals.** Prompts that name a field, identifier, or script behaviour should either be grounded in something seen in the current session, or instruct verification first. Both the `id` permalink bug and the stray-identifier incident came from confident instructions about unverified internals — and confidence in the prompt gave Claude Code no reason to question them.

**Checkpoint bulk operations after three items.** Nineteen replacements created six stray public items before halting. A three-item checkpoint costs minutes and would have caught it at one.

**A report-only reconnaissance pass is worth its cost.** The Batch 0 run found the local `index.html` stale, a whole batch already applied, two live defects on no list, and thirteen canonical events where the plan assumed eleven. Assumptions about repo state go stale between sessions faster than they feel like they should.

**Declining to guess is correct.** The Drive canonical rule was left documented as an open gap rather than fabricated from a plausible-looking pattern. A wrong rule written into documentation is worse than a known gap, because the next session trusts it.
