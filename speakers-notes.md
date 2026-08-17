# Speaker's notes — MeshCore for Bitcoiners

Spoken cues, staging advice, and the fact-check provenance for the deck, in
slide order. The `.tex` keeps only short pointers here — when a slide's facts
or staging change, update this file in the same commit.

Last full fact-check: **2026-07-02** (all claims re-verified against primary
sources; LoRa time-on-air recomputed independently).

Upstream re-check: **2026-08-12** — current firmware is **1.17.0**
(2026-08-09); 1.17 is hardware/power/stability only, **no protocol change**, so
every "firmware 1.14+" statement in the deck still describes when a feature
shipped, not the current release. Re-verified live: `loop.detect` still
defaults to `off`, the threshold matrix is unchanged, and `path.hash.mode`
still defaults to `0` (1-byte) — the multibyte rollout really is still in
progress. New since the deck was written: the `flood.max.*` hop budget
(firmware 1.16) and the trademark opposition filing (both below).

LoRa prehistory added **2026-08-17** (v1.7): Cycleo/Semtech dates, the founding
patent, and the Knight/Vangelista publications verified against primary sources
that day — see "Before MeshCore — where LoRa comes from".

---

## Opening — before "The one-line version"

Put the stakes in the room *before* revealing the slide:

> "How many of you could send a message tonight if the cell network went
> down? … Keep your hand up if you could do it without asking permission."

