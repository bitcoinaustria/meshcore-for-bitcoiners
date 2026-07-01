"""Fetch a captured packet from a meshcore.observer / CoreScope logger.

The logger exposes a JSON API::

    https://<host>.meshcore.observer/api/packets/<hash>

whose ``packet.decoded_json`` carries ``channelHash``, ``mac`` and
``encryptedData`` (the raw ciphertext) for a GRP_TXT packet, and ``first_seen``
gives the capture time — the anchor for the timestamp filter.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import urllib.request
from dataclasses import dataclass

from .packet import GroupPacket

DEFAULT_HOST = "logger-at.meshcore.observer"
_HASH_RE = re.compile(r"[0-9a-fA-F]{8,}")


@dataclass
class ObservedPacket:
    packet: GroupPacket
    first_seen: int | None      # unix seconds, or None
    source_url: str
    raw_decoded: dict


def _parse_ref(url_or_id: str) -> str:
    """Return an API URL from a full packet URL, a bare hash, or an API URL."""
    s = url_or_id.strip()
    if s.startswith("http") and "/api/" in s:
        return s
    if s.startswith("http"):
        # a UI URL like https://host/#/packets/<hash>
        m = _HASH_RE.search(s.split("#", 1)[-1])
        host = re.sub(r"^https?://", "", s).split("/", 1)[0]
        if m:
            return f"https://{host}/api/packets/{m.group(0)}"
    if _HASH_RE.fullmatch(s):
        return f"https://{DEFAULT_HOST}/api/packets/{s}"
    raise ValueError(f"cannot interpret observer reference: {url_or_id!r}")


def _iso_to_unix(s: str | None) -> int | None:
    if not s:
        return None
    try:
        return int(_dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())
    except ValueError:
        return None


def fetch(url_or_id: str, *, timeout: float = 15.0) -> ObservedPacket:
    api = _parse_ref(url_or_id)
    req = urllib.request.Request(api, headers={
        "User-Agent": "mcgrpdec/0.1 (+https://github.com/bitcoinaustria)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        doc = json.load(r)
    pkt = doc.get("packet", doc)
    decoded = pkt.get("decoded_json")
    if isinstance(decoded, str):
        decoded = json.loads(decoded)
    if not decoded or decoded.get("type") != "GRP_TXT":
        raise ValueError(f"not a GRP_TXT packet: type={decoded.get('type') if decoded else None}")
    chash = int(decoded["channelHash"])
    mac = bytes.fromhex(decoded["mac"])
    ct = bytes.fromhex(decoded["encryptedData"])
    gp = GroupPacket(chash=chash, mac=mac, ciphertext=ct,
                     payload_type=0x05, framing="observer")
    first_seen = _iso_to_unix(pkt.get("first_seen"))
    return ObservedPacket(packet=gp, first_seen=first_seen, source_url=api, raw_decoded=decoded)
