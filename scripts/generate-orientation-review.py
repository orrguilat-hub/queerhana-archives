#!/usr/bin/env python3
"""Generates review-orientation.html: a local-only, dense thumbnail grid of
every image item in data/catalog.json, grouped by event, for a human to scan
for wrong rotation. EXIF-based detection cannot catch pixel-rotated files
with no orientation signal, so this replaces further programmatic guessing.

Not deployed -- review-orientation.html is gitignored. Output is a review
aid, not a publishable page.

Usage:
  python3 scripts/generate-orientation-review.py
"""
import json, html

CATALOG_PATH = "data/catalog.json"
EVENTS_PATH = "data/events.json"
OUT_PATH = "review-orientation.html"


def main():
    catalog = json.load(open(CATALOG_PATH))
    events = json.load(open(EVENTS_PATH))
    event_order = [e if isinstance(e, str) else e.get("name", "") for e in events]

    images = [i for i in catalog if i.get("file_type") == "image"]

    groups = {}
    for item in images:
        ev = item.get("event") or "(no event)"
        groups.setdefault(ev, []).append(item)

    ordered_keys = [e for e in event_order if e in groups] + \
                   sorted(k for k in groups if k not in event_order)

    sections = []
    for ev in ordered_keys:
        items = sorted(groups[ev], key=lambda i: i["archive_id"])
        cards = []
        for item in items:
            aid = item["archive_id"]
            title = html.escape(item.get("title", ""))
            thumb = f"https://archive.org/services/img/{aid}"
            cards.append(f'''
        <div class="cell">
          <img src="{thumb}" loading="lazy" alt="{title}">
          <div class="label">{html.escape(aid)}</div>
        </div>''')
        sections.append(f'''
      <section>
        <h2>{html.escape(ev)} <span class="count">({len(items)})</span></h2>
        <div class="grid">{''.join(cards)}</div>
      </section>''')

    html_out = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Orientation review — local only, not deployed</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #111; color: #eee; margin: 0; padding: 16px; }}
  h1 {{ font-size: 18px; }}
  .warn {{ color: #ff6; font-size: 13px; margin-bottom: 20px; }}
  h2 {{ font-size: 14px; margin: 24px 0 8px; border-bottom: 1px solid #444; padding-bottom: 4px; }}
  .count {{ color: #888; font-weight: normal; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .cell {{ width: 140px; }}
  .cell img {{ width: 140px; height: 140px; object-fit: contain; background: #222; display: block; }}
  .label {{ font-size: 9px; font-family: monospace; color: #aaa; word-break: break-all; padding: 2px 0; }}
</style>
</head>
<body>
<h1>Orientation review — {len(images)} image items</h1>
<p class="warn">LOCAL ONLY. Not deployed, not linked from the site. Scan for wrong rotation, note archive_id + degrees needed.</p>
{''.join(sections)}
</body>
</html>
'''
    with open(OUT_PATH, "w") as f:
        f.write(html_out)
    print(f"wrote {OUT_PATH}: {len(images)} images across {len(ordered_keys)} event groups")


if __name__ == "__main__":
    main()
