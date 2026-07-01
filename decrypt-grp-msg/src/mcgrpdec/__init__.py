"""Decrypt and brute-force MeshCore group-channel ("#hashtag room") messages.

Verified against real packets and a known-answer public-channel vector.
"""

from .crypto import (
    GroupMessage,
    PUBLIC_CHANNEL_KEY,
    candidate_keys,
    channel_hash,
    key_from_name,
    parse_plaintext,
    try_decrypt,
)
from .packet import GroupPacket, PacketError, candidate_framings, parse_group_packet

__all__ = [
    "GroupMessage", "GroupPacket", "PacketError", "PUBLIC_CHANNEL_KEY",
    "candidate_framings", "candidate_keys", "channel_hash", "key_from_name",
    "parse_group_packet", "parse_plaintext", "try_decrypt",
]

__version__ = "0.1.0"
