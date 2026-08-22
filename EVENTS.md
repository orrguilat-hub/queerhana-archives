# Event Vocabulary — QueeRhaNA Archives

Canonical event names for the archive. Tracked in git (alongside `POLICIES.md`)
so this survives across machines/sessions.

**Future batches must reuse these exact strings for the same occasion, rather
than coining a new variant.** Lowercase house style, matching the site's own
use of "queerhana" — do not title-case.

## How these names are derived

**Event years and occasion splits come from EXIF capture dates, not from the
original review notes.** The notes written during review carried years that
were often wrong; where a note's year and the EXIF date disagreed, the EXIF
date was taken as authoritative and the name corrected. Several brand names
turned out to cover more than one occasion — separate dates months or years
apart sharing a name — and have been split accordingly.

Splitting rule: photographs within two to three days of each other are one
occasion (a multi-day festival or a run of related actions). A larger gap is a
separate occasion. Occasion names carry month and year; where two occasions of
the same brand fall in the same month, the day or day range is included.

EXIF is authoritative for dates, but not blindly: where a camera's date is
plainly wrong against what the event itself is (a Purim march cannot fall in
August), the EXIF date is treated as a camera misdate, the items stay with
their occasion, and their `created_year` is left blank rather than recording
the false year.

A caution on reading the original notes: a month name inside a note is a date,
not a description. The note "Mini Queerhana Purim March 2003" names Purim in
March 2003 — it does not describe a march.

**Independent corroboration for one occasion.** `no-pride queerhana under the
bridge` is dated by more than EXIF: in `wetransfer-024eb0(1)/DSCN0826a.jpg` the
date is spray-painted on the bridge pier itself, reading קוויר חנה 6.2003
(Hebrew: "Queerhana 6.2003"). This matches the EXIF capture date of 2003-06-27
across every item in the occasion, and contradicts the "2002" recorded in the
original review note. Where a date is written into the photograph like this it
outranks both EXIF and the notes.

**A separate, earlier under-the-bridge occasion in 2002 is known to exist.**
The nGbK invitation (`queerhana-qh-inv`) dates the first bridge gathering to
2002 — a gathering distinct from the 2003 occasion documented above, whose
own material is expected in a later batch. `no-pride queerhana under the
bridge, 2003` is therefore not the first bridge gathering, only the first for
which material has been catalogued so far; do not treat its name as implying
otherwise, and do not merge future 2002 material into it once it arrives.

## Canonical names

| Canonical name | EXIF date(s) |
|---|---|
| `no-pride queerhana under the bridge, 2003` | 2003-06-27 (corroborated in-frame — see above) |
| `queerhana furry tale, june 2005` | 2005-06-14 |
| `mini queerhana purim, march 2003` | 2003-03-21 (most items; a few carry a camera misdate of 2004-08-05 and are left without a `created_year`) |
| `allenbeach reclaim the streets action, 8 march 2003` | 2003-03-08 |
| `allenbeach reclaim the streets action, 15-18 march 2003` | 2003-03-15 .. 2003-03-18 |
| `pink communities coalition, 2009` | 2009-08-05 (some items; the rest undated) |
| `queerhana four-day festival, september 2002` | 2002-09-28 |
| `this is a free zone, ngbk berlin, 2017` | no EXIF (year from the material itself) |
| `timeout photoshoot (unpublished)` | 2006-12-24 |
| `haritz parties` | spans December 2008 and February 2009, plus undated items — see below on why this isn't split like allenbeach |
| `queerhana chuchu` | 2008-08-29 |
| `down to the atlantis queerhana` | no EXIF (ephemera) |

**The two allenbeach occasions are deliberately NOT merged, unlike haritz.**
Both `8 march 2003` and `15-18 march 2003` carry the same series framing (one
of the Allenbeach crew's reclaim-the-streets actions) and, by the splitting
rule above, are far enough apart in date to be separate occasions in their
own right — the date split stands. This is a different situation from
`haritz parties`: haritz is one long-running series of parties rather than a
set of individually dated actions, which is why its dated variants were
merged back into a single name (see Corrections applied) while allenbeach's
were not.

## Corrections applied

| Previous name | Corrected to |
|---|---|
| `allenbeach reclaim the streets action, 2002` | split into `8 march 2003` and `15-18 march 2003` |
| `no-pride queerhana under the bridge, 2002` | `no-pride queerhana under the bridge, 2003` (corroborated by text in the photographs, not EXIF alone) |
| `queerhana furry tale, july 2006` | `queerhana furry tale, june 2005` |
| `mini queerhana purim march, 2003` | `mini queerhana purim, march 2003` (the trailing "march" in the original note was the month, not a procession; not split — see the misdate note above) |
| `haritz parties` (pilot-era generic) | split into `december 2008` and `february 2009`, later merged back into a single `haritz parties` — the name now covers the ongoing party series rather than individually dated occasions |
| `fun fun funzine urban festival` | removed along with its sole item, `queerhana-off-the-grid` (deleted from IA) |

## Blank event field

`queerhana-dscn6163` is now the only item deliberately without an event name
— no occasion could be established for it, and none has been guessed.

## The location field

`location` records **where an item was made** — where the photograph was
taken, where the document was written or issued. It is a fact about the item,
not about its content.

A place used as a **subject tag** means something different: that the place is
what the item is *about*. A photograph taken in Tel Aviv is not tagged
`tel aviv` — the location field already carries that. An essay arguing about
Tel Aviv's public space, or an invitation to a Berlin venue, is tagged,
because there the place is the subject.

Where the two coincide, the location field carries it and the tag does not.
Never infer a location from a folder name. Where the place an item was made is
not established, leave the field blank — a blank field is correct, a wrong one
is not.

