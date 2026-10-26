"""Durability and bounded recovery against fixture-owned services."""

import json
import re
import time
from uuid import uuid4

import pytest
from conftest import ROOT, Stack, json_object
from test_obs_access import gateway, request
from test_obs_ingestion import await_ids, emit


def test_delivery_retry_parameters() -> None:
    config = (ROOT / "infra" / "alloy" / "config.alloy").read_text(encoding="utf-8")
    for name, value in {
        "batch_wait": '"1s"',
        "batch_size": '"1MiB"',
        "remote_timeout": '"5s"',
        "min_backoff_period": '"1s"',
        "max_backoff_period": '"5s"',
        "max_backoff_retries": "30",
    }.items():
        assert re.search(r"\b" + name + r"\s*=\s*" + re.escape(value), config)


@pytest.mark.integration
def test_restarts_preserve_data_and_resume_collection(stack: Stack) -> None:
    url = gateway(stack)
    ids = {f"persist-{uuid4().hex}" for _ in range(20)}
    emit(stack, "source-a", [json.dumps({"id": event}) for event in ids])
    await_ids(stack, url, ids)
    stack.compose("restart", "loki")
    stack.compose("up", "-d", "--wait", "--wait-timeout", "120", "loki")
    await_ids(stack, url, ids)
    stack.compose("restart", "alloy")
    stack.compose("up", "-d", "--wait", "--wait-timeout", "120", "alloy")
    resumed = f"resumed-{uuid4().hex}"
    emit(stack, "source-a", [json.dumps({"id": resumed})])
    await_ids(stack, url, ids | {resumed})


@pytest.mark.integration
def test_thirty_second_outage_recovers_twenty_events(stack: Stack) -> None:
    url = gateway(stack)
    baseline = "before-outage-" + uuid4().hex
    emit(stack, "source-a", [json.dumps({"id": baseline})])
    await_ids(stack, url, {baseline})
    stack.compose("stop", "-t", "10", "loki")
    stopped = time.monotonic()
    ids = {f"outage-{uuid4().hex}" for _ in range(20)}
    emit(stack, "source-a", [json.dumps({"id": event}) for event in ids])
    assert request(url + "/loki/api/v1/labels", "reader", stack.password) in {
        502,
        503,
        504,
    }
    time.sleep(max(0, 30 - (time.monotonic() - stopped)))
    logs = stack.logs("logs-gateway")
    events = [json_object(line) for line in logs.splitlines() if line.strip()]
    assert any(
        event.get("service") == "logs-gateway"
        and event.get("method") == "POST"
        and event.get("status") in {502, 503, 504}
        for event in events
    ), (
        "Destination outage did not produce an explicit delivery diagnostic: "
        + json.dumps(events[-12:])
        + stack.logs("alloy", tail=12)
    )
    for service in ("alloy", "source-a", "source-b"):
        assert stack.compose("ps", "--status", "running", "-q", service).stdout.strip()
    stack.compose("up", "-d", "--wait", "--wait-timeout", "120", "loki")
    restored = time.monotonic()
    new_id = f"after-outage-{uuid4().hex}"
    emit(stack, "source-a", [json.dumps({"id": new_id})])
    await_ids(
        stack, url, ids | {new_id}, timeout=max(0, 60 - (time.monotonic() - restored))
    )
