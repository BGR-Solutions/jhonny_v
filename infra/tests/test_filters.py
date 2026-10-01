"""Filtros por origem e por atributos estruturados (US2: SC-005, FR-005 a FR-008)."""

from __future__ import annotations

import time
import uuid

import httpx

from .conftest import ALLOWED_LABELS, ProbeFn, QueryFn, WaitFn


def _json_emitter(service: str, trace: str) -> str:
    lines = [
        f'{{"level":"ERROR","trace_id":"{trace}-a","span_id":"s1","msg":"boom"}}',
        f'{{"level":"warning","trace_id":"{trace}-b","span_id":"s2","msg":"careful"}}',
        f'{{"level":"Info","trace_id":"{trace}-c","span_id":"s3","msg":"hello"}}',
        f'{{"msg":"no level {service}"}}',
    ]
    return "; ".join(f"echo '{line}'" for line in lines) + "; sleep 3600"


def test_structured_filters(
    probe_container: ProbeFn, wait_for_lines: WaitFn, query_lines: QueryFn
) -> None:
    """SC-005: filtros por serviço, nível e trace sem falsos positivos."""
    suffix = uuid.uuid4().hex[:8]
    service_a, service_b = f"qs-svc-a-{suffix}", f"qs-svc-b-{suffix}"
    trace = uuid.uuid4().hex
    for service in (service_a, service_b):
        probe_container(
            _json_emitter(service, trace if service == service_a else "other"),
            labels={
                "com.docker.compose.project": "qs",
                "com.docker.compose.service": service,
            },
        )
    sel_a = f'{{compose_service="{service_a}"}}'
    wait_for_lines(sel_a, predicate=lambda ls: len(ls) >= 4)
    wait_for_lines(
        f'{{compose_service="{service_b}"}}', predicate=lambda ls: len(ls) >= 4
    )

    for level, expected in (("error", "ERROR"), ("warn", "warning"), ("info", "Info")):
        lines = query_lines(f'{sel_a} | detected_level="{level}"')
        assert [line.labels.get("level") for line in lines] == [expected], level

    lines = query_lines(f'{sel_a} | trace_id="{trace}-a"')
    assert len(lines) == 1 and '"boom"' in lines[0].line
    assert lines[0].labels.get("span_id") == "s1"

    only_b = query_lines(f'{{compose_service="{service_b}"}}')
    assert only_b and all(service_b in (x.labels["compose_service"]) for x in only_b)
    assert all(x.labels.get("service_name") == service_b for x in only_b)


def test_labels_have_bounded_cardinality(loki: httpx.Client) -> None:
    """FR-006/FR-007: só os rótulos permitidos são indexados."""
    start = time.time_ns() - int(3600 * 1e9)
    resp = loki.get("/loki/api/v1/labels", params={"start": start})
    resp.raise_for_status()
    labels = set(resp.json()["data"])
    assert labels <= ALLOWED_LABELS, labels - ALLOWED_LABELS


def test_non_json_lines_are_kept(
    probe_container: ProbeFn, wait_for_lines: WaitFn
) -> None:
    """FR-008: linhas não JSON passam intactas e são consultáveis."""
    name = probe_container("echo '{broken json'; echo plain >&2; sleep 3600")
    lines = wait_for_lines(f'{{container="{name}"}}', predicate=lambda ls: len(ls) >= 2)
    assert sorted(line.line.strip() for line in lines) == ["plain", "{broken json"]
