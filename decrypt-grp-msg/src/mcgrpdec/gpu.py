"""Vulkan GPU brute-forcer (wgpu-native, no browser).

Runs the WGSL kernel in ``shaders/crack.wgsl`` on whatever Vulkan device wgpu
picks — on this machine the Intel iGPU. The kernel fully verifies each candidate
(channel hash + 2-byte HMAC), so only real hits return; the host reconstructs
the name and confirms by decrypting.
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from . import candidates as C
from . import crypto
from .cpu import Hit
from .packet import GroupPacket

_SHADER = Path(__file__).with_name("shaders") / "crack.wgsl"

# Keep per-dispatch work bounded so a single submit stays responsive.
_MAX_INNER = 37 ** 5          # ~69M candidates per dispatch
_WORKGROUP = 256
_MAX_GROUPS_DIM = 65535
_OUT_CAP = 4096               # true hits are rare; this is plenty


class GpuUnavailable(RuntimeError):
    pass


def _sha256_tail_blocks(prefix_len: int, msg: bytes) -> list[list[int]]:
    """The 512-bit blocks of ``SHA256(<prefix of prefix_len bytes> || msg)`` that
    come *after* the first ``prefix_len``-byte block.

    Used to bake the ciphertext (and its SHA padding) for the inner HMAC, where
    the first block is the key-dependent ipad computed in the shader. Requires
    ``prefix_len`` to be a whole number of blocks (64 here). Handles any msg
    length (one or more trailing blocks)."""
    assert prefix_len % 64 == 0
    total = prefix_len + len(msg)
    padded = bytearray(msg)
    padded.append(0x80)
    while (prefix_len + len(padded)) % 64 != 56:
        padded.append(0x00)
    padded += (total * 8).to_bytes(8, "big")
    words: list[list[int]] = []
    for off in range(0, len(padded), 64):
        block = padded[off:off + 64]
        words.append([int.from_bytes(block[i:i + 4], "big") for i in range(0, 64, 4)])
    return words


def gpu_available() -> bool:
    try:
        import wgpu  # noqa: F401
    except ImportError:
        return False
    try:
        import wgpu.utils

        adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        return adapter is not None
    except Exception:
        return False


def _build_shader(gp: GroupPacket) -> str:
    """Substitute the ciphertext-dependent inner-HMAC blocks into the kernel.

    Handles any ciphertext length (one or more trailing blocks after the
    key-dependent ipad block computed in the shader)."""
    src = _SHADER.read_text()
    lines = []
    for i, block in enumerate(_sha256_tail_blocks(64, gp.ciphertext)):
        words = ", ".join(f"0x{w:08x}u" for w in block)
        lines.append(f"var _ib{i} = array<u32,16>({words}); compress(&hi, &_ib{i});")
    return src.replace("/*INNER_TAIL*/", "\n    ".join(lines))


def brute_gpu(
    framings: list[GroupPacket],
    *,
    charset: str = C.DEFAULT_CHARSET,
    min_len: int = 1,
    max_len: int = 6,
    both_prefix: bool = True,
    min_ts: int = crypto.TS_MIN_DEFAULT,
    max_ts: int = crypto.TS_MAX_DEFAULT,
    progress=None,
) -> Hit | None:
    """Brute-force names ``min_len..max_len`` on the GPU. Returns a Hit or None."""
    try:
        import numpy as np
        import wgpu
    except ImportError as e:
        raise GpuUnavailable(f"wgpu/numpy not installed ({e}); `uv sync --extra gpu`") from e

    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    if adapter is None:
        raise GpuUnavailable("no Vulkan adapter")
    device = adapter.request_device_sync()
    info = adapter.info
    dev_name = info.get("device", "?") if isinstance(info, dict) else str(info)

    base = len(charset)
    charset_bytes = np.frombuffer(charset.encode("ascii"), dtype=np.uint8).astype(np.uint32)

    prefixes = (1, 0) if both_prefix else (1,)

    for gp in framings:
        shader = device.create_shader_module(code=_build_shader(gp))
        pipeline = device.create_compute_pipeline(
            layout="auto", compute={"module": shader, "entry_point": "main"}
        )
        cs_buf = device.create_buffer_with_data(
            data=charset_bytes.tobytes(),
            usage=wgpu.BufferUsage.STORAGE,
        )
        for use_hash in prefixes:
            for length in range(min_len, max_len + 1):
                hit = _sweep_length(
                    device, pipeline, cs_buf, charset, base, length, use_hash,
                    gp, np, wgpu, min_ts, max_ts, progress,
                )
                if hit:
                    return hit
    return None


def _sweep_length(device, pipeline, cs_buf, charset, base, length, use_hash,
                  gp, np, wgpu, min_ts, max_ts, progress) -> Hit | None:
    inner_len = min(length, 5)
    while base ** inner_len > _MAX_INNER and inner_len > 0:
        inner_len -= 1
    inner_count = base ** inner_len
    high_len = length - inner_len
    total = base ** length
    done = 0

    # host loops over the fixed high-order characters
    for high_index in range(base ** high_len):
        high_name = C.index_to_name(high_index, charset, high_len) if high_len else ""
        high_bytes = np.frombuffer(high_name.encode("ascii"), dtype=np.uint8).astype(np.uint32) \
            if high_name else np.zeros(1, dtype=np.uint32)

        hit = _dispatch(device, pipeline, cs_buf, charset, base, length, inner_len,
                        inner_count, high_len, high_name, high_bytes, use_hash,
                        high_index, gp, np, wgpu, min_ts, max_ts)
        done += inner_count
        if progress:
            progress(length, min(done, total), total)
        if hit:
            return hit
    return None


def _dispatch(device, pipeline, cs_buf, charset, base, length, inner_len,
              inner_count, high_len, high_name, high_bytes, use_hash,
              high_index, gp, np, wgpu, min_ts, max_ts) -> Hit | None:
    groups = (inner_count + _WORKGROUP - 1) // _WORKGROUP
    groups_x = min(groups, _MAX_GROUPS_DIM)
    groups_y = (groups + groups_x - 1) // groups_x
    stride_x = groups_x * _WORKGROUP

    params = struct.pack(
        "<12I",
        base, length, inner_len, inner_count, stride_x, use_hash, high_len, 0,
        gp.chash, gp.mac[0], gp.mac[1], 0,
    )
    ubuf = device.create_buffer_with_data(data=params, usage=wgpu.BufferUsage.UNIFORM)
    hbuf = device.create_buffer_with_data(
        data=high_bytes.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    count_buf = device.create_buffer(
        size=4, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC | wgpu.BufferUsage.COPY_DST
    )
    gids_buf = device.create_buffer(
        size=4 * _OUT_CAP,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )

    bind = device.create_bind_group(
        layout=pipeline.get_bind_group_layout(0),
        entries=[
            {"binding": 0, "resource": {"buffer": ubuf, "offset": 0, "size": ubuf.size}},
            {"binding": 1, "resource": {"buffer": cs_buf, "offset": 0, "size": cs_buf.size}},
            {"binding": 2, "resource": {"buffer": hbuf, "offset": 0, "size": hbuf.size}},
            {"binding": 3, "resource": {"buffer": count_buf, "offset": 0, "size": 4}},
            {"binding": 4, "resource": {"buffer": gids_buf, "offset": 0, "size": gids_buf.size}},
        ],
    )

    enc = device.create_command_encoder()
    cp = enc.begin_compute_pass()
    cp.set_pipeline(pipeline)
    cp.set_bind_group(0, bind)
    cp.dispatch_workgroups(groups_x, groups_y, 1)
    cp.end()
    device.queue.submit([enc.finish()])

    count = int(np.frombuffer(device.queue.read_buffer(count_buf), dtype=np.uint32)[0])
    if count == 0:
        return None
    gids = np.frombuffer(
        device.queue.read_buffer(gids_buf, size=4 * min(count, _OUT_CAP)), dtype=np.uint32
    )
    for gid in gids.tolist():
        low = C.index_to_name(int(gid), charset, inner_len)
        name = low + high_name
        hashed = ("#" + name) if use_hash else name
        key = hashlib.sha256(hashed.encode("utf-8")).digest()[:16]
        # chash/mac already matched gp on the GPU; confirm by decrypting +
        # timestamp-gating (rejects the 24-bit collisions the GPU can't filter).
        msg = crypto.try_decrypt(key, gp.chash, gp.mac, gp.ciphertext,
                                 min_ts=min_ts, max_ts=max_ts)
        if msg:
            return Hit(name, hashed, key, gp, msg)
    return None
