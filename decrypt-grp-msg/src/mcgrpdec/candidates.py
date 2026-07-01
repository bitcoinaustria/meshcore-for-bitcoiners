"""Candidate channel-name generation for the brute-forcer.

MeshCore hashtag-room names are short, lowercase, ``a-z 0-9 -`` (dash not at the
ends and not doubled). The *entropy is the name*, so a dictionary pass plus a
short exhaustive sweep cracks the vast majority.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator

# Default brute-force alphabet: lowercase alphanumerics + hyphen (jkingsman's set).
DEFAULT_CHARSET = "abcdefghijklmnopqrstuvwxyz0123456789-"
DASH = "-"

# Seed list tried before any brute force: MeshCore defaults + this deck's world.
COMMON_NAMES = [
    "public", "test", "default", "home", "general", "chat", "lounge",
    "meshcore", "mesh", "lora", "node", "nodes", "local", "emergency",
    "bitcoin", "btc", "sats", "satoshi", "hodl", "nostr", "lightning", "ln",
    "bitcoin-at", "bitcoinaustria", "bitcoin-austria", "austria", "at",
    "vienna", "wien", "graz", "linz", "salzburg", "innsbruck", "tirol",
    "europe", "eu", "region", "radio", "ham", "aprs", "meshtastic",
]


def name_space_size(charset: str, length: int) -> int:
    return len(charset) ** length


def _dash_ok(name: str) -> bool:
    if not name:
        return False
    if name[0] == DASH or name[-1] == DASH:
        return False
    if DASH * 2 in name:
        return False
    return True


def iter_brute(
    charset: str = DEFAULT_CHARSET,
    min_len: int = 1,
    max_len: int = 6,
    *,
    enforce_dash_rules: bool = True,
) -> Iterator[str]:
    """Yield every candidate name of length ``min_len..max_len`` (CPU path)."""
    for length in range(min_len, max_len + 1):
        for tup in itertools.product(charset, repeat=length):
            name = "".join(tup)
            if enforce_dash_rules and DASH in name and not _dash_ok(name):
                continue
            yield name


def index_to_name(index: int, charset: str, length: int) -> str:
    """Map a linear index in ``[0, len(charset)**length)`` to a name.

    Digit ``j`` (least significant first) is ``charset[(index // base**j) % base]``.
    This is the exact mapping the GPU kernel uses, so host-side reconstruction of
    a GPU-reported hit matches the bytes the shader hashed.
    """
    base = len(charset)
    chars = []
    for _ in range(length):
        chars.append(charset[index % base])
        index //= base
    return "".join(chars)


def load_wordlist(path: str) -> list[str]:
    """Load a newline-delimited wordlist, deduped, order-preserving.

    Case is preserved — MeshCore hashes the exact name bytes, so ``Bitcoin`` and
    ``bitcoin`` are different channels. Put whatever case variants you want to try
    directly in the file.
    """
    seen: set[str] = set()
    out: list[str] = []
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            w = line.strip()
            if w and w not in seen:
                seen.add(w)
                out.append(w)
    return out


def dictionary_candidates(extra_words: list[str] | None = None) -> Iterator[str]:
    """The seed list plus optional extra words, with simple hyphenated pairs of
    the shortest seeds (cheap, catches ``bitcoin-austria``-style names)."""
    words = list(COMMON_NAMES)
    if extra_words:
        words.extend(extra_words)
    seen: set[str] = set()
    for w in words:
        if w not in seen:
            seen.add(w)
            yield w
