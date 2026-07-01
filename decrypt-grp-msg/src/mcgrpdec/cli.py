"""Command-line interface (click) for the MeshCore group-message decrypter.

Commands:
  decrypt  — decrypt a packet with a known channel name/key (falls through to a
             crack if none is given, so any crack flag also works here)
  crack    — recover an unknown channel name (dictionary, then brute force)
  batch    — run a list of messages from a file, sharing work across them
  bench    — measure brute-force throughput (keys/s)
  selftest — known-answer vectors
"""

from __future__ import annotations

import datetime as dt
import os
import sys
import time

import click

from . import candidates as C
from . import crypto
from .cpu import BatchTarget, Hit, brute_cpu, check_names, crack_batch
from .packet import GroupPacket, PacketError, candidate_framings

DAY = 86400


# --------------------------------------------------------------------------- io

def _read_raw(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    if value.startswith("@"):
        with open(value[1:], encoding="utf-8") as fh:
            return fh.read()
    return value


def _parse_time(s: str) -> int:
    s = s.strip()
    if s.isdigit():
        return int(s)
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def _is_observer_ref(s: str) -> bool:
    s = s.strip()
    return s.startswith("obs:") or s.startswith("http")


def _window(ref: int | None, window: int) -> tuple[int, int]:
    now = int(time.time())
    win = window or DAY
    if ref is not None:
        return ref - win, ref + win
    return now - 370 * DAY, now + 2 * DAY


def _framings_and_window(
    *, raw: str | None, observer: str | None, seen_time: str | None,
    window: int, quiet: bool = False,
) -> tuple[list[GroupPacket], int, int]:
    ref: int | None = None
    if observer:
        from .observer import fetch
        obs = fetch(observer[4:] if observer.startswith("obs:") else observer)
        framings = [obs.packet]
        ref = obs.first_seen
        if not quiet:
            click.echo(f"observer: {obs.source_url}")
            seen = dt.datetime.utcfromtimestamp(ref).isoformat() + "Z" if ref else "unknown"
            click.echo(f"  first_seen: {seen}")
    else:
        framings = candidate_framings(_read_raw(raw))
    if seen_time:
        ref = _parse_time(seen_time)
    min_ts, max_ts = _window(ref, window)
    if not quiet:
        best = framings[0]
        click.echo("packet:")
        click.echo("  " + best.describe().replace("\n", "\n  "))
        if len(framings) > 1:
            click.echo(f"  (+{len(framings) - 1} alternative tail framing(s))")
        lo = dt.datetime.utcfromtimestamp(min_ts).date()
        hi = dt.datetime.utcfromtimestamp(max_ts).date()
        click.echo(f"  accept timestamps: {lo} .. {hi}")
    return framings, min_ts, max_ts


def _report_hit(hit: Hit) -> None:
    click.secho(f"\n✔ CRACKED: channel = {hit.name!r}  (hashed as {hit.hashed!r})", fg="green", bold=True)
    click.echo(f"  key       : {hit.key.hex()}")
    click.echo(f"  timestamp : {hit.message.timestamp}")
    click.echo(f"  sender    : {hit.message.sender}")
    click.echo(f"  message   : {hit.message.text}")


def _mk_progress():
    state = {"t": 0.0}

    def progress(length, done, total):
        now = time.time()
        if now - state["t"] < 0.5:
            return
        state["t"] = now
        pct = 100.0 * done / total if total else 100.0
        sys.stderr.write(f"\r    len {length}: {done:,}/{total:,} ({pct:5.1f}%)   ")
        sys.stderr.flush()
        if done >= total:
            sys.stderr.write("\n")

    return progress


def _gpu_available() -> bool:
    try:
        from .gpu import gpu_available
        return gpu_available()
    except Exception:
        return False


# ------------------------------------------------------------------- core solve

def _try_known_keys(framings, name, key, public, min_ts, max_ts) -> Hit | None:
    keys: list[tuple[str, bytes]] = []
    if public:
        keys.append(("<public>", crypto.PUBLIC_CHANNEL_KEY))
    if key:
        keys.append((f"key:{key}", bytes.fromhex(key)))
    if name:
        keys.extend(crypto.candidate_keys(name))
    for label, k in keys:
        for gp in framings:
            msg = crypto.try_decrypt(k, gp.chash, gp.mac, gp.ciphertext,
                                     min_ts=crypto.TS_MIN_DEFAULT, max_ts=crypto.TS_MAX_DEFAULT)
            if msg:
                nm = name.lstrip("#") if name else label
                return Hit(nm, label, k, gp, msg)
    return None


def _solve(framings, min_ts, max_ts, *, name, key, public, wordlist, charset,
           min_len, max_len, engine, jobs, no_brute, both_prefix) -> Hit | None:
    if name or key or public:
        hit = _try_known_keys(framings, name, key, public, min_ts, max_ts)
        if hit:
            return hit
        click.echo("    (given name/key did not decrypt; continuing)", err=True)

    # dictionary / seed list (+ optional wordlist)
    words = list(C.dictionary_candidates())
    if wordlist:
        words = C.load_wordlist(wordlist) + words
    click.echo(f"\n[1] dictionary: {len(words):,} names ...")
    t0 = time.time()
    hit = check_names(words, framings, both_prefix=both_prefix, min_ts=min_ts, max_ts=max_ts)
    if hit:
        return hit
    click.echo(f"    no dictionary hit ({time.time() - t0:.1f}s)")

    if no_brute:
        return None

    eng = engine
    if eng == "auto":
        eng = "gpu" if _gpu_available() else "cpu"
    click.echo(f"\n[2] brute force lengths {min_len}..{max_len} charset={len(charset)} engine={eng} ...")
    hit = None
    if eng == "gpu":
        from .gpu import GpuUnavailable, brute_gpu
        try:
            hit = brute_gpu(framings, charset=charset, min_len=min_len, max_len=max_len,
                            both_prefix=both_prefix, min_ts=min_ts, max_ts=max_ts,
                            progress=_mk_progress())
        except GpuUnavailable as e:
            click.echo(f"    GPU unavailable ({e}); falling back to CPU", err=True)
            eng = "cpu"
    if eng == "cpu":
        n = jobs if jobs and jobs > 0 else (os.cpu_count() or 4)
        click.echo(f"    CPU: {n} worker process(es)")
        hit = brute_cpu(framings, charset=charset, min_len=min_len, max_len=max_len,
                        both_prefix=both_prefix, processes=n, min_ts=min_ts, max_ts=max_ts,
                        progress=_mk_progress())
    return hit


# --------------------------------------------------------------------- options

def _source_options(f):
    f = click.argument("raw", required=False)(f)
    f = click.option("--observer", help="fetch the packet from a meshcore.observer id/URL")(f)
    f = click.option("--seen-time", help="capture time (unix or ISO) to anchor the timestamp filter")(f)
    f = click.option("--window", type=int, default=0, help="timestamp window in seconds (default 86400)")(f)
    return f


def _key_options(f):
    f = click.option("--name", help="channel name, e.g. test or #test")(f)
    f = click.option("--key", help="16-byte AES key as hex")(f)
    f = click.option("--public", is_flag=True, help="try the well-known public-channel key")(f)
    return f


def _crack_options(f):
    f = click.option("--wordlist", help="newline-delimited wordlist to try first")(f)
    f = click.option("--charset", default=C.DEFAULT_CHARSET, show_default=True, help="brute-force alphabet")(f)
    f = click.option("--min-len", type=int, default=1, show_default=True)(f)
    f = click.option("--max-len", type=int, default=6, show_default=True)(f)
    f = click.option("--engine", type=click.Choice(["auto", "gpu", "cpu"]), default="auto", show_default=True)(f)
    f = click.option("-j", "--jobs", type=int, default=0, help="CPU workers (0 = all cores)")(f)
    f = click.option("--no-brute", is_flag=True, help="dictionary only")(f)
    f = click.option("--hash-prefix-only", is_flag=True,
                     help="only try SHA256('#'+name); default also tries SHA256(name)")(f)
    return f


# -------------------------------------------------------------------- commands

@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def cli():
    """Decrypt / brute-force MeshCore group-channel (#hashtag room) messages."""


@cli.command()
@_source_options
@_key_options
@_crack_options
@click.pass_context
def decrypt(ctx, raw, observer, seen_time, window, name, key, public, **crack):
    """Decrypt with a known channel name or key.

    If no name/key is given (or it doesn't match), this falls through to a crack,
    so brute-force flags like --max-len also work here.
    """
    if not raw and not observer:
        raise click.UsageError("give a raw packet, or --observer <id/URL>")
    framings, min_ts, max_ts = _framings_and_window(
        raw=raw, observer=observer, seen_time=seen_time, window=window)
    hit = _solve(framings, min_ts, max_ts, name=name, key=key, public=public,
                 both_prefix=not crack["hash_prefix_only"],
                 wordlist=crack["wordlist"], charset=crack["charset"],
                 min_len=crack["min_len"], max_len=crack["max_len"],
                 engine=crack["engine"], jobs=crack["jobs"], no_brute=crack["no_brute"])
    if hit:
        _report_hit(hit)
        ctx.exit(0)
    click.secho("\n✗ not decrypted.", fg="red")
    ctx.exit(1)


@cli.command()
@_source_options
@_key_options
@_crack_options
@click.pass_context
def crack(ctx, raw, observer, seen_time, window, name, key, public, **cr):
    """Recover an unknown channel name by dictionary + brute force."""
    if not raw and not observer:
        raise click.UsageError("give a raw packet, or --observer <id/URL>")
    framings, min_ts, max_ts = _framings_and_window(
        raw=raw, observer=observer, seen_time=seen_time, window=window)
    hit = _solve(framings, min_ts, max_ts, name=name, key=key, public=public,
                 both_prefix=not cr["hash_prefix_only"],
                 wordlist=cr["wordlist"], charset=cr["charset"],
                 min_len=cr["min_len"], max_len=cr["max_len"],
                 engine=cr["engine"], jobs=cr["jobs"], no_brute=cr["no_brute"])
    if hit:
        _report_hit(hit)
        ctx.exit(0)
    click.secho("\n✗ not found in the searched space.", fg="red")
    ctx.exit(1)


@cli.command()
@click.argument("listfile")
@click.option("--wordlist", help="newline-delimited wordlist to try (in addition to the seed list)")
@click.option("--window", type=int, default=0, help="timestamp window in seconds (default 86400)")
@click.option("--hash-prefix-only", is_flag=True)
@click.option("--brute/--no-brute-unsolved", "brute", default=False,
              help="also GPU-brute each message the wordlist didn't solve")
@click.option("--charset", default=C.DEFAULT_CHARSET, show_default=True)
@click.option("--min-len", type=int, default=1, show_default=True)
@click.option("--max-len", type=int, default=6, show_default=True)
@click.option("--engine", type=click.Choice(["auto", "gpu", "cpu"]), default="auto", show_default=True)
def batch(listfile, wordlist, window, hash_prefix_only, brute, charset, min_len, max_len, engine):
    """Decrypt a LISTFILE of messages, sharing the dictionary work across them.

    LISTFILE: one entry per line. Blank lines and '#' comments are ignored.
    An optional 'label = ' prefix names the entry; the value is raw packet hex,
    an 'obs:<id>' observer reference, or a full observer URL. Example:

        \b
        p1 = 154191 DD42 06 EE ...
        vienna = obs:e9847719c3d40dee
        154F12 7F A1 ...
    """
    both = not hash_prefix_only
    targets: list[BatchTarget] = []
    with open(listfile, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            label, _, val = s.partition(" = ")
            if not val:
                label, val = f"msg{n}", s
            try:
                framings, mn, mx = _framings_and_window(
                    raw=None if _is_observer_ref(val) else val,
                    observer=val if _is_observer_ref(val) else None,
                    seen_time=None, window=window, quiet=True)
                gp = framings[0]
                click.echo(f"  {label:16} chash=0x{gp.chash:02x} mac={gp.mac.hex()} "
                           f"ct={len(gp.ciphertext)}B")
                targets.append(BatchTarget(label, framings, mn, mx))
            except (PacketError, ValueError, OSError) as e:
                click.echo(f"  {label:16} SKIP ({e})", err=True)

    if not targets:
        raise click.UsageError("no valid messages in listfile")

    words = list(C.dictionary_candidates())
    if wordlist:
        words = C.load_wordlist(wordlist) + words
    click.echo(f"\n[1] dictionary across {len(targets)} message(s): {len(words):,} names ...")
    t0 = time.time()
    solved = crack_batch(targets, words, both_prefix=both)
    click.echo(f"    {len(solved)}/{len(targets)} solved by dictionary ({time.time() - t0:.1f}s)")

    if brute:
        from .gpu import GpuUnavailable, brute_gpu
        for i, t in enumerate(targets):
            if i in solved:
                continue
            click.echo(f"\n[2] brute '{t.label}' lengths {min_len}..{max_len} ...")
            try:
                hit = brute_gpu(t.framings, charset=charset, min_len=min_len, max_len=max_len,
                                both_prefix=both, min_ts=t.min_ts, max_ts=t.max_ts,
                                progress=_mk_progress())
            except GpuUnavailable:
                n = os.cpu_count() or 4
                hit = brute_cpu(t.framings, charset=charset, min_len=min_len, max_len=max_len,
                                both_prefix=both, processes=n, min_ts=t.min_ts, max_ts=t.max_ts,
                                progress=_mk_progress())
            if hit:
                solved[i] = hit

    click.echo("\n================ results ================")
    for i, t in enumerate(targets):
        if i in solved:
            h = solved[i]
            click.secho(f"  ✔ {t.label:16} #{h.name}  ->  {h.message.sender}: {h.message.text}", fg="green")
        else:
            click.secho(f"  ✗ {t.label:16} (not cracked)", fg="yellow")


@cli.command()
@click.option("--engine", type=click.Choice(["auto", "gpu", "cpu"]), default="auto")
@click.option("--length", type=int, default=6, show_default=True, help="name length to sweep")
@click.option("--charset", default=C.DEFAULT_CHARSET, show_default=True)
@click.option("-j", "--jobs", type=int, default=0, help="CPU workers (0 = all cores)")
def bench(engine, length, charset, jobs):
    """Measure brute-force throughput (keys/s) and project exhaustion times."""
    total = len(charset) ** length
    gp = [GroupPacket(chash=0x00, mac=b"\x00\x00", ciphertext=b"\x00" * 48,
                      payload_type=0x05, framing="bench")]
    empty = dict(min_ts=2, max_ts=1)  # nothing matches -> full sweep
    eng = engine if engine != "auto" else ("gpu" if _gpu_available() else "cpu")
    click.echo(f"benchmark: length {length}, charset {len(charset)} -> {total:,} candidates, engine {eng}")
    t0 = time.time()
    if eng == "gpu":
        from .gpu import brute_gpu
        brute_gpu(gp, charset=charset, min_len=length, max_len=length,
                  both_prefix=False, progress=_mk_progress(), **empty)
    else:
        n = jobs if jobs and jobs > 0 else (os.cpu_count() or 4)
        click.echo(f"    CPU: {n} worker process(es)")
        brute_cpu(gp, charset=charset, min_len=length, max_len=length,
                  both_prefix=False, processes=n, progress=_mk_progress(), **empty)
    dt_ = time.time() - t0
    rate = total / dt_ if dt_ else 0
    click.echo(f"\n{total:,} candidates in {dt_:.1f}s  =>  {_fmt_rate(rate)}")
    click.echo("projected full exhaustion (single derivation; x2 for #name AND name):")
    for L in (6, 7, 8):
        n = len(charset) ** L
        click.echo(f"    length {L:2}: {n:,} names  ~{_fmt_time(n / rate if rate else 0)}")


@cli.command()
def selftest():
    """Run known-answer vectors (public channel + a real #test packet)."""
    from .packet import parse_group_packet
    ok = True
    raw = "150011C3C1354D619BAE9590E4D177DB7EEAF982F5BDCF78005D75157D9535FA90178F785D"
    gp = parse_group_packet(raw)
    m = crypto.try_decrypt(crypto.PUBLIC_CHANNEL_KEY, gp.chash, gp.mac, gp.ciphertext)
    got = (m.timestamp, m.sender, m.text) if m else None
    exp = (1758484279, "🌲 Tree", "☁️")
    click.echo(f"public-channel vector: {'OK' if got == exp else 'FAIL'}  {got}")
    ok &= got == exp
    raw = ("150320 DD 2CD9 B9 E7 7A 7A B2 CE C9 18 EA AC A3 95 EE 38 AD 98 99 A5 "
           "64 A4 01 AE 22 88 CD C8 83 6C 6E 4E 00 7F 1D D6")
    hit = check_names(["test"], candidate_framings(raw))
    got2 = (hit.name, hit.hashed, hit.message.sender, hit.message.text) if hit else None
    exp2 = ("test", "#test", "42B8C196", "Test")
    click.echo(f"#test real packet    : {'OK' if got2 == exp2 else 'FAIL'}  {got2}")
    ok &= got2 == exp2
    click.secho("ALL PASS" if ok else "FAILURES", fg="green" if ok else "red")
    sys.exit(0 if ok else 1)


def _fmt_rate(n: float) -> str:
    for unit, div in (("G", 1e9), ("M", 1e6), ("k", 1e3)):
        if n >= div:
            return f"{n / div:.1f} {unit}/s"
    return f"{n:.0f} /s"


def _fmt_time(secs: float) -> str:
    if secs < 90:
        return f"{secs:.0f}s"
    if secs < 5400:
        return f"{secs / 60:.1f} min"
    if secs < 86400 * 2:
        return f"{secs / 3600:.1f} h"
    if secs < 86400 * 400:
        return f"{secs / 86400:.1f} days"
    return f"{secs / (86400 * 365):.1f} years"


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
