"""Known-answer tests for the MeshCore group-message crypto and cracker.

Vectors:
  * public-channel packet -> "🌲 Tree: ☁️"  (from michaelhart/meshcore-decoder tests)
  * a real #test packet    -> "42B8C196: Test"
"""

import hashlib

import pytest

from mcgrpdec import crypto
from mcgrpdec.cpu import brute_cpu, check_names
from mcgrpdec.packet import (
    PAYLOAD_TYPE_GRP_TXT,
    candidate_framings,
    clean_hex,
    parse_group_packet,
)

# --- vectors -----------------------------------------------------------------

PUBLIC_RAW = "150011C3C1354D619BAE9590E4D177DB7EEAF982F5BDCF78005D75157D9535FA90178F785D"
PUBLIC_EXPECT = dict(ts=1758484279, sender="🌲 Tree", text="☁️", chash=0x11, mac="c3c1")

TEST_RAW = ("150320 DD 2CD9 B9 E7 7A 7A B2 CE C9 18 EA AC A3 95 EE 38 AD 98 99 A5 "
            "64 A4 01 AE 22 88 CD C8 83 6C 6E 4E 00 7F 1D D6")
TEST_EXPECT = dict(name="test", hashed="#test", ts=1782920347,
                   sender="42B8C196", text="Test", chash=0xD9, mac="b9e7",
                   key="9cd8fcf22a47333b591d96a2b848b73f")

UNKNOWN_RAW = ("154191 DD42 06 EE A5 AF FC 4F 11 3E 3D 62 AF D8 C1 82 A0 EE 75 44 2A "
               "0A 81 16 9E 08 5F 04 9B 16 F6 95 05 C0 D6 80 42 28 09 E7 5D BB A6 1A "
               "E5 34 97 FB DB 87 B1 28")


# --- crypto primitives -------------------------------------------------------

def test_key_derivation_includes_hash_prefix():
    # The real #test packet proves the '#' is part of the hashed string.
    key = hashlib.sha256(b"#test").digest()[:16]
    assert key.hex() == TEST_EXPECT["key"]
    assert crypto.key_from_name("test").hex() == TEST_EXPECT["key"]
    assert crypto.key_from_name("#test").hex() == TEST_EXPECT["key"]


def test_channel_hash_and_secret():
    key = bytes.fromhex(TEST_EXPECT["key"])
    assert crypto.channel_hash(key) == TEST_EXPECT["chash"]
    assert crypto.channel_secret(key) == key + b"\x00" * 16


def test_candidate_keys_yields_both_derivations():
    ks = crypto.candidate_keys("foo")
    labels = [lbl for lbl, _ in ks]
    assert labels == ["#foo", "foo"]


# --- packet parsing ----------------------------------------------------------

def test_clean_hex_tolerates_spacing():
    assert clean_hex("15 03:20\nDD") == bytes.fromhex("150320dd")


def test_parse_public_packet_framing():
    gp = parse_group_packet(PUBLIC_RAW)
    assert gp.payload_type == PAYLOAD_TYPE_GRP_TXT
    assert gp.chash == PUBLIC_EXPECT["chash"]
    assert gp.mac.hex() == PUBLIC_EXPECT["mac"]
    assert len(gp.ciphertext) % 16 == 0 and len(gp.ciphertext) == 32


def test_parse_test_packet_framing():
    gp = parse_group_packet(TEST_RAW)
    assert gp.payload_type == PAYLOAD_TYPE_GRP_TXT
    assert gp.hash_size == 1 and gp.hop_count == 3
    assert gp.chash == TEST_EXPECT["chash"]
    assert gp.mac.hex() == TEST_EXPECT["mac"]


def test_parse_unknown_packet_framing():
    gp = parse_group_packet(UNKNOWN_RAW)
    assert gp.payload_type == PAYLOAD_TYPE_GRP_TXT
    assert gp.hash_size == 2 and gp.hop_count == 1
    assert gp.chash == 0x42
    assert gp.mac.hex() == "06ee"
    assert len(gp.ciphertext) == 48


