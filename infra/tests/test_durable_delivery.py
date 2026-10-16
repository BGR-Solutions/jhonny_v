"""Recuperação de registros mascarados duráveis, sem depender do produtor."""

from __future__ import annotations

import re
import time
import uuid

import pytest

from .conftest import (
    PROBE_IMAGE,
    ComposeFn,
    ProbeFn,
    StackEnv,
    WaitFn,
    run,
    service_container,
    unique_marker,
    wait_healthy,
)

pytestmark = pytest.mark.disruptive


def _metrics(container: str) -> str:
    return run(
        [
            "docker",
            "exec",
            container,
            "bash",
            "-c",
            "exec 3<>/dev/tcp/127.0.0.1/12345; "
            "printf 'GET /metrics HTTP/1.0\\r\\n\\r\\n' >&3; cat <&3",
        ]
    ).stdout


def _receipts(metrics: str, container: str, stream: str) -> int:
    for line in metrics.splitlines():
        if (
            line.startswith("loki_source_docker_durable_receipts_total{")
            and f'container="{container}"' in line
            and f'stream="{stream}"' in line
        ):
            return int(float(line.rsplit(" ", 1)[1]))
    return 0


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_committed_queue_survives_sigkill_and_producer_removal(
    stream: str,
    env: StackEnv,
    compose: ComposeFn,
    probe_container: ProbeFn,
    wait_for_lines: WaitFn,
) -> None:
    """FR-026: 40 recibos duráveis sobrevivem a SIGKILL e produtor removido."""
    marker = unique_marker("durable")
    raw_value = uuid.uuid4().hex + uuid.uuid4().hex
    count = 40
    alloy = service_container(env, "alloy")
    name = ""
    compose("stop", "loki-gateway")
    try:
        redirect = " >&2" if stream == "stderr" else ""
        name = probe_container(
            f'i=0; while [ "$i" -lt {count} ]; do '
            f'echo "{marker} seq=$i token={raw_value}"{redirect}; '
            "i=$((i+1)); done; sleep 3600",
            auto_remove=False,
        )
        deadline = time.monotonic() + 90
        while _receipts(_metrics(alloy), name, stream) < count:
            assert time.monotonic() < deadline, "faltam recibos duráveis"
            time.sleep(1)
        # Não basta esperar: o contador é emitido somente depois do fsync.
        metrics = _metrics(alloy)
        assert _receipts(metrics, name, stream) == count
        pending = re.search(
            r"^loki_source_docker_durable_pending_records(?:\{[^\n]*\})? (\d+)",
            metrics,
            re.MULTILINE,
        )
        assert pending and int(pending.group(1)) >= count
        scan = run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{env.project}-alloy-data:/state:ro",
                PROBE_IMAGE,
                "grep",
                "-arl",
                raw_value,
                "/state",
            ],
            check=False,
        )
        assert scan.returncode == 1, "segredo bruto encontrado no estado durável"
        run(["docker", "rm", "-f", name])
        run(["docker", "update", "--restart=no", alloy])
        run(["docker", "kill", "--signal=KILL", alloy])
        compose("rm", "-f", "alloy")
        compose("up", "-d", "--no-deps", "alloy")
        wait_healthy([alloy])
    finally:
        compose("start", "loki-gateway")
        compose("up", "-d", "--no-deps", "alloy")
        wait_healthy([alloy, service_container(env, "loki-gateway")])

    stored = wait_for_lines(
        f'{{container="{name}",stream="{stream}"}} |= "{marker}"',
        predicate=lambda lines: len(
            {
                int(match.group(1))
                for line in lines
                if (match := re.search(r"seq=(\d+)", line.line))
            }
        )
        == count,
        timeout=180,
    )
    assert all(raw_value not in line.line for line in stored)
    assert all("<redacted>" in line.line for line in stored)


def test_bounded_queue_pauses_and_resumes_without_dropping(
    request: pytest.FixtureRequest,
    env: StackEnv,
    compose: ComposeFn,
    probe_container: ProbeFn,
    wait_for_lines: WaitFn,
) -> None:
    """Fila cheia suspende confirmação; espaço liberado retoma leitura."""
    alloy = service_container(env, "alloy")
    marker = unique_marker("bounded")
    count = 80
    limit = 16_384

    def restore() -> None:
        compose("start", "loki-gateway")
        compose("up", "-d", "--force-recreate", "--no-deps", "alloy")
        wait_healthy([alloy, service_container(env, "loki-gateway")])

    request.addfinalizer(restore)
    compose(
        "up",
        "-d",
        "--force-recreate",
        "--no-deps",
        "alloy",
        env={"ALLOY_QUEUE_MAX_BYTES": str(limit)},
    )
    wait_healthy([alloy])
    compose("stop", "loki-gateway")
    try:
        name = probe_container(
            f'i=0; while [ "$i" -lt {count} ]; do '
            f'echo "{marker} seq=$i {"x" * 512}"; '
            "i=$((i+1)); done; sleep 3600"
        )
        deadline = time.monotonic() + 90
        while True:
            metrics = _metrics(alloy)
            paused = re.search(
                r"^loki_source_docker_durable_paused_sources" r"(?:\{[^\n]*\})? (\d+)",
                metrics,
                re.MULTILINE,
            )
            if paused and int(paused.group(1)) > 0:
                break
            assert time.monotonic() < deadline, "fila cheia não suspendeu a origem"
            time.sleep(1)
        pending_bytes = re.search(
            r"^loki_source_docker_durable_pending_bytes(?:\{[^\n]*\})? (\d+)",
            metrics,
            re.MULTILINE,
        )
        assert pending_bytes and int(pending_bytes.group(1)) <= limit
        assert _receipts(metrics, name, "stdout") < count
    finally:
        compose("start", "loki-gateway")
        wait_healthy([service_container(env, "loki-gateway")])
    wait_for_lines(
        f'{{container="{name}"}} |= "{marker}"',
        predicate=lambda lines: len(
            {
                int(match.group(1))
                for line in lines
                if (match := re.search(r"seq=(\d+)", line.line))
            }
        )
        == count,
        timeout=180,
    )
    assert _receipts(_metrics(alloy), name, "stdout") == count
