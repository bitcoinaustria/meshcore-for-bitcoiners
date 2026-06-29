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

### Fixed
- **Channel-key formula made consistent.** The "Joining `#bitcoin-at`" slide
  showed `SHA256(SHA256(name)[:16])` over the bare name, while the brainwallet
  slide hashes `#name` (with the `#`). The `#` *is* part of the input, so the
  derivation slide now reads `SHA256(SHA256(#name)[:16])` — both slides agree.
- **Region-key crop restored.** The region-transport-code bridge said the key is
  `SHA256(name)`; corrected to `SHA256(name)[:16]`, matching the channel-key crop
  and the verified source note.
- **Routing hard-fork divider retitled** ("The 2-byte routing hard fork" →
  "The multi-byte routing hard fork"): the prefix grows 1 → 1–3 bytes, and
  "2-byte" collided with the separate 2-byte region code.
- **Backup-slide note** corrected from "1-byte path hashes" to "1–3 byte path
  hashes" (the obsolete pre-1.14 width).

### Added
- **Two intro slides (from a full deck review).** **"The catch --- kilometres of
  range, bytes of bandwidth"**, right after the packet-across-Austria visual,
  names the long-range / tiny-pipe trade-off up front so the audience drops the
  "WhatsApp-over-radio" model early (the throughput bridge pays it off later);
  and **"What recurs --- and a promise"**, before "The core thesis", maps the
  recurring Bitcoin primitives and states the deck's honesty contract (every
  parallel drawn rigorously, every break named out loud).
- **"Your first five minutes on the mesh"** — an onboarding slide before the
  channel CTA: buy a companion board → install Liam Cottle's app and pair over
  Bluetooth → keypair generated on first run (back it up) → type a channel name
  to join. Turns the "permissionless, you just join" thesis into a concrete
  action the room can take that night.

### Changed
- **Thesis stated once, as a reveal.** "The core thesis" now opens with a
  callback ("we opened with the one-liner; here is the precise claim…") so it
  reads as escalation, not repetition of the hook slide.