# --- end-to-end decryption (the "known message" tests) -----------------------

def test_decrypt_public_channel_vector():
    gp = parse_group_packet(PUBLIC_RAW)
    msg = crypto.try_decrypt(crypto.PUBLIC_CHANNEL_KEY, gp.chash, gp.mac, gp.ciphertext)
    assert msg is not None
    assert msg.timestamp == PUBLIC_EXPECT["ts"]
    assert msg.sender == PUBLIC_EXPECT["sender"]
    assert msg.text == PUBLIC_EXPECT["text"]


def test_decrypt_known_test_channel():
    gp = parse_group_packet(TEST_RAW)
    key = crypto.key_from_name("#test")
    msg = crypto.try_decrypt(key, gp.chash, gp.mac, gp.ciphertext)
    assert msg is not None
    assert msg.timestamp == TEST_EXPECT["ts"]
    assert msg.sender == TEST_EXPECT["sender"]
    assert msg.text == TEST_EXPECT["text"]


def test_wrong_key_is_rejected():
    gp = parse_group_packet(TEST_RAW)
    wrong = crypto.key_from_name("#nottest")
    assert crypto.try_decrypt(wrong, gp.chash, gp.mac, gp.ciphertext) is None


# --- cracker -----------------------------------------------------------------

def test_dictionary_cracks_test_channel():
    framings = candidate_framings(TEST_RAW)
    hit = check_names(["public", "foo", "test", "bar"], framings)
    assert hit is not None
    assert hit.name == "test"
    assert hit.hashed == "#test"
    assert hit.message.text == "Test"


def test_brute_force_cracks_short_name():
    # "test" is 4 chars; a small exhaustive sweep must find it.
    framings = candidate_framings(TEST_RAW)
    hit = brute_cpu(framings, charset="abceimnorstuvwxyz", min_len=4, max_len=4,
                    processes=2, chunk=50_000)
    assert hit is not None
    assert hit.name == "test"
    assert hit.message.text == "Test"


def test_brute_force_reports_none_when_absent():
    framings = candidate_framings(TEST_RAW)
    # Search a tiny space that cannot contain "test".
    hit = brute_cpu(framings, charset="0123456789", min_len=1, max_len=2, processes=2)
    assert hit is None


# --- framing hygiene: no speculative tail framings when the header is valid ----

def test_no_tail_framings_when_header_valid():
    # The unknown packet parses as GRP_TXT, so the header framing (chash 0x42) is
    # authoritative — speculative tail framings (which caused a chash 0xEE false
    # positive) must NOT be emitted alongside it.
    fr = candidate_framings(UNKNOWN_RAW)
    assert len(fr) == 1
    assert fr[0].framing == "header" and fr[0].chash == 0x42


# --- the 24-bit-collision / timestamp-window subtlety --------------------------
# The 1-byte chash + 2-byte MAC is only a 24-bit tag, so brute force throws up
# collisions whose plaintext timestamp is random (e.g. years in the future).
# Anchoring the timestamp window to the packet's capture time rejects them.

FIRST_SEEN = 1782919932  # 2026-07-01T15:32:12Z (observer first_seen)


def test_timestamp_gate_rejects_far_future():
    import struct
    # A plausible-looking decrypted plaintext, but timestamped in year 2031.
    future = struct.pack("<I", 1955680249) + b"\x00" + b"gU"
    assert crypto.looks_like_plaintext(future) is True           # broad default
    assert crypto.looks_like_plaintext(
        future, min_ts=FIRST_SEEN - 86400, max_ts=FIRST_SEEN + 86400
    ) is False                                                    # anchored


def test_timestamp_gate_accepts_capture_time():
    import struct
    real = struct.pack("<I", FIRST_SEEN) + b"\x00" + b"Alice: hi"
    assert crypto.looks_like_plaintext(
        real, min_ts=FIRST_SEEN - 86400, max_ts=FIRST_SEEN + 86400
    ) is True
