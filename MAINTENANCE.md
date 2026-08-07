# Maintenance Log

## 2026-08-07 — GitHub token rotation

- Old fine-grained PAT (`queerhana-push`, unused/stale) revoked.
- New fine-grained PAT: `queerhana-archive-2026`, scope: `queerhana-archives` repo only, Contents: Read and write.
- **Expires: 2026-11-05** (90 days from creation).
- Authenticated via `gh auth login` (token stored in system keychain, not in this repo).
- Full git history scanned for committed secrets during rotation — none found.

Planned: replace token auth with SSH key — removes expiry entirely. See project notes.
