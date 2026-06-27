# Changelog

A running log of this **talk** — what content the deck covers and how it
evolved, version by version. It's a changelog for slides, not code: entries
describe what changed *on stage* (sections, framing, facts, visuals), not just
file edits.

- **Versioning:** a git tag `vMAJOR.MINOR` cuts a release. CI
  (`.github/workflows/release.yml`) builds the PDF and attaches it to a
  [GitHub Release](https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases).
  Bump **MINOR** for content additions/reworks; reserve **MAJOR** (→ `v1.0`)
  for the first version actually delivered on stage.
- The built `meshcore-for-bitcoiners.pdf` is a release artifact (gitignored),
  not committed — grab it from the Release page.
- The Bitcoin Austria beamer style lives in its own repo and is pinned here as
  the `theme/` submodule; its own history is tracked
  [there](https://github.com/bitcoinaustria/latex-beamer-style-2026).

This format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **"Double SHA256 — but not mining"** — a new crypto section on the channel
  hash. The channel name is hashed, cropped to 16 bytes, and hashed again
  (`SHA256(SHA256(name)[:16])`), which *looks* like Bitcoin's double-SHA256.
  A side-by-side table contrasts the MeshCore channel hash, Bitcoin's
  txid/block-ID, and Bitcoin **mining** (construction, computed-once vs nonce
  search, difficulty target, purpose) to show the mining analogy breaks: no
  nonce search, no target, no contest. Names the parallel that *does* hold —
  a short one-way commitment plus truncation as a namespace trade-off (HASH160,
  txid prefixes), the same tension as the 1 B → 1–3 B routing prefix.
  Construction verified against the MeshCore source: for a `#room`, the AES-128
  key is `SHA256("#room")[:16]` and the channel id is the first byte of
  `SHA256(key)` — so the double-hash-with-cropping framing is exact.

### Fixed
- **Crypto table: group channels are AES-128, not AES-256.** Verified against
  the MeshCore firmware and the `meshcore-decoder` library (`AES-128-ECB` + an
  HMAC-SHA256 MAC) and the "Hitchhiker's Guide to MeshCore Cryptography". The
  `handoff` note that said "AES-256 in CTR mode" was wrong on both the key size
  and the mode.
- **"The 2-byte routing hard fork"** — the firmware 1.14+ multi-byte routing
  prefix is backward-incompatible: old firmware can't parse the new
  adverts/path hashes, so it's framed as a hard fork. Where it breaks: MeshCore
  has no consensus or ledger to fork — it's a coordinated firmware upgrade, not
  a persistent chain split.

### To do before stage
- **Verify the EU 868 MHz duty-cycle figure** before stating a number out loud
  (throughput slide is intentionally kept qualitative for now; there's a `TODO`
  comment in the `.tex` at the throughput section).
- Develop further from the draft — this is still a working draft built from
  `handoff-20260626.md`.

## [v0.3] — 2026-06-27

Show the real thing — break up the theory with app/website screenshots.

### Added
- **"Live on the mesh"** — a three-up screenshot gallery after the packet-route
  image: the observer's live map (828 nodes, packets arcing across Vienna), the
  public **#test** channel (signed adverts + ping/pong probes), and the
  line-of-sight planner (terrain + Fresnel zone, 6.7 km in Vienna).
- **"How a message reaches me"** — a #coffee message opened to show its metadata
  (path-hash size, SNR, hop count) alongside its hop-by-hop delivery path traced
  through known repeaters.
- **`\screenshotcard[width]{image}{caption}`** — reusable card macro (portrait
  image + caption beneath) so phone screenshots sit side by side on one slide.
- Five figures under `pix/` (observer live map, #test channel, line-of-sight,
  #coffee message, 7-hop path).

(Deck is now 22 pages.)

## [v0.2] — 2026-06-26

Tightened the technical comparison and the framing around it.

### Added
- **Crypto comparison table** — the old "crypto checked" bullet slide is now a
  proper side-by-side `\comparisontable` (Bitcoin vs MeshCore) along technical
  dimensions: curve(s), identity, signatures, encryption, the key's job, address
  reuse. Footnote on the routing-prefix size (1 byte originally → 1–3 bytes since
  firmware 1.14+). Drove a matching `\comparisontable` macro + demo table into
  the theme repo.

### Changed
- Reworded the divider before the crypto table from "Verified facts / use these"
  to **"Crypto facts / what's under the hood"** — the old framing didn't fit a
  side-by-side technical comparison.

## [v0.1] — 2026-06-26

First complete draft of the talk — end to end, buildable, releasable.

### Added
- **Deck scaffold:** `meshcore-for-bitcoiners.tex` (XeLaTeX/Beamer, 16:9), the
  Bitcoin Austria theme as the `theme/` submodule, `makefile`
  (build/view/watch/clean + submodule check), and CI — build-on-push artifact +
  release-on-tag.
- **MeshCore intro section** (Bitcoiners don't know MeshCore — introduce it
  before drawing parallels): what it is (off-grid LoRa messaging, licence-free
  ISM bands, the EU angle), where it comes from (grew out of Meshtastic; created
  by Scott Powell late 2024; Liam Cottle = clients; Andy Kirby = promoter;
  meshcore.io), the hardware (T1000-E companion, Heltec/Wio portable, SenseCAP
  Solar Node P1-Pro repeater ~130 EUR, RAK WisBlock DIY), and a MeshCore vs
  Meshtastic comparison.
- **Live packet-trace visual:** a full-bleed slide of a packet routed across
  Austria, captured from `logger-at.meshcore.observer`
  (`pix/observer-package-across-austria-20260626.png`).
- **Core thesis + bridge slides:** keypair-as-identity, the signing model
  (opposite jobs for the same keypair), throughput (consensus cap vs regulatory
  duty cycle), and two distinct Lightning analogies (route-along-a-path; and
  bootstrap-then-jump-layers) — each naming where the analogy breaks.
- **Closing slide** with links to meshcore.io and the live observer map.
- **`\bridgeslide{title}{bitcoin}{meshcore}{where-it-breaks}`** — talk-specific
  wrapper over the theme's `\comparisonslide`, defined in the deck preamble.
- **Project docs & tooling:** README + CLAUDE.md (both flag the submodule
  checkout prominently), SPECS.md, `handoff-20260626.md` (the brainstorm notes
  the talk is based on), and `generate-images/` (a `uv` project for AI image
  generation via fal.ai / Replicate).
- **Apache-2.0** license.

### Content corrections folded in during v0.1
- Founder/date fixed to **Scott Powell, late 2024** (was "Andy Kirby, early
  2025"); roles clarified (Cottle = clients, Kirby = promoter).
- Subtitle "permissionless **communication**" (was "identity") — better captures
  the scope.
- MeshCore launch framed as **late 2024** per Wikipedia, not "early 2025".

[Unreleased]: https://github.com/bitcoinaustria/meshcore-for-bitcoiners/compare/v0.3...HEAD
[v0.3]: https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases/tag/v0.3
[v0.2]: https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases/tag/v0.2
[v0.1]: https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases/tag/v0.1