The closing slide answers it (#bitcoin-wien is already up) — don't spoil that.

## Before MeshCore — where LoRa comes from (2 slides)

The prehistory of the layer *underneath* MeshCore, added because it is the
mirror image of Bitcoin's origin: **silicon first, paper later**. Slide 1 is
the company story, slide 2 is the "whitepaper" beat.

**Spoken lead-in** (after "The catch"):

> "MeshCore is two years old. The radio it runs on is fifteen — and its story
> is the exact opposite of Bitcoin's."

**Facts (verified 2026-08-17):**

- **Cycleo**, Grenoble (France). Nicolas Sornin and Olivier Seller started the
  work in **2009**, met François Sforza in **2010**, and the three founded the
  company. They did *not* invent chirp spread spectrum — CSS comes from radar
  and sonar (and bats/dolphins do it in nature); they applied it to cheap
  long-range data. (Semtech's own retelling, "A Brief History of LoRa".)
- **Semtech acquires Cycleo, 2012:** **$5 M cash at closing plus up to $16 M
  earn-out** over four years, per the press release of **2012-03-07**.
  *Discrepancy to know:* Semtech's blog says "May 2012" — announcement vs.
  close. The slide says just "2012".
- **The founding patent** (re-verified 2026-08-17, because "patented physical
  layer" is a load-bearing claim in the alertblock): US **8,406,275** B2
  "Communications system", inventor **François Sforza**, priority
  **2009-07-02**, filed 2010-03-09, granted 2013-03-26. Original assignee
  **Nanoscale Labs**, current assignee **Semtech International AG**. Legal
  status **active**, anticipated expiry **2031-04-23**. The claims cover
  **both ends** — "a modulator for generating a chirp signal" *and* "a
  demodulator for receiving a chirp signal". Independent corroboration from a
  peer-reviewed source, Vangelista's first page: *"The LoRa modulation is
  patented and has never been described theoretically"*, and on the patent
  itself: *"The patent [4], indeed, does not provide the details, in term of
  equations and signal processing."*
  *So yes — "patented" is literal, not rhetorical.* Two honest caveats if
  pushed: patents **expire** (this family runs out around 2031, after which the
  modulation is anyone's to implement), and Semtech **licenses** the IP rather
  than hoarding it (ST's STM32WL, ASR's ASR6601) — so it is patented and
  single-vendor-ish, not secret and locked.
- **LoRa Alliance, founded February 2015**, maintains **LoRaWAN** — the MAC /
  network layer. The **PHY was never part of it**. Vangelista, first page:
  *"Strictly speaking, LoRa is the physical layer of the LoRaWAN system, whose
  specification is maintained by the LoRa Alliance. The LoRa modulation is
  patented and has never been described theoretically."*
- **MeshCore (like Meshtastic) uses no LoRaWAN at all** — no network server, no
  join server, no DevEUI/AppKey provisioning, no operator. It drives the raw
  LoRa PHY and does its own mesh on top. That's the permissionless point: the
  *operator* model was never adopted, only the modem.
- **The fiat twist on the 2015 bullet** (the bold parenthetical). LoRaWAN is
  what a Bitcoin room instinctively recognises: a device is **registered**
  (DevEUI / JoinEUI / AppKey), **activated through a join server**, and its
  traffic runs through a **network server** somebody operates — telcos and
  cloud providers sell it as a subscription. Same radio, opposite politics:
  **MeshCore is cash, LoRaWAN is the card rails**. Say it as a joke, not a
  sneer — LoRaWAN is genuinely good at what it is for (metering, logistics).
  *Q&A trap:* "but The Things Network is free!" — true, TTN is a community
  network, but you still **register the device with a join server** and route
  through someone's infrastructure. Free account ≠ no issuer; it's the
  free-checking-account version of the same model, not cash.
- **2016 — the reverse engineering:** Matt Knight (with Balint Seeber),
  *"Decoding LoRa: Realizing a Modern LPWAN with SDR"*, GNU Radio Conference
  2016 — a **blind** analysis with an Ettus B210 and a Microchip RN2903 mote,
  released as the open-source GNU Radio module **`gr-lora`**
  (github.com/BastilleResearch/gr-lora).
- **2017 — the academic description:** Lorenzo Vangelista (University of
  Padova), *"Frequency Shift Chirp Modulation: the LoRa Modulation"*, IEEE
  Signal Processing Letters, DOI **10.1109/LSP.2017.2762960**. Claims
  "**the first rigorous mathematical signal processing description**".

**The technical core (the cropped formula on slide 2 — Eq. (15)/(16)):**
a symbol is a chirp cyclically shifted to one of 2^SF starting frequencies, so
SF bits ride per symbol ("the chirp is similar to a kind of a carrier" — hence
*frequency shift chirp* modulation, FSCM). Projecting the received signal onto
the basis reduces to **two steps**: (1) multiply sample-by-sample by
`e^(−j2π k²/2^SF)` — the **down-chirp** — and (2) take the **DFT** of the
result and pick the output index; the underbraced `d(nTs+kT)` in Eq. (16) *is*
the de-chirped vector. That's why a cheap MCU can demodulate it at all.
Performance result: same uncoded BER as FSK in AWGN, **better in a
frequency-selective channel** (the chirp sweeps the whole band and averages
the fading).

**Q&A ammo:**

- *"Is LoRa open now?"* No. LoRaWAN is an open spec (and ITU-T standardised);
  the **PHY is still Semtech IP**. What's open is the *understanding* — thanks
  to Knight and Vangelista — plus SDR implementations. Silicon still comes from
  Semtech or its licensees (ST's STM32WL packs the same SX126x radio IP; ASR's
  ASR6601 is a licensed second source).
- *"So MeshCore isn't really permissionless?"* Distinguish the layers: you need
  nobody's permission to *transmit* (licence-free ISM band) or to *join* (a
  keypair). You do depend on one vendor's chip design to *modulate*. That's a
  supply-chain dependency, not a gatekeeper — but it is the one layer of the
  stack you cannot fork.
- *"Why eight years?"* 2009 (Cycleo starts) → 2017 (the paper). Or "five years
  after Semtech bought it". Either framing is fine; don't say "eight years
  after the patent".
- *Image provenance:* the front page on the slide is page 1 of the accepted
  version of the IEEE paper, reproduced with author, title, venue and DOI
  credited — citation use in a non-commercial talk, same footing as the
  mokosmart diagrams in Appendix 2.

Sources: blog.semtech.com "A Brief History of LoRa: Three Inventors Share
Their Personal Story" · design-reuse.com/news/28706 (Semtech/Cycleo press
release, 2012-03-07) · patents.google.com/patent/US8406275B2 ·
pubs.gnuradio.org (GRCon 2016, "Decoding LoRa") ·
doi.org/10.1109/LSP.2017.2762960 (the paper itself, read in full)

## Origins of MeshCore

*(Slide was titled "Where it comes from" until 2026-08-17 — renamed because
"it" was ambiguous once the LoRa prehistory sits in front of it.)*

**The lead-in line — the lineage.** The slide opens with
**LoRa (2009, a chip) → Meshtastic (2020, a mesh) → MeshCore (2024)**: same
radio layer, a new network on top each time. Meshtastic was created by **Kevin
Hester in early 2020** (hobby repo from 2019) and is what MeshCore's authors
knew before rebuilding — LoRa P2P on ESP32 / nRF52840 boards, i.e. the *same*
cheap hardware. Say the chain out loud; it pays off the two LoRa slides and
sets up the MeshCore-vs-Meshtastic comparison later.
Source: en.wikipedia.org/wiki/Meshtastic.

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

**Where it stands now (verified 2026-08-12) — the fourth bullet.** The dispute
is *live* as you speak, which is the point of saying it out loud:

- **2026-03-29** Kirby files the UK mark in secret; confronted in April, he
  refuses to withdraw. **2026-04-10/11** the core team incorporates *MeshCore
  Technologies Limited* and counter-files. May–June: lawyers' letters, all
  demands refused; the opposition deadline is extended to **2026-07-17**.
- **2026-07-04** Powell and Cottle publish "Help Us Save MeshCore": ~**$18k**
  estimated legal costs, **>$15k already paid out of their own pockets**, and
  the crowdfunder standing at only ~$1.8k.
- **2026-07-28** "Thank You": the community funded it — large donations,
  many small ones, anonymous *manufacturer* donors, new GitHub sponsors. The
  UK lawyer **filed the opposition**; the mark is now in **opposed status**.
  No hearing date. Their line: *"the tech goes on regardless."*

Spoken framing for a Bitcoin room — the parallel is the *funding*, not just
the fork: nobody could capture the protocol (MIT), so the attack landed on the
only capturable thing, **the name** — and a voluntary whip-round defended it.
If asked "who wins?": genuinely unknown, it's with the UK IPO.

Sources: blog.meshcore.io/2026/07/04/help-us-save-meshcore ·
blog.meshcore.io/2026/07/28/thankyou

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
path is re-learned. Hard limit: the path field is capped at **64 bytes**
(`MAX_PATH_SIZE`), so max hops depend on the ID width — **64 / 32 / 21** at
1 / 2 / 3-byte path hashes (kiekr's "max 64 hops" is the 1-byte case).

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

**Q&A / marketing-myth ammo:** meshcore.at (features page) advertises "**AES-256
Verschlüsselung** … derselbe Standard wie Banken und Geheimdienste." It's wrong
on three counts, and we can *show* it: (1) it's **AES-128, not 256** — our own
decrypter uses a 16-byte key (`SHA256(secret)[:16]`), a 32-byte key wouldn't
decrypt; (2) the mode is **ECB**, which is precisely what banks/agencies do
*not* use (identical plaintext blocks → identical ciphertext — the ECB-penguin);
(3) "only digital noise on an SDR" is content-only — the **channel-id byte,
routing header, and adverts (identity + often location) go out in the clear**.
Live-demo beat: show their "AES-256" slide, then run our decrypter and point at
the plaintext channel-id byte + AES-128 decrypt. The honest version: content is
protected, but the security is your *password's* entropy, not the "256".

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

## Appendix 3 — loop detection

**Normal loop prevention (why the mesh doesn't echo by design):** every
packet is hashed (SHA-256 over payload type + payload) into a seen-packet
cache (`hasSeen()`), so a repeater forwards each flood exactly once; the
64-byte path field (`MAX_PATH_SIZE`) caps the hops at **64 / 32 / 21** for
1 / 2 / 3-byte IDs (strictly 63 at 1 byte — the `path_len` hop count
encodes 0–63); nearby repeaters also stagger retransmits with random
delays to dodge collisions.

**The storm:** one repeater running broken (forked/custom) firmware that
*modifies* the payload before forwarding changes the packet's hash — dedup
goes blind and the same message re-floods as "new", up to the hop
ceiling, over and over. Documented by the core team as actually happening
in the wild; `loop.detect` shipped in repeater firmware **1.14**
(March 2026) as the mitigation.

**The matrix** (drop a flood when the repeater's own ID already appears
N+ times in the path): `minimal` = 4/2/1 for 1/2/3-byte IDs; `moderate` =
2/1/1; `strict` = 1/1/1; **default `off`**. The thresholds scale with
collision probability: a 1-byte ID has 256 values, so "my ID is in the
path" is weak evidence at 1 byte and near-proof at 3 bytes.

**The hop budget (firmware 1.16, June 2026) — the fourth bullet.** Separate
from `loop.detect`: an explicit cap on how far a flood travels, rather than a
test for whether it is circling. `flood.max` = max flood hop count (0–64,
default **64**, i.e. the same ceiling the 64-byte path already imposes — so no
change unless an operator lowers it). `flood.max.advert` = the same for advert
packets, default **8** — this one *is* a real default, so adverts no longer
ride to the path-length ceiling. `flood.max.unscoped` = for traffic with no
region scope, default 64/`0xFF` (unset ≈ disabled); the docs pitch it as the
gentler alternative to `region denyf *` — set it to e.g. **3** and local
unscoped chatter still works while a noisy neighbour can't flood your region.
Q&A: yes, this partly overlaps the region code — region filtering fences by
*agreement*, the hop budget fences by *distance*, and unscoped packets carry no
region code to filter on, which is exactly the gap `flood.max.unscoped` closes.

**Why off by default (official):** the multibyte-path rollout is still in
progress; the blog tells operators to enable it if they see storms. The
slide's editorial is ours: `minimal` is all but false-positive-free (it
takes *four* 1-byte collisions on one path) while a single storm eats a
region's duty-cycle budget — arguably the default belongs at `minimal`.
Q&A nuance if pushed the other way: `strict` at 1-byte *would* false-drop
legitimate floods (≈ n/256 chance per relay that another repeater on an
n-hop path shares your ID) — that caution is presumably what "off" is
protecting; it just overshoots.

Sources: docs.meshcore.io/cli_commands ("Routing", `loop.detect`,
`flood.max` / `flood.max.advert` / `flood.max.unscoped`, re-checked
2026-08-12) · blog.meshcore.io "Release 1.16.0" (2026-06-06, where the
flood caps shipped) ·
blog.meshcore.io "Path Diagnostics Improvements" (2026-03-06) · DeepWiki
7.2 "Routing and Path Discovery" (the `hasSeen` dedup) ·
docs.meshcore.io/packet_format (`MAX_PATH_SIZE` 64 B, `path_len` 0–63) ·
nodakmesh.org "Path Hash Modes Explained" (the 64/32/21 table).

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
