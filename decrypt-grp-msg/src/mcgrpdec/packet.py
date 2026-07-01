"""Parse a MeshCore on-air packet (or a meshcore.observer "raw" string) into
the group-text fields we need: channel hash, MAC, and ciphertext.

Wire format (firmware ``Packet.h``)::

    header : 1 byte   route(bits0-1) | payload_type(bits2-5) | version(bits6-7)
    path   : 1 length byte, then path bytes
             length byte = (hash_size-1)<<6 | (hop_count & 0x3F)
             path is  hop_count * hash_size  bytes
    payload: for GRP_TXT ->  chash(1) | mac(2) | ciphertext(16*k)

The observer groups the hex cosmetically (e.g. ``154191 DD42 06 EE ...``); the
concatenated string is the contiguous packet, so we just strip whitespace.
"""

from __future__ import annotations

from dataclasses import dataclass

ROUTE_TYPES = {0: "TRANSPORT_FLOOD", 1: "FLOOD", 2: "DIRECT", 3: "TRANSPORT_DIRECT"}
PAYLOAD_TYPES = {
    0x00: "REQ", 0x01: "RESPONSE", 0x02: "TXT_MSG", 0x03: "ACK", 0x04: "ADVERT",
    0x05: "GRP_TXT", 0x06: "GRP_DATA", 0x07: "ANON_REQ", 0x08: "PATH",
    0x09: "TRACE", 0x0A: "MULTIPART", 0x0B: "CONTROL", 0x0F: "RAW_CUSTOM",
}
PAYLOAD_TYPE_GRP_TXT = 0x05
# Transport route types carry an extra 4-byte transport code before the path.
_TRANSPORT_ROUTES = {0, 3}


class PacketError(ValueError):
    pass


def clean_hex(s: str) -> bytes:
    """Whitespace/':'-tolerant hex → bytes."""
    compact = "".join(s.split()).replace(":", "").replace("0x", "").replace("0X", "")
    try:
        return bytes.fromhex(compact)
    except ValueError as e:
        raise PacketError(f"not valid hex: {e}") from e


@dataclass
class GroupPacket:
    chash: int
    mac: bytes
    ciphertext: bytes
    # framing metadata (best-effort; None when derived by the tail fallback)
    route_type: int | None = None
    payload_type: int | None = None
    version: int | None = None
    hash_size: int | None = None
    hop_count: int | None = None
    path: bytes = b""
    framing: str = "header"  # "header" | "tail"

    def describe(self) -> str:
        pt = PAYLOAD_TYPES.get(self.payload_type, "?") if self.payload_type is not None else "?"
        rt = ROUTE_TYPES.get(self.route_type, "?") if self.route_type is not None else "?"
        lines = [
            f"framing     : {self.framing}",
            f"route       : {rt} ({self.route_type})" if self.route_type is not None else None,
            f"payload     : {pt} ({self.payload_type})" if self.payload_type is not None else None,
            f"path        : {self.path.hex()}  ({self.hop_count} hop(s) x {self.hash_size} B)"
            if self.hash_size is not None else None,
            f"channel hash: 0x{self.chash:02x}",
            f"MAC         : {self.mac.hex()}",
            f"ciphertext  : {len(self.ciphertext)} bytes ({len(self.ciphertext)//16} AES blocks)",
        ]
        return "\n".join(l for l in lines if l)


def parse_group_packet(s: str) -> GroupPacket:
    """Best single interpretation of a raw group-text packet.

    Returns the header/path decode when the header is GRP_TXT; otherwise the
    longest tail framing. For ambiguous logger formats prefer
    :func:`candidate_framings`, which yields every possibility and lets the MAC
    decide.
    """
    cands = candidate_framings(s)
    if not cands:
        raise PacketError(
            "could not locate a GRP_TXT payload: header is not GRP_TXT and no "
            "16-byte-aligned ciphertext tail found"
        )
    return cands[0]


def candidate_framings(s: str) -> list[GroupPacket]:
    """Plausible (chash, mac, ciphertext) split(s), best first.

    When the header parses as a real GRP_TXT packet, that single framing is
    authoritative and returned alone. Only when the header can't be parsed (an
    unusual logger that prepends metadata bytes) do we fall back to speculative
    tail-based framings — those are guesses and can manufacture false positives,
    so we never mix them in alongside a valid header parse.
    """
    data = clean_hex(s)
    if len(data) < 4:
        raise PacketError("packet too short")
    try:
        pkt = _parse_header(data)
    except PacketError:
        pkt = None
    if pkt is not None:
        return [pkt]
    return _tail_framings(data)


def _parse_header(data: bytes) -> GroupPacket | None:
    header = data[0]
    route_type = header & 0x03
    payload_type = (header >> 2) & 0x0F
    version = (header >> 6) & 0x03
    if payload_type != PAYLOAD_TYPE_GRP_TXT:
        return None

    off = 1
    if route_type in _TRANSPORT_ROUTES:
        off += 4  # transport code
    if off >= len(data):
        raise PacketError("truncated before path length")
    plen_byte = data[off]
    off += 1
    hash_size = ((plen_byte >> 6) & 0x03) + 1
    hop_count = plen_byte & 0x3F
    path_len = hash_size * hop_count
    path = data[off:off + path_len]
    off += path_len

    payload = data[off:]
    if len(payload) < 3:
        raise PacketError("truncated group-text payload")
    chash = payload[0]
    mac = payload[1:3]
    ct = payload[3:]
    if len(ct) == 0 or len(ct) % 16 != 0:
        raise PacketError(f"ciphertext length {len(ct)} is not a positive multiple of 16")
    return GroupPacket(
        chash=chash, mac=mac, ciphertext=ct, route_type=route_type,
        payload_type=payload_type, version=version, hash_size=hash_size,
        hop_count=hop_count, path=path, framing="header",
    )


def _tail_framings(data: bytes) -> list[GroupPacket]:
    """All tail framings: ciphertext = a 16-byte-aligned suffix, ``mac`` the two
    bytes before it, ``chash`` the byte before that. Longest ciphertext first
    (must leave at least one prefix byte for header/path)."""
    out: list[GroupPacket] = []
    max_ct = ((len(data) - 4) // 16) * 16  # leave >=1 prefix byte + chash + mac
    for ct_len in range(max_ct, 0, -16):
        start = len(data) - ct_len
        out.append(GroupPacket(
            chash=data[start - 3], mac=data[start - 2:start],
            ciphertext=data[start:], framing="tail",
        ))
    return out
