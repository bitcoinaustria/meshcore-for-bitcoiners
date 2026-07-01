#!/usr/bin/env python3
"""Build wordlists/combined.txt for the MeshCore hashtag-room cracker.

Pulls base words from the system dictionaries (English + Austrian/German
hunspell) plus a curated Bitcoin/Austria/mesh seed list, and emits case variants
(names are hashed case-sensitively). The generated .txt is gitignored — rebuild
it with:

    uv run python wordlists/build_wordlist.py

Sources are optional; missing ones are skipped with a warning.
"""

from __future__ import annotations

import os
import re

SOURCES = [
    "/usr/share/dict/american-english",
    "/usr/share/hunspell/de_AT.dic",
    "/usr/share/hunspell/de_DE.dic",
    "/usr/share/dict/cracklib-small",
]

SEEDS = """bitcoin btc austria oesterreich osterreich vienna wien wean graz linz salzburg
innsbruck tirol tyrol noe ooe donau moedling baden klosterneuburg krems tulln
meshcore mesh lora hodl satoshi sats nostr lightning ln plebs pleb bitcoinaustria
bitcoin-at bitcoin-austria familie freunde crew team group gruppe geheim secret
privat private notfall emergency funk radio ham aprs meshtastic node nodes relay
repeater bitcoiners orange stack einundzwanzig kraut server verein community treffen
stammtisch test chat lounge home""".split()

VALID = re.compile(r"[A-Za-z0-9\-]{1,30}")
TRANS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe",
                       "Ü": "Ue", "ß": "ss"})


def variants(word: str):
    w = word.split("/")[0].strip()          # strip hunspell affix flags
    if not w:
        return
    if not VALID.fullmatch(w):
        w = w.translate(TRANS)               # transliterate umlauts, retry
        if not VALID.fullmatch(w):
            return
    for v in (w, w.lower(), w.capitalize(), w.upper()):
        if VALID.fullmatch(v):
            yield v


def main() -> None:
    out: set[str] = set()
    for src in SOURCES:
        if not os.path.exists(src):
            print(f"  skip (missing): {src}")
            continue
        with open(src, encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i == 0 and src.endswith(".dic") and line.strip().isdigit():
                    continue                 # hunspell count header
                out.update(variants(line))
        print(f"  read: {src}")
    for s in SEEDS:
        out.update(variants(s))

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "combined.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(out)))
    print(f"wrote {len(out):,} names -> {path}")


if __name__ == "__main__":
    main()
