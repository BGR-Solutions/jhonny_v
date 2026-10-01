"""Conformidade da política de logs só em stdout/stderr (US3).

Cobre SC-006, SC-011, SC-015, FR-016, FR-019 e FR-020.
"""

from __future__ import annotations

import json
import time

import httpx
import pytest

from .conftest import (
    ALL_FILES,
    OBS_SERVICES,
    PROBE_IMAGE,
    ComposeFn,
    StackEnv,
    inspect,
    run,
)

MAX_LOG_BYTES = 31_457_280
IDLE_MINUTES = 5
MAX_LINES_PER_MINUTE = 60
MAX_GROWTH = 1.2


@pytest.fixture(scope="module")
def rendered(compose: ComposeFn, llm_env: dict[str, str]) -> dict:
    """Configuração renderizada das quatro camadas."""
    out = compose("config", "--format", "json", files=ALL_FILES, env=llm_env).stdout
    return json.loads(out)


def test_every_service_rotates_json_file_logs(rendered: dict) -> None:
    """FR-019: todo serviço usa json-file com 10m × 3."""
    wrong = {}
    for name, service in rendered["services"].items():
        logging = service.get("logging") or {}
        options = logging.get("options") or {}
        if (
            logging.get("driver") != "json-file"
            or options.get("max-size") != "10m"
            or str(options.get("max-file")) != "3"
        ):
            wrong[name] = logging
    assert not wrong, wrong


def test_no_log_file_mounts(rendered: dict) -> None:
    """FR-016/SC-006: nenhum volume com destino em diretório ou arquivo de log."""
    offenders = [
        f"{name}:{volume.get('target')}"
        for name, service in rendered["services"].items()
        for volume in service.get("volumes") or []
        if str(volume.get("target", "")).startswith("/var/log")
        or str(volume.get("target", "")).endswith(".log")
    ]
    assert not offenders, offenders


@pytest.mark.parametrize("service", OBS_SERVICES)
def test_obs_services_log_json(compose: ComposeFn, service: str) -> None:
    """FR-020: os serviços da camada obs logam em JSON no stdout/stderr."""
    out = compose("logs", "--no-log-prefix", "--no-color", "--tail", "20", service)
    lines = [line for line in (out.stdout + out.stderr).splitlines() if line.strip()]
    assert lines, f"{service} sem logs"
    for line in lines:
        json.loads(line)


def test_log_files_stay_within_rotation_limit(env: StackEnv) -> None:
    """SC-011: os arquivos de log de cada contêiner da stack ficam ≤ 30 MB."""
    root = run(["docker", "info", "--format", "{{.DockerRootDir}}"]).stdout.strip()
    ids = run(
        [
            "docker",
            "ps",
            "-q",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project={env.project}",
        ]
    ).stdout.split()
    assert ids, "nenhum contêiner da stack em execução"
    script = " ; ".join(f"du -cb /c/{cid}/{cid}-json.log* | tail -1" for cid in ids)
    out = run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{root}/containers:/c:ro",
            PROBE_IMAGE,
            "sh",
            "-c",
            script,
        ]
    ).stdout.split("\n")
    sizes = {cid: int(line.split()[0]) for cid, line in zip(ids, out, strict=False)}
    assert len(sizes) == len(ids), out
    too_big = {
        inspect(cid)["Name"]: size
        for cid, size in sizes.items()
        if size > MAX_LOG_BYTES
    }
    assert not too_big, too_big


@pytest.mark.slow
def test_idle_obs_layer_has_no_feedback_loop(loki: httpx.Client) -> None:
    """SC-015: ociosa, a camada gera ≤ 60 linhas/min e o volume não cresce."""
    start = time.time()
    time.sleep(IDLE_MINUTES * 60 + 15)
    services = "|".join(OBS_SERVICES)
    resp = loki.get(
        "/loki/api/v1/query_range",
        params={
            "query": (f'sum(count_over_time({{compose_service=~"{services}"}}[1m]))'),
            "start": str(int((start + 60) * 1e9)),
            "end": str(int((start + IDLE_MINUTES * 60) * 1e9)),
            "step": "60",
        },
    )
    resp.raise_for_status()
    result = resp.json()["data"]["result"]
    # Minutos sem nenhuma linha não aparecem na série: ficam com 0.
    per_minute = [0] * IDLE_MINUTES
    for ts, count in result[0]["values"] if result else []:
        minute = round((float(ts) - start) / 60)
        if 1 <= minute <= IDLE_MINUTES:
            per_minute[minute - 1] = int(count)
    assert max(per_minute) <= MAX_LINES_PER_MINUTE, per_minute
    assert per_minute[4] <= MAX_GROWTH * per_minute[1], per_minute
