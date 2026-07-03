# Speaker's notes — MeshCore for Bitcoiners

Spoken cues, staging advice, and the fact-check provenance for the deck, in
slide order. The `.tex` keeps only short pointers here — when a slide's facts
or staging change, update this file in the same commit.

Last full fact-check: **2026-07-02** (all claims re-verified against primary
sources; LoRa time-on-air recomputed independently).

---

## Opening — before "The one-line version"

Put the stakes in the room *before* revealing the slide:

> "How many of you could send a message tonight if the cell network went
> down? … Keep your hand up if you could do it without asking permission."

The closing slide answers it (#bitcoin-wien is already up) — don't spoil that.

## Where it comes from

Lead spoken, with the punchline first:

> "In 2026 someone tried to trademark MeshCore and ship secret AI-rewritten
> apps. Guess how that went."

Then the bullets.

**Facts (verified):** created by Scott Powell, late 2024; web/mobile clients
by Liam Cottle; firmware MIT-licensed; rebuilt from scratch, *not*
interoperable with Meshtastic. The 2026 split: promoter Andy Kirby filed the
MeshCore trademark on 2026-03-29 without telling the team and pushed
undisclosed AI-rewritten ("vibe coded") apps; the core team broke with him and
kept shipping at meshcore.io; Kirby kept meshcore.co.uk and the old Discord.

Sources: blog.meshcore.io/2026/04/23/the-split ·
meshcoreeurope.org "MeshCore Splits Over Trademark, AI Code, and Team
Breakdown" (2026-04-27) · lwn.net/Articles/1070218 ·
en.wikipedia.org/wiki/MeshCore

## The hardware

Prices are mid-2026 EU street prices: T1000-E ~40 EUR; Heltec LoRa32 V4 ~40
EUR (V4 is current, V3 still works); P1-Pro ~100 EUR **plus ~30 for the
antenna** (5 W panel + 4×18650 — Seeed markets it for continuous 24/7
operation, effectively indefinite with sunlight). All four run MeshCore
(supported-devices list on flasher.meshcore.io).

## Live on the mesh

If connectivity allows, **switch to the live observer/app for ~30 s** — a
real packet arcing across Vienna beats any screenshot. If not, say aloud:
"this is live right now."

## Routing (two slides: "flood once…" / "What always floods")

Source: **kiekr.app/meshcore-explained** (German, excellent plain-language
explainer — the two routing slides follow its structure).

**DM lifecycle:** first message to a new contact floods (no path known);
each repeater stamps its ID into the packet as it relays, so the route
accumulates in the packet itself. The recipient's ACK floods back carrying
that path; the sender stores it. Later DMs are source-routed along the
stored path — **each direction keeps its own path** (outbound and return may
differ). A failed direct route falls back to flooding automatically and the
path is re-learned. Hard limit: **max 64 hops**.

**Channels:** membership = knowing the shared key, no member list, no
sign-up. No single recipient ⇒ channel messages **always flood**, and there
is **no ACK** — offline recipients simply miss the message. Q&A nuance:
sender names in channels are unverified text (unlike DMs, which are
cryptographically tied to the contact's key).

**Adverts:** two modes — zero-hop (direct neighbours only, cheap) and flood
(region-wide via repeaters, expensive). Etiquette per kiekr: repeater
operators should disable periodic flood adverts, or at most every 168 h.

**Q&A ammo (region interaction):** a flood is scoped by the *sender's*
configured region, but the ACK returns under the *recipient's* region
setting — mismatched regions can silently break DM delivery even when the
outbound message arrives.

## The region transport code

**Construction (verified against the MeshCore source):**
region key = `SHA256(regionName)[:16]`; transport code = LE uint16 of the
first 2 bytes of `HMAC-SHA256(key, payloadType || payload)`, with
0x0000/0xFFFF nudged to 1/0xFFFE. Computed over the *encrypted* payload, so
repeaters filter by region without decrypting; recomputed per hop. Symmetric
and 2 bytes wide ⇒ a routing/airtime filter, not a signature.

Sources: meshcore-decoder `src/crypto/region-transport.ts` · DeepWiki 7.6
"Region Filtering and Transport Codes" · kiekr.app/why-regions (German —
the airtime argument: the duty-cycle budget is per repeater and shared by
*all* users, ~680 pkts/h ceiling at ~500–586 ms/packet; regions partition
that budget, so "pick the smallest region that covers your recipients")

**Austrian scheme** (meshcore-austria.at): `at` = Austria-wide; macro-regions
`at-west` / `at-ost` / `at-sued`; cities nest below, e.g. `at-w` = Vienna.

Repeaters usually have **several regions** configured (e.g. a Vienna repeater
relays `at` + `at-ost` + `at-w`) — that's how the nesting works in practice:
a packet is relayed if its code matches *any* of the repeater's regions.
Hence the slide's plural: "a match with their own region**s**".

## Throughput

**Stage the airtime figure as a reveal:** ask "how much airtime per minute is
a node legally allowed? … six seconds." The smallness is the hook.

**Regulatory (verified):** ERC 70-03 band "P" (869.4–869.65 MHz): 10% duty
cycle, up to 500 mW (+27 dBm) ERP; the lower 868.0–868.6 MHz sub-band is only
1% at 25 mW — MeshCore deliberately picks the generous one. Austria
implements ERC 70-03 via the national frequency plan. Q&A nuance: the duty
cycle is defined over a **1-hour window** (10% = 360 s/h), so "6 s per
minute" is a fair average, not a hard per-minute cap.

**Radio preset (re-verified 2026-07-02):** EU/UK **Narrow** =
**869.618 MHz, BW 62.5 kHz, SF 8, CR 4/8**. Primary source for Austria:
meshcore-austria.at/doku.php?id=start ("Funk Einstellungen"). Also
meshcore.ch/settings and chatters.io/meshcore-network-presets; consistent
with docs.meshcore.io/faq ("as of October 2025, many regions have moved to
the 'narrow' setting"). **869.525 MHz is the OLD wide preset / LoRaWAN RX2
frequency — don't put it back.** Both sit inside band P, so the duty-cycle
claim is unaffected. In the wild, observers also show **CR 4/5** on good
links (less FEC, ~1/3 less airtime).

**Time-on-air** (Semtech formula: 8-symbol preamble, explicit header, CRC,
LDRO off, at SF8/BW62.5/CR4-8): 16 B ≈ 0.25 s · 64 B ≈ 0.64 s · 184 B
(full payload) ≈ 1.62 s. At CR 4/5: ≈ 0.19 s … 1.05 s. So 6 s/min ⇒ ~24
short msgs/min down to ~4 full packets/min (~30/min tiny pings @ 4/5).
Effective bitrate ≈ 1 kbit/s — hence "roughly a 1980s modem".

**Bitcoin side (updated 2026-07):** ~3,000–4,000 tx/block (the 2022-era
2,000–3,000 undercounts today), 1 block/~10 min ⇒ ~5–7 tx/s ≈ 300–400
tx/min. The consensus cap is **4M weight units** (block *weight*, not a
"1 MB size") since SegWit.

Sources: The Things Network "Regional limitations of RF use" · rf.guru
"Meshtastic, MeshCore, 868 MHz and the Ham Radio Trap" · disk91.com 868 MHz
regulation overview · Semtech SX1261/2 datasheet (ToA formula)

## Channel hash / "not mining"

**Construction (verified against firmware + michaelhart/meshcore-decoder
`src/crypto/channel-crypto.ts`; jacksbrain.com "Hitchhiker's Guide to
MeshCore Cryptography"):** for a `#room`, key = `SHA256("#room")[:16]` (the
AES-128 key); channel id = `SHA256(key)[0]` (first byte). Cipher is
**AES-128-ECB + an HMAC-SHA256-derived 2-byte MAC** — *not* AES-256/CTR.
No salt, no key stretching.

## Hashtag rooms are brainwallets

Room names: lowercase alphanumerics + hyphens, ≤30 chars. **Every name under
7 chars is exhaustively brute-forced in ~90 s** on a 2023 laptop GPU
(100M+ keys/s); public WebGPU cracker:
github.com/jkingsman/meshcore-hashtag-cracker. Not an AES break — the
effective security is the entropy of the *name*. Hashtag rooms are
world-readable *by design* (the honest divergence from the Bitcoin footgun).
The default "Public" channel ships a **well-known key** (docs/faq.md).

## ASICs — and the SX1262

SX1262 runs the entire LoRa modem (chirp spread spectrum) in silicon; the MCU
just hands it bytes over SPI; sleep current ~1 µA. ST's STM32WL packs the
same SX126x radio IP onto an MCU die. An SDR *can* decode LoRa in software
(gr-lora et al.) — at orders of magnitude more power, which is why the slide
frames the chip as power, not impossibility. The analogy breaks on the
*reason*: a mining ASIC wins a competitive PoW race; the SX1262 is
fixed-function and just saves energy — no contest.

Sources: Semtech SX1261/SX1262 datasheet/product pages · blog.st.com (STM32WL)

## Time — advert anti-replay

The forward-in-time rule is scoped to **adverts** (self-announcements), keyed
per pubkey by `last_advert_timestamp` — *not* enforced on every data packet;
keep the slide's wording. "Timestamp must be greater than
last_advert_timestamp. If not, advert is rejected as possible replay attack"
(`src/helpers/BaseChatMesh.cpp`). Failure mode: a node reset with a wrong
clock silently stops appearing in discovery (documented in docs/faq.md).

Sources: DeepWiki (ripplebiz/MeshCore) 10.3 Troubleshooting · official FAQ

## The multi-byte routing hard fork

Verified (docs/faq.md): repeaters older than 1.14 repeat only 1-byte
path-hash packets and **silently drop** 2- and 3-byte ones — old nodes
*degrade* (miss the new traffic) rather than drop off entirely; hence the
slide says "fades off the mesh", not "falls off".

## Shortcomings

Sources for the added facts: jacksbrain.com "Hitchhiker's Guide" (static-ECDH
DMs → no forward secrecy; channel/#room key model) · localmesh.nl "MeshCore
encryption details" (AES-128; default public key) · docs.meshcore.io.

## Appendix 1 — packet anatomy

Verified against docs.meshcore.io/packet_format, DeepWiki 7.1 "Packet
Structure and Types", and michaelhart/meshcore-decoder. Max packet 255 B
(LoRa PHY); header 1 B (2 bits route type, 4 bits payload type, 2 bits
version); optional 4 B transport codes on transport routes; path ≤64 B;
payload ≤184 B. Skip unless the room likes wire formats.

---

## Q&A ammo — Bitcoin-side nuances behind the slides

Deliberately simplified on stage; know the full story if pressed:

- **Taproot:** P2TR outputs put a *tweaked x-only pubkey* on-chain directly —
  no hash. "Address = hash of the pubkey" holds for legacy/P2WPKH; the
  identity slide's break-note carries the caveat ("Taproot skips the hash").
- **Double-spend:** *infeasible*, not impossible — probabilistic finality; a
  majority-hashrate attacker can reorg; hence the slide's wording.
- **HASH160** = RIPEMD160(SHA256(x)) — a *shorter hash*, not truncation of a
  256-bit digest (true truncation in Bitcoin: base58check/bech32 checksums).
- **Hard fork** = rules *loosened*, so old nodes reject the new blocks (soft
  fork is the reverse). Two chains persist only if each keeps miners/users.
- **Lightning** gossips only the *public* channel graph — unannounced
  channels aren't in it.
- **Ledger vs wire:** "encryption: none" is about the ledger; the P2P
  transport can be encrypted since BIP-324 (2023+).
- **Block subsidy** in 2026: 3.125 BTC (post-April-2024 halving).
