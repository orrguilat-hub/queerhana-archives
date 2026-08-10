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
on all 123 items in the occasion, and contradicts the "2002" recorded in the
original review note. Where a date is written into the photograph like this it
outranks both EXIF and the notes.

## Canonical names

| Canonical name | Items | EXIF date(s) |
|---|---|---|
| `no-pride queerhana under the bridge, 2003` | 123 | 2003-06-27 (corroborated in-frame — see below) |
| `queerhana furry tale, june 2005` | 40 | 2005-06-14 |
| `mini queerhana purim, march 2003` | 16 | 2003-03-21 (14 items; 2 more carry a camera misdate of 2004-08-05 and are left without a `created_year`) |
| `allenbeach reclaim the streets action, 8 march 2003` | 13 | 2003-03-08 |
| `allenbeach reclaim the streets action, 15-18 march 2003` | 9 | 2003-03-15 .. 2003-03-18 |
| `pink communities coalition, 2009` | 5 | 2009-08-05 (2 of 5; rest undated) |
| `queerhana four-day festival, september 2002` | 4 | 2002-09-28 |
| `this is a free zone, ngbk berlin, 2017` | 3 | no EXIF (year from the material itself) |
| `timeout photoshoot (unpublished)` | 2 | 2006-12-24 |
| `fun fun funzine urban festival` | 1 | no EXIF |
| `haritz parties, december 2008` | 1 | 2008-12-27 |
| `haritz parties, february 2009` | 1 | 2009-02-07 |
| `queerhana chuchu` | 1 | 2008-08-29 |

## Corrections applied

| Previous name | Corrected to |
|---|---|
| `allenbeach reclaim the streets action, 2002` | split into `8 march 2003` and `15-18 march 2003` |
| `no-pride queerhana under the bridge, 2002` | `no-pride queerhana under the bridge, 2003` (corroborated by text in the photographs, not EXIF alone) |
| `queerhana furry tale, july 2006` | `queerhana furry tale, june 2005` |
| `mini queerhana purim march, 2003` | `mini queerhana purim, march 2003` (the trailing "march" in the original note was the month, not a procession; not split — see the misdate note above) |
| `haritz parties` | split into `december 2008` and `february 2009` |

## Blank event field

7 items carry no event name:

- 4 marked "no event" during clustering, or had no note to cluster from.
- 3 lost their event when their cluster split and they carry no EXIF date to
  place them on an occasion: `atlantis-flyer-all.jpg`, `Haritz/shana pizoz1.jpg`,
  `Haritz/haritz_Loop_2.MPG`. These need a human to assign an occasion —
  do not guess one from folder name.

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

