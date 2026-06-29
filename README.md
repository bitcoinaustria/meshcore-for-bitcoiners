# MeshCore for Bitcoiners

> [!NOTE]
> 📄 **Prebuilt slide PDFs are published as [GitHub Releases](https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases/latest).**
> Just want to read the deck? Grab `meshcore-for-bitcoiners.pdf` from the
> [latest release](https://github.com/bitcoinaustria/meshcore-for-bitcoiners/releases/latest)
> — no need to clone or build anything. Each `v*` tag ships a new PDF.

A LaTeX **Beamer** talk (Bitcoin Austria) drawing the structural parallels
between **Bitcoin** and **MeshCore** — off-grid, permissionless messaging over
long-range **LoRa** radio — and honestly naming where each analogy breaks.

The through-line: *Bitcoin made money permissionless by replacing institutional
identity with a self-generated keypair; MeshCore makes **communication**
permissionless the same way.* But Bitcoin defends a scarce asset while MeshCore
relays only fleeting messages, so the two diverge in instructive ways — and the
talk leans into those breaks rather than glossing over them.

**Audience:** technically inclined Bitcoiners who don't (yet) know MeshCore.

## What the talk covers

**Intro — what MeshCore even is**

- The one-line version, and why a Bitcoiner should care; messaging without a
  network, on licence-free ISM bands
- The hardware (tens of euros) and how MeshCore differs from Meshtastic
  (source-routed, not flood-based)
- A real packet routed across Austria, plus live app / observer screenshots

**The parallels** — each paired with an honest *"where it breaks"*:

- **Identity is a keypair** — a self-issued identity replaces the SIM / call sign
- **The signing model** — the same keypair, opposite jobs (Ed25519 adverts,
  X25519 DMs)
- **Throughput** — Bitcoin's block-size cap vs the EU 868 MHz duty cycle, a
  *regulatory* throttle
- **Lightning** — routing along discovered paths, and bootstrap-then-jump-layers
- **Crypto facts** — secp256k1 vs Ed25519 / X25519, side by side
- **Double SHA256 — but not mining** — the channel-hash construction
- **Hashtag rooms are brainwallets** — name-derived keys and the public-oracle trap
- **What Bitcoin's consensus buys — and MeshCore skips** — Sybil resistance,
  incentives, state, and time / ordering
- **The region transport code** — geofencing the flood, bridged to SIGHASH
- **The 2-byte routing hard fork** — a backward-incompatible wire-format change
- **Backup:** anatomy of a MeshCore packet (source-routing, not flooding)

See [`CHANGELOG.md`](CHANGELOG.md) for how the talk evolved release to release.

## Build & develop

This is a XeLaTeX deck, with the Bitcoin Austria theme included as a **git
submodule**. See **[BUILDING.md](BUILDING.md)** for cloning (mind the
submodule!), building the PDF, the repo layout, and how releases work.

## License

**Apache-2.0** (see [`LICENSE`](LICENSE)), © Bitcoin Austria. The beamer theme
and the Blinker font are licensed (Apache-2.0 / SIL OFL 1.1) in the
[theme repository](https://github.com/bitcoinaustria/latex-beamer-style-2026).
