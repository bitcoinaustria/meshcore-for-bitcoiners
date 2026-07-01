"""CPU brute-force / dictionary cracker (multiprocessing, hashlib).

This is the always-available fallback and the dictionary engine. It is correct
but modest (~1-3 M names/s per core); for large exhaustive sweeps use the GPU
engine in :mod:`mcgrpdec.gpu`.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from . import candidates as C
from . import crypto
from .packet import GroupPacket


@dataclass
class Hit:
    name: str            # the bare candidate name
    hashed: str          # the exact string that was SHA256'd (e.g. "#test")
    key: bytes
    packet: GroupPacket
    message: crypto.GroupMessage


# A target is (chash, mac, ciphertext); we group framings by their chash byte so
# the hot loop does one dict lookup and only MAC-checks on a chash hit.
Target = tuple[int, bytes, bytes]


def _targets_by_chash(framings: list[GroupPacket]) -> dict[int, list[GroupPacket]]:
    d: dict[int, list[GroupPacket]] = {}
    for gp in framings:
        d.setdefault(gp.chash, []).append(gp)
    return d


def _check(
    hashed: str, name: str, by_chash: dict[int, list[GroupPacket]],
    min_ts: int, max_ts: int,
) -> Hit | None:
    key = hashlib.sha256(hashed.encode("utf-8")).digest()[:16]
    ch = hashlib.sha256(key).digest()[0]
    hits = by_chash.get(ch)
    if not hits:
        return None
    for gp in hits:
        msg = crypto.try_decrypt(key, gp.chash, gp.mac, gp.ciphertext,
                                 min_ts=min_ts, max_ts=max_ts)
        if msg:
            return Hit(name, hashed, key, gp, msg)
    return None


def check_names(
    names: Iterable[str],
    framings: list[GroupPacket],
    *,
    both_prefix: bool = True,
    min_ts: int = crypto.TS_MIN_DEFAULT,
    max_ts: int = crypto.TS_MAX_DEFAULT,
) -> Hit | None:
    """Scan an iterable of names (dictionary path). Tries ``#name`` and ``name``."""
    by_chash = _targets_by_chash(framings)
    for name in names:
        if name.startswith("#"):
            variants = (name,)
        elif both_prefix:
            variants = ("#" + name, name)
        else:
            variants = ("#" + name,)
        for hashed in variants:
            hit = _check(hashed, name.lstrip("#"), by_chash, min_ts, max_ts)
            if hit:
                return hit
    return None


# ------------------------- multiprocessing brute force -----------------------

_W_CHARSET = ""
_W_LENGTH = 0
_W_BYCHASH: dict[int, list[GroupPacket]] = {}
_W_BOTH = True
_W_MIN_TS = crypto.TS_MIN_DEFAULT
_W_MAX_TS = crypto.TS_MAX_DEFAULT


def _winit(charset, length, by_chash, both, min_ts, max_ts):
    global _W_CHARSET, _W_LENGTH, _W_BYCHASH, _W_BOTH, _W_MIN_TS, _W_MAX_TS
    _W_CHARSET, _W_LENGTH, _W_BYCHASH, _W_BOTH = charset, length, by_chash, both
    _W_MIN_TS, _W_MAX_TS = min_ts, max_ts


def _wscan(rng: tuple[int, int]) -> Hit | None:
    lo, hi = rng
    charset, length, by_chash, both = _W_CHARSET, _W_LENGTH, _W_BYCHASH, _W_BOTH
    min_ts, max_ts = _W_MIN_TS, _W_MAX_TS
    for idx in range(lo, hi):
        name = C.index_to_name(idx, charset, length)
        if C.DASH in name and not C._dash_ok(name):
            continue
        variants = ("#" + name, name) if both else ("#" + name,)
        for hashed in variants:
            hit = _check(hashed, name, by_chash, min_ts, max_ts)
            if hit:
                return hit
    return None


def brute_cpu(
    framings: list[GroupPacket],
    *,
    charset: str = C.DEFAULT_CHARSET,
    min_len: int = 1,
    max_len: int = 5,
    both_prefix: bool = True,
    processes: int | None = None,
    chunk: int = 200_000,
    min_ts: int = crypto.TS_MIN_DEFAULT,
    max_ts: int = crypto.TS_MAX_DEFAULT,
    progress: "callable | None" = None,
) -> Hit | None:
    """Exhaustively brute-force names ``min_len..max_len`` across processes.

    ``progress(length, done, total)`` is called periodically if given.
    Returns the first :class:`Hit` or ``None``.
    """
    import multiprocessing as mp

    procs = processes or os.cpu_count() or 4
    for length in range(min_len, max_len + 1):
        total = len(charset) ** length
        ranges = [(lo, min(lo + chunk, total)) for lo in range(0, total, chunk)]
        done = 0
        with mp.Pool(procs, initializer=_winit,
                     initargs=(charset, length, _targets_by_chash(framings),
                               both_prefix, min_ts, max_ts)) as pool:
            try:
                for res in pool.imap_unordered(_wscan, ranges):
                    done += 1
                    if progress:
                        progress(length, min(done * chunk, total), total)
                    if res is not None:
                        pool.terminate()
                        return res
            finally:
                pool.close()
                pool.join()
    return None


def iter_ranges(total: int, chunk: int) -> Iterator[tuple[int, int]]:
    for lo in range(0, total, chunk):
        yield (lo, min(lo + chunk, total))


# ------------------------- batch (many messages) -----------------------------

@dataclass
class BatchTarget:
    label: str
    framings: list[GroupPacket]
    min_ts: int
    max_ts: int


def crack_batch(
    targets: list[BatchTarget],
    names: Iterable[str],
    *,
    both_prefix: bool = True,
) -> dict[int, Hit]:
    """Try each name against *every* target at once (dictionary/wordlist path).

    Computes each candidate key once and checks it against all targets whose
    channel-hash matches, so scanning N messages costs barely more than one.
    Returns ``{target_index: Hit}`` for those solved.
    """
    # chash -> list of (target_index, framing)
    by_chash: dict[int, list[tuple[int, GroupPacket]]] = {}
    for i, t in enumerate(targets):
        for gp in t.framings:
            by_chash.setdefault(gp.chash, []).append((i, gp))

    solved: dict[int, Hit] = {}
    remaining = len(targets)
    for name in names:
        if name.startswith("#"):
            variants = (name,)
        elif both_prefix:
            variants = ("#" + name, name)
        else:
            variants = ("#" + name,)
        for hashed in variants:
            key = hashlib.sha256(hashed.encode("utf-8")).digest()[:16]
            ch = hashlib.sha256(key).digest()[0]
            hits = by_chash.get(ch)
            if not hits:
                continue
            for idx, gp in hits:
                if idx in solved:
                    continue
                t = targets[idx]
                msg = crypto.try_decrypt(key, gp.chash, gp.mac, gp.ciphertext,
                                         min_ts=t.min_ts, max_ts=t.max_ts)
                if msg:
                    solved[idx] = Hit(name.lstrip("#"), hashed, key, gp, msg)
                    remaining -= 1
        if remaining == 0:
            break
    return solved
