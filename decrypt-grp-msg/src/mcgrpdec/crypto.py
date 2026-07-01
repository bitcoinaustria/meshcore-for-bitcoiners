"""MeshCore group/channel ("#hashtag room") message crypto.

Verified bit-for-bit against a known-answer vector (see tests/test_crypto.py):
the public-channel packet decodes to sender ``🌲 Tree`` / message ``☁️``.

Scheme (from MeshCore firmware + michaelhart/meshcore-decoder):

    key      = SHA256(<name>)[:16]                 # 16-byte AES-128 key
    secret   = key || (16 zero bytes)              # 32-byte "channel secret"
    chash    = SHA256(key)[0]                       # 1-byte public channel id
    cipher   = AES-128-ECB, NoPadding
    mac      = HMAC-SHA256(secret, ciphertext)[:2] # 2-byte tag, over ciphertext
    plaintext= <ts:u32 LE><flags:u8><utf-8 text\0> # text is "Sender: message"

The one thing the public sources disagree on is whether ``<name>`` includes the
leading ``#``. We do not guess: :func:`candidate_keys` yields *both* derivations
and the MAC decides which is real.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Well-known "public" channel key (the deliberately-weak default everyone holds).
PUBLIC_CHANNEL_KEY = bytes.fromhex("8b3387e9c5cdea6ac9e5edbaa115cd72")


def key_from_name(name: str, *, hash_prefix: bool = True) -> bytes:
    """Derive the 16-byte AES key from a channel name.

    ``hash_prefix`` controls whether the leading ``#`` is part of the hashed
    string (``SHA256("#name")`` vs ``SHA256("name")``). Try both — see
    :func:`candidate_keys`.
    """
    s = name if name.startswith("#") else (("#" + name) if hash_prefix else name)
    return hashlib.sha256(s.encode("utf-8")).digest()[:16]


def candidate_keys(name: str) -> list[tuple[str, bytes]]:
    """Both plausible key derivations for a bare name, labelled.

    Returns ``[("#"+name, key1), (name, key2)]`` (deduped if ``name`` already
    starts with ``#``).
    """
    out: list[tuple[str, bytes]] = []
    seen: set[bytes] = set()
    for label in (name if name.startswith("#") else "#" + name, name.lstrip("#")):
        k = hashlib.sha256(label.encode("utf-8")).digest()[:16]
        if k not in seen:
            seen.add(k)
            out.append((label, k))
    return out


def channel_hash(key: bytes) -> int:
    """The 1-byte public channel id = first byte of SHA256(key)."""
    return hashlib.sha256(key).digest()[0]


def channel_secret(key: bytes) -> bytes:
    """32-byte channel secret used as the HMAC key: key || 16 zero bytes."""
    return key + b"\x00" * 16


def compute_mac(key: bytes, ciphertext: bytes) -> bytes:
    """2-byte MAC = HMAC-SHA256(channel_secret, ciphertext)[:2]."""
    return hmac.new(channel_secret(key), ciphertext, hashlib.sha256).digest()[:2]


def aes_ecb_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    """AES-128-ECB, no padding. ``ciphertext`` must be a multiple of 16 bytes."""
    dec = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    return dec.update(ciphertext) + dec.finalize()


@dataclass
class GroupMessage:
    """A decoded group-text plaintext."""

    timestamp: int
    flags: int
    sender: str | None
    text: str
    plaintext: bytes  # raw decrypted bytes (for debugging)

    def __str__(self) -> str:
        who = self.sender if self.sender is not None else "?"
        return f"[{self.timestamp}] {who}: {self.text}"


def parse_plaintext(pt: bytes) -> GroupMessage:
    """Split decrypted bytes into ``<ts:u32 LE><flags:u8><text>``.

    The text is conventionally ``"Sender: message"``; we split on the first
    ``": "`` when the prefix looks like a name (no bracket/colon chars),
    matching meshcore-decoder's heuristic.
    """
    timestamp = int.from_bytes(pt[0:4], "little")
    flags = pt[4] if len(pt) > 4 else 0
    text = pt[5:].split(b"\x00", 1)[0].decode("utf-8", "replace")
    sender: str | None = None
    body = text
    if ": " in text[:80]:
        pre, rest = text.split(": ", 1)
        if pre and not any(c in pre for c in "[]:"):
            sender, body = pre, rest
    return GroupMessage(timestamp, flags, sender, body, pt)


# Broad default timestamp gate (unix seconds): 2020-01-01 .. 2035-01-01.
TS_MIN_DEFAULT = 1_577_836_800
TS_MAX_DEFAULT = 2_051_222_400


def looks_like_plaintext(
    pt: bytes, *, min_ts: int = TS_MIN_DEFAULT, max_ts: int = TS_MAX_DEFAULT
) -> bool:
    """Cheap sanity check used to reject MAC/chash false positives.

    The 1-byte channel hash + 2-byte MAC is only a 24-bit tag, so across billions
    of brute-force candidates *collisions are expected*. A real message decrypts
    to a plausible unix timestamp (a hard discriminator — a false hit's timestamp
    is uniformly random, e.g. years in the future) and valid UTF-8 text. Anchor
    ``min_ts``/``max_ts`` to the packet's capture time to make this decisive.
    """
    if len(pt) < 5:
        return False
    ts = int.from_bytes(pt[0:4], "little")
    if not (min_ts <= ts <= max_ts):
        return False
    body = pt[5:].split(b"\x00", 1)[0]
    if not body:
        return False
    try:
        body.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def try_decrypt(
    key: bytes, chash: int, mac: bytes, ciphertext: bytes,
    *, min_ts: int = TS_MIN_DEFAULT, max_ts: int = TS_MAX_DEFAULT,
) -> GroupMessage | None:
    """Full verify+decrypt for one key. Returns the message or ``None``.

    Checks the 1-byte channel hash, then the 2-byte MAC, then decrypts and
    sanity-checks the plaintext against ``[min_ts, max_ts]``. With the window
    anchored to the packet's capture time, a surviving false positive is
    astronomically unlikely.
    """
    if channel_hash(key) != chash:
        return None
    if compute_mac(key, ciphertext) != mac:
        return None
    pt = aes_ecb_decrypt(key, ciphertext)
    if not looks_like_plaintext(pt, min_ts=min_ts, max_ts=max_ts):
        return None
    return parse_plaintext(pt)
