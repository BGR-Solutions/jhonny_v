"""Ingestão de stdout/stderr de todos os contêineres (US1: SC-001, SC-002, SC-003)."""

from __future__ import annotations

import time

import httpx

from .conftest import (
    BASE_FILES,
    ComposeFn,
    ProbeFn,
    QueryFn,
    WaitFn,
    unique_marker,
)


def _label_values(loki: httpx.Client, label: str) -> set[str]:
    start = time.time_ns() - int(3600 * 1e9)
    resp = loki.get(f"/loki/api/v1/label/{label}/values", params={"start": start})
    resp.raise_for_status()
    return set(resp.json().get("data") or [])


def test_all_compose_services_and_standalone_are_ingested(
    loki: httpx.Client, compose: ComposeFn, probe_container: ProbeFn
) -> None:
    """SC-001/FR-002: todo serviço da stack e um contêiner avulso aparecem."""
    services = set(compose("config", "--services", files=BASE_FILES).stdout.split())
    name = probe_container("while true; do echo standalone-alive; sleep 1; done")

    deadline = time.monotonic() + 60
    while True:
        missing = services - _label_values(loki, "compose_service")
        standalone_seen = name in _label_values(loki, "container")
        if not missing and standalone_seen:
            return
        assert time.monotonic() < deadline, (
            f"serviços sem logs no Loki: {sorted(missing)}; "
            f"contêiner avulso visto: {standalone_seen}"
        )
        time.sleep(2)


def test_new_container_is_queryable_within_30s(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """SC-003: um contêiner novo fica consultável em até 30 s."""
    marker = unique_marker()
    started = time.monotonic()
    name = probe_container(f"while true; do echo {marker}; sleep 1; done")
    wait_for_lines(f'{{container="{name}"}} |= "{marker}"', timeout=30)
    assert time.monotonic() - started <= 30


def test_short_lived_container_is_ingested(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """Edge case: contêiner que imprime uma linha e encerra em ~5 s.

    O coletor descobre contêineres por polling (1 s) e lê os logs pela API do
    Docker: vidas a partir de ~5 s são garantidas; mais curtas são best-effort.
    Sem `--rm`, porque a remoção automática apaga o log no encerramento.
    """
    marker = unique_marker()
    name = probe_container(f"echo {marker}; sleep 5", auto_remove=False)
    wait_for_lines(f'{{container="{name}"}} |= "{marker}"', timeout=60)


def test_stdout_and_stderr_are_distinguishable(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-004: stdout e stderr chegam com o rótulo `stream` correto."""
    marker = unique_marker()
    name = probe_container(
        f"echo {marker}-out; echo {marker}-err >&2; sleep 3600",
    )
    lines = wait_for_lines(
        f'{{container="{name}"}} |= "{marker}"',
        predicate=lambda ls: len(ls) >= 2,
    )
    streams = {line.line.strip(): line.labels.get("stream") for line in lines}
    assert streams[f"{marker}-out"] == "stdout"
    assert streams[f"{marker}-err"] == "stderr"


def test_emitted_line_is_queryable_within_10s(
    probe_container: ProbeFn, wait_for_lines: WaitFn, query_lines: QueryFn
) -> None:
    """SC-002: uma linha com timestamp embutido fica consultável em até 10 s."""
    marker = unique_marker()
    name = probe_container(
        f'while true; do echo "{marker} emitted=$(date +%s)"; sleep 0.5; done'
    )
    selector = f'{{container="{name}"}} |= "{marker}"'
    wait_for_lines(selector, timeout=60)

    reference = int(time.time()) + 1
    started = time.monotonic()

    def emitted_after_reference(lines: list) -> bool:
        return any(
            int(line.line.rsplit("emitted=", 1)[1]) >= reference for line in lines
        )

    wait_for_lines(selector, predicate=emitted_after_reference, timeout=15)
    # A linha de referência é emitida até ~1 s depois de `started`.
    assert time.monotonic() - started <= 11
