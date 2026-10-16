"""Truncamento de linhas longas e timestamp do Docker (US1: SC-013)."""

from __future__ import annotations

from datetime import UTC, datetime

from .conftest import ProbeFn, WaitFn, run, unique_marker

MAX_LINE = 262_144


def test_long_line_is_truncated(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-023: uma linha de 300.000 caracteres é armazenada com 256 KB."""
    name = probe_container(
        "head -c 300000 /dev/zero | tr '\\0' a; echo; sleep 3600",
    )
    lines = wait_for_lines(f'{{container="{name}"}} |= "aaaa"', timeout=60)
    assert len(lines) == 1
    assert len(lines[0].line) == MAX_LINE


def _rfc3339_to_ns(value: str) -> int:
    whole, _, frac = value.rstrip("Z").partition(".")
    seconds = datetime.fromisoformat(whole).replace(tzinfo=UTC).timestamp()
    return int(seconds) * 1_000_000_000 + int((frac or "0").ljust(9, "0")[:9])


def test_timestamp_matches_docker(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-024: o timestamp no Loki é o do Docker (tolerância de 1 ms)."""
    marker = unique_marker()
    name = probe_container(f"echo {marker}; sleep 3600")
    stored = wait_for_lines(f'{{container="{name}"}} |= "{marker}"')

    docker_line = run(["docker", "logs", "-t", name]).stdout.splitlines()[0]
    docker_ts = _rfc3339_to_ns(docker_line.split(" ", 1)[0])
    assert abs(stored[0].ts_ns - docker_ts) <= 1_000_000