- **Brainwallet slide reframed as a payoff** of the channel-hash slide ("we just
  saw the room key *is* SHA256 of the name…"); its alertblock trimmed to fit.
- **"advert" defined at first lean** (the signing model: "a node's signed *here
  is my key, here I am*"), and the three node **roles glossed** where named
  (companion = handset, repeater = always-on relay, room server = store-and-forward).
- **Seed-phrase / key-backup parallel** added to the identity bridge: no seed
  phrase, the key lives on the device — lose it and you lose the *handle*, but
  with no value at stake it's a re-announce, not a theft.
- **"Scarce airtime" turned into a callback** — the region-code slide now ties it
  back to the duty-cycle budget from the throughput slide, instead of
  re-introducing the constraint from scratch.
- **More links on the references slide**, including a new **"Hardware & radio"**
  group: the **Semtech SX1262** (the LoRa radio IC behind the ASIC slide — chirp
  spread spectrum in silicon) and **ST STM32WL** (the same SX126x radio IP on an
  MCU die). Also added **docs.meshcore.io/packet_format** (the on-wire format
  behind the backup slide) to the internals column.
- **"ASICs --- and the LoRa radio chip"** — a new `\bridgeslide` after the
  "not mining" slide, answering the natural Bitcoiner question *"does LoRa have
  ASICs too?"* It does: the LoRa PHY (chirp spread spectrum) runs in a dedicated
  radio IC — Semtech's **SX1262** (the modem is in hardware; the MCU just hands
  it bytes; ~µA asleep), the same chip in the deck's Heltec LoRa 32 V3. The
  analogy *breaks* on the **reason**: a mining ASIC wins a competitive PoW race
  (more efficiency → more reward, difficulty follows), while the SX1262 is
  fixed-function and just saves power — no contest, the ceiling is physics and
  the duty cycle. Verified against Semtech's SX1261/SX1262 product docs.
- **Closing call to action: "Join the Bitcoin channels on MeshCore."** A
  concrete join prompt just before the "Thank you" slide, listing the channels
  the audience can join on the spot: `#bitcoin` (no region, mesh-wide),
  `#bitcoin-at` (region `at`, Austria), and `#bitcoin-wien` (region `at-w`,
  Vienna). Reinforces the region-code concept (no region = mesh-wide; a region
  scopes the flood). Also corrected the region-code slide's `at-w` gloss from
  "western Austria" to **Vienna**, to match these channel names.
- **Backup slide: "Anatomy of a MeshCore packet"** — an *optional* deep-dive on
  the on-wire format (`[header][transport codes?][path_len][path][payload]`,
  ≤255 B; header bits = route/payload type + version; 1–3 byte path hashes; payload
  ≤184 B, advert is Ed25519-signed, group/text is channel-hash + 2-byte MAC +
  AES-128). Foregrounds the **core idea**: each relay *appends its own short
  router ID* to the path as it forwards, so the path *is* the route — a direct
  message carries the exact list of router IDs and only those repeaters relay it.
  That's **routing, not flooding** (vs Meshtastic rebroadcasting everywhere).
  Placed after the "Thank you" closing as a `[noframenumbering]` backup
  so it can be **skipped for a non-technical audience** and shown only on demand —
  self-contained, so skipping it breaks nothing. Ties together the region code,
  the 1–3 byte routing prefix, and the AES-128/MAC facts. Verified against
  `docs.meshcore.io/packet_format`, DeepWiki 7.1, and `michaelhart/meshcore-decoder`.
- **Intro rework for the target audience (technical Bitcoiners new to MeshCore).**
  Added an opening **"The one-line version"** hook slide right after the
  "What is MeshCore?" divider: a one-line mental model ("Bitcoin's move, applied
  to talking" — self-issued identity, peer relay) plus a **"Why a Bitcoiner
  should care"** callout (licensed spectrum, KYC'd telcos, the network as
  chokepoint — MeshCore routes around all three) *before* the mechanics. Also
  pulled the **"packet routed across Austria"** full-bleed visual up to right
  after "Messaging without the network", so the audience sees the real thing
  works early instead of after the Meshtastic comparison.
- **"What is a region code, and why?"** — a plain-language setup slide before the
  region-transport-code bridge. The audience are Bitcoiners new to MeshCore, so
  this explains the concept first: flooding wastes airtime → a *region* is an
  agreed name (e.g. `at-w`) hashed into a shared key → every packet carries a
  2-byte transport code → repeaters relay only matching codes, geofencing the
  mesh by agreement (no registry, no coordinates). Sets up the SIGHASH bridge
  that follows (the code commits to the encrypted payload).
- **"What Bitcoin's consensus buys --- and MeshCore skips"** — a new four-slide
  section (divider + four `\bridgeslide`s) flowing from one insight: Bitcoin
  defends a scarce asset, so it pays for heavy consensus machinery; MeshCore
  defends nothing scarce (fleeting messages), so it skips all of it. The four
  faces:
  - **Sybil resistance** — permissionless *without* proof-of-work. Answers the
    "so where's the security?" the mining slide opens: identity is a free
    Ed25519 keypair; the only brakes are physical (airtime/range) and social
    (repeater ACLs, admin passwords). No scarce asset → no PoW needed.
  - **Incentives** — paid miners (subsidy + fees, a fee market) vs. unpaid
    repeater operators on goodwill and etiquette; a commons with no fee market.
  - **State** — a permanent global ledger vs. channel messages that exist only
    as transmitted (offline = missed silently). Scoped to *channels* — DMs ACK
    and identities/contacts persist.
  - **Time** — one global order (what stops double-spend) vs. MeshCore's
    per-sender rule that **adverts must move forward in time**
    (`last_advert_timestamp`); a wrong clock after a reset gets your adverts
    silently dropped. **Verified** against the firmware behaviour via two sources
    independent of the "Hitchhiker's Guide" blog (DeepWiki's firmware annotation
    + the official FAQ's clock-not-set failure mode), and the claim was
    **scope-corrected** from "packets" to "adverts" so it stays watertight.
- **"Hashtag rooms are brainwallets"** — a new two-slide module (divider +
  two frames) on the most audience-recognizable Bitcoin parallel in the deck.
  A MeshCore `#room` derives its AES-128 key straight from the room name
  (`SHA256("#"+name)[:16]` — no salt, no key-stretching), which is structurally
  a Bitcoin **brainwallet** (`SHA256(passphrase)`). A side-by-side table makes
  the match: human-chosen low-entropy input, no stretching, deterministic, and —
  the deep point — a **free public verification oracle** (the blockchain for the
  brainwallet, the broadcast packet for the room) that turns offline guessing
  catastrophic. Concrete stat: every room name under 7 chars falls in ~90 s on a
  laptop GPU (100M+ keys/s); it's a dictionary attack, **not** an AES break.
  The honest divergence is voiced: lower stakes (confidentiality, not theft) and
  hashtag rooms are world-readable *by design* — which actually flatters MeshCore
  (it labels the room public; for private traffic use X25519/Ed25519 DMs or
  private channels with long random hex keys). Verified against the MeshCore
  source and the "Hitchhiker's Guide to MeshCore Cryptography".
- **WebGPU hashtag-room brute-forcer** added to the references slide
  (`jkingsman/meshcore-hashtag-cracker`) — the demonstrated tool behind the
  brainwallet slide's brute-force claim.
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

- **"References & further reading"** — a new penultimate slide collecting the
  links behind the deck: project home/docs/firmware source, the Austrian packet
  observer, and the internals/crypto sources (DeepWiki annotated internals incl.
  region filtering, the "Hitchhiker's Guide to MeshCore Cryptography", the
  `meshcore-decoder` library, and LocalMesh's encryption details).

### Fixed
- **Dropped stray German text on "How a message reaches me".** The path caption
  had a German parenthetical (*"Nachricht wurde wiederholt"*) left over from the
  screenshot; removed for an English-language deck.
- **"A hashtag room is a brainwallet" slide no longer overflows.** It had a
  redundant intro line, a 6-row table, a footnote, and an alertblock — too much
  vertical content, pushing off the bottom. Trimmed to a 5-row table and folded
  the brute-force/AES facts into the alertblock.
- **Hardware slide: Heltec LoRa 32 V3 price ~20 → ~40 EUR.** The ~20 EUR figure
  was the bare-board AliExpress price; EU retail for the 868 MHz board is around
  40 EUR (e.g. Eckstein-Shop.de lists it at €39.95). ~40 EUR is consistent with
  the deck's other EU-retail figures (T1000-E ~40 EUR, P1-Pro ~130 EUR).
- **Crypto table: group channels are AES-128, not AES-256.** Verified against
  the MeshCore firmware and the `meshcore-decoder` library (`AES-128-ECB` + an
  HMAC-SHA256 MAC) and the "Hitchhiker's Guide to MeshCore Cryptography". The
  `handoff` note that said "AES-256 in CTR mode" was wrong on both the key size
  and the mode.
- **"The region rides inside the message"** — a slide on MeshCore's region
  *transport code*. The 2-byte region code is an `HMAC-SHA256` of the region key
  (`SHA256(region name)[:16]`) over the packet payload, truncated to a
  little-endian uint16; repeaters recompute it per hop, over the *encrypted*
  payload, to decide whether to relay (geofencing the flood — no key exchange,
  no registry, agreement on the region name is the whole protocol). Bridged to
  Bitcoin **SIGHASH**: a signature commits to the transaction, so authorization
  is bound to the content and can't be lifted onto another message. Where it
  breaks: the region "key" is public-ish (anyone who knows the name can forge)
  and only 2 bytes wide — a flood-scoping/airtime filter, not a real signature;
  it binds *scope* to content, not *authorship*. Verified against the MeshCore
  source (`meshcore-decoder` `region-transport.ts`; DeepWiki region-filtering).
- **"The 2-byte routing hard fork"** — the firmware 1.14+ multi-byte routing
  prefix is backward-incompatible: old firmware can't parse the new
  adverts/path hashes, so it's framed as a hard fork. Where it breaks: MeshCore
  has no consensus or ledger to fork — it's a coordinated firmware upgrade, not
  a persistent chain split.

### Changed
- **Throughput slide now states the EU/Austria duty-cycle figure.** Resolves the
  long-standing `TODO`: MeshCore's EU default **869.525 MHz** falls in the
  **869.4–869.65 MHz** sub-band, which CEPT/ERC 70-03 (and ETSI EN 300 220-2,
  implemented in Austria) allows at a **10% duty cycle** and up to **500 mW
  (+27 dBm) ERP** — the generous high-power sub-band, not the 1%/25 mW one lower
  in the band. The "throttle is imposed, not a failure" framing stays; it now
  has a concrete number behind it.

### To do before stage
- **Sanity-check the 10% / 500 mW figure** against the current Austrian
  frequency plan before saying it out loud — it's verified against CEPT/ETSI
  sources but worth a final cross-check on stage night.
- **Decide: live-demo vs screenshot** the WebGPU hashtag-room brute-forcer on
  the brainwallet slide — live is higher-impact but depends on venue wifi/time.
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
