# mcgrpdec — MeshCore group-message decrypter

Decrypt and brute-force **MeshCore group-channel** ("#hashtag room") messages.

Hashtag rooms are *brainwallets*: the AES-128 key is `SHA256("#name")[:16]`, with
no salt and no stretching, so the effective security is the **entropy of the room
name**. A captured packet is a public verification oracle (the 1-byte channel
hash + 2-byte MAC confirm a guess), so short names fall to offline search — the
same footgun a Bitcoiner knows from `SHA256("correct horse")` addresses. This
tool demonstrates that end to end. (Companion to the *MeshCore for Bitcoiners*
talk.)

## Crypto (verified against real packets)

```
key      = SHA256("#name")[:16]                 # AES-128 key
secret   = key || 16 zero bytes                 # 32-byte HMAC key
chash    = SHA256(key)[0]                        # public 1-byte channel id
cipher   = AES-128-ECB, NoPadding
mac      = HMAC-SHA256(secret, ciphertext)[:2]  # 2-byte tag over ciphertext
plaintext= <ts:u32 LE><flags:u8><utf-8 "Sender: message">
```

On-air packet: `header(1) | path-len(1) | path | chash(1) | mac(2) | ciphertext(16·k)`.
The meshcore.observer "raw" string is this packet with cosmetic spacing — paste
it as-is.

Validated bit-for-bit against a known public-channel vector (`🌲 Tree: ☁️`) and a
real `#test` packet — run `mcgrpdec selftest`.

## Install

Requires [`uv`](https://docs.astral.sh/uv/). From this directory:

```bash
uv sync                 # base (decrypt + CPU cracker)
uv sync --extra gpu     # + Vulkan GPU brute-force (wgpu, uses the Intel iGPU)
```

## Usage

```bash
# Decrypt when you know the channel:
uv run mcgrpdec decrypt "<raw hex>" --name test
uv run mcgrpdec decrypt "<raw hex>" --public        # the weak default channel
uv run mcgrpdec decrypt "<raw hex>" --key <32-hex>  # raw AES key

# Recover an unknown channel name (dictionary, then exhaustive brute force):
uv run mcgrpdec crack "<raw hex>"                    # engine=auto (GPU if available)
uv run mcgrpdec crack "<raw hex>" --max-len 7 --engine gpu
uv run mcgrpdec crack "<raw hex>" -j 8 --engine cpu  # CPU, 8 workers (0=all cores)
uv run mcgrpdec crack "<raw hex>" --wordlist words.txt --no-brute

# Pull the packet straight from a meshcore.observer logger (id or URL). This also
# anchors the timestamp filter to the capture time (first_seen):
uv run mcgrpdec crack    --observer e9847719c3d40dee
uv run mcgrpdec decrypt  --observer e9847719c3d40dee --name test

# Work a whole list of messages at once (shares the dictionary across them):
uv run mcgrpdec batch messages.txt --wordlist wordlists/combined.txt
uv run mcgrpdec batch messages.txt --brute        # also GPU-brute the unsolved

# How fast is the brute force on this machine?
uv run mcgrpdec bench --engine gpu --length 6
uv run mcgrpdec bench --engine cpu --length 5 -j 16

uv run mcgrpdec selftest
```

`decrypt` and `crack` take the same flags — `decrypt` just tries your
`--name`/`--key`/`--public` first and falls through to a crack if none match, so
brute-force options like `--max-len` work under either verb.

`<raw hex>` may be given literally, as `-` (read stdin), or `@file`.

### Message list (`batch`)

`messages.txt` — one entry per line, `#` comments allowed. An optional
`label = ` prefix names it; the value is raw hex, `obs:<id>`, or an observer URL:

```
test    = 150320 DD 2CD9 B9 E7 ...
vienna  = obs:e9847719c3d40dee
154F12 7F A1 ...
```

Prefer `obs:<id>` where you can: it fetches the exact ciphertext (no paste
errors) and anchors the timestamp filter to when the packet was seen.

### Throughput (this machine: Intel Panther Lake iGPU, Vulkan)

| engine | rate | len 6 | len 7 | len 8 |
|--------|------|-------|-------|-------|
| GPU (iGPU) | ~54 M keys/s | ~1.5 min | ~1 h | ~1.5 days |
| CPU (16 cores) | ~10 M keys/s | ~9 min | ~5.5 h | ~8 days |

(Times are for the full `#name`+`name` sweep of the 37-char alphabet. Length 9+
is infeasible by brute force — use wordlists for longer names.)

### Why the timestamp filter matters

The channel hash (1 byte) + MAC (2 bytes) is only a **24-bit** tag, so an
exhaustive search over billions of names throws up *collisions* — names that pass
the tag but are not the real channel. Their decrypted timestamp is essentially
random (often years in the future), whereas a real message is timestamped at its
capture time. `mcgrpdec` rejects any candidate whose timestamp falls outside a
window; `--observer` (or `--seen-time <unix|ISO> [--window <secs>]`) anchors that
window to when the packet was actually seen, which makes the first surviving hit
the answer.

## Acceleration

The exhaustive engine computes `SHA256("#"+name)[:16]` → `SHA256(key)[0]` over the
candidate space and confirms survivors with the 2-byte MAC.

- **GPU (default when available):** a Vulkan compute shader (`wgpu`, native — no
  browser) runs on this machine's Intel iGPU. `≤6`-char names in seconds.
- **CPU fallback:** multiprocessing over all cores (`hashlib`); fine for the
  dictionary pass and short brute force.

This is **not** an AES break — AES-128 is untouched. It only searches the *name*.
Inspired by [`jkingsman/meshcore-hashtag-cracker`](https://github.com/jkingsman/meshcore-hashtag-cracker)
(WebGPU); this is a local, native reimplementation.
