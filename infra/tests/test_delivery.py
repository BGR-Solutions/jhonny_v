"""Entrega ao menos uma vez após reinícios (US1: SC-004, FR-011, FR-025)."""

from __future__ import annotations

import re

import pytest

from .conftest import (
    ComposeFn,
    LogLine,
    ProbeFn,
    StackEnv,
    WaitFn,
    service_container,
    unique_marker,
    wait_healthy,
)

pytestmark = pytest.mark.disruptive

SEQ = re.compile(r"seq=(\d+)")


def _seqs(lines: list[LogLine]) -> set[int]:
    return {int(m.group(1)) for line in lines if (m := SEQ.search(line.line))}


def _assert_no_gap_across_restart(
    service: str,
    env: StackEnv,
    compose: ComposeFn,
    probe_container: ProbeFn,
    wait_for_lines: WaitFn,
) -> None:
    marker = unique_marker()
    name = probe_container(
        f'i=0; while true; do echo "{marker} seq=$i"; i=$((i+1)); sleep 0.2; done'
    )
    selector = f'{{container="{name}"}} |= "{marker}"'
    before = max(_seqs(wait_for_lines(selector, predicate=lambda ls: len(ls) >= 5)))

    compose("restart", service)
    wait_healthy([service_container(env, service)])

    target = before + 100
    lines = wait_for_lines(
        selector,
        predicate=lambda ls: max(_seqs(ls), default=0) >= target,
        timeout=120,
    )
    seqs = _seqs(lines)
    missing = sorted(set(range(min(seqs), max(seqs) + 1)) - seqs)
    assert not missing, f"{len(missing)} números faltando: {missing[:20]}"


def test_no_loss_when_collector_restarts(
    env: StackEnv, compose: ComposeFn, probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """SC-004: reiniciar o coletor não perde linhas."""
    _assert_no_gap_across_restart(
        "alloy", env, compose, probe_container, wait_for_lines
    )


def test_no_loss_when_socket_proxy_restarts(
    env: StackEnv, compose: ComposeFn, probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """Edge case: reiniciar o proxy de socket não perde linhas."""
    _assert_no_gap_across_restart(
        "socket-proxy", env, compose, probe_container, wait_for_lines
    )


def test_logs_persist_when_loki_is_recreated(
    env: StackEnv, compose: ComposeFn, probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-011: os logs sobrevivem à recriação do contêiner do Loki."""
    marker = unique_marker()
    name = probe_container(f"echo {marker}; sleep 3600")
    selector = f'{{container="{name}"}} |= "{marker}"'
    wait_for_lines(selector)

    compose("rm", "-sf", "loki")
    compose("up", "-d", "--wait", "loki", "loki-gateway", "alloy")
    wait_healthy([service_container(env, s) for s in ("loki", "loki-gateway")])

    wait_for_lines(selector, timeout=60)


def test_backlog_before_collector_start_is_ingested(
    env: StackEnv, compose: ComposeFn, probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-025: linhas emitidas antes de o coletor subir são ingeridas."""
    marker = unique_marker()
    compose("stop", "alloy")
    try:
        name = probe_container(f"echo {marker}-early; sleep 3600")
    finally:
        compose("start", "alloy")
    wait_healthy([service_container(env, "alloy")])
    wait_for_lines(f'{{container="{name}"}} |= "{marker}-early"', timeout=60)
