"""Observable collection deadlines, with unique fixture-owned event IDs."""

import base64
import json
import time
import urllib.parse
import urllib.request
from collections import Counter
from uuid import uuid4

import pytest
from conftest import (
    SOURCE_IMAGE,
    Stack,
    docker_command,
    json_object,
    validate_fixture_context,
)
from test_obs_access import gateway


def emit(stack: Stack, service: str, lines: list[str], stream: int = 1) -> None:
    script = (
        "import os;"
        f"fd=os.open('/proc/1/fd/{stream}',os.O_WRONLY);"
        f"os.write(fd,{chr(10).join(lines).encode()!r}+b'\\n');os.close(fd)"
    )
    stack.compose("exec", "-T", service, "python", "-c", script)


def query(stack: Stack, url: str, expression: str | None = None) -> dict[str, object]:
    return read_api(
        stack,
        url,
        "/loki/api/v1/query_range",
        {"query": expression or f'{{project="{stack.project}"}}', "limit": "5000"},
    )


def read_api(
    stack: Stack, url: str, path: str, parameters: dict[str, str]
) -> dict[str, object]:
    params = urllib.parse.urlencode(parameters)
    token = base64.b64encode(f"reader:{stack.password}".encode()).decode()
    req = urllib.request.Request(
        url + path + "?" + params,
        headers={"Authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        return json_object(response.read().decode())


def await_ids(stack: Stack, url: str, ids: set[str], timeout: float = 60) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = json.dumps(query(stack, url))
        if all(value in text for value in ids):
            return text
        time.sleep(1)
    diagnostics = stack.logs("alloy", "logs-gateway", "docker-log-proxy", tail=15)
    raise AssertionError(
        f"{len(ids)} expected event IDs not all visible before deadline\n{diagnostics}"
    )


def log_rows(payload: dict[str, object]) -> list[tuple[dict[str, str], str, str]]:
    data = payload.get("data")
    assert isinstance(data, dict)
    results = data.get("result")
    assert isinstance(results, list)
    rows = []
    for result in results:
        assert isinstance(result, dict)
        labels, values = result.get("stream"), result.get("values")
        assert isinstance(labels, dict) and isinstance(values, list)
        assert all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in labels.items()
        )
        typed_labels = {str(key): str(value) for key, value in labels.items()}
        for value in values:
            assert isinstance(value, list) and len(value) >= 2
            timestamp, line = value[0], value[1]
            assert isinstance(timestamp, str) and timestamp.isdecimal()
            assert isinstance(line, str)
            rows.append((typed_labels, timestamp, line))
    return rows


@pytest.mark.integration
def test_two_sources_both_streams(stack: Stack) -> None:
    url = gateway(stack)
    ids = set()
    origins: dict[str, tuple[str, str]] = {}
    for service in ("source-a", "source-b"):
        for stream in (1, 2):
            batch = [f"obs-{uuid4().hex}" for _ in range(50)]
            ids.update(batch)
            origins.update(
                {
                    event: (service, "stdout" if stream == 1 else "stderr")
                    for event in batch
                }
            )
            emit(stack, service, [json.dumps({"id": value}) for value in batch], stream)
    payload = await_ids(stack, url, ids)
    found = set()
    for labels, _, line in log_rows(json_object(payload)):
        if line.startswith('{"id": "obs-'):
            event = json_object(line).get("id")
            assert isinstance(event, str)
            assert (labels["service"], labels["stream"]) == origins[event]
            assert labels["project"] == stack.project
            found.add(event)
    assert found == ids


@pytest.mark.integration
def test_dynamic_discovery(stack: Stack) -> None:
    url = gateway(stack)
    stack.compose("--profile", "dynamic", "up", "-d", "source-new")
    event = f"new-{uuid4().hex}"
    emit(stack, "source-new", [json.dumps({"id": event})])
    await_ids(stack, url, {event})


@pytest.mark.integration
def test_foreign_project_is_not_ingested(stack: Stack) -> None:
    url = gateway(stack)
    foreign = [f"foreign-{uuid4().hex}" for _ in range(20)]
    payload = "\n".join(json.dumps({"id": value}) for value in foreign)
    script = (
        f"import os,time; os.write(1,{payload.encode()!r}+b'\\n'); time.sleep(3600)"
    )
    container = docker_command(
        "run",
        "-d",
        "--network",
        "none",
        "--label",
        f"com.docker.compose.project={stack.project}-foreign",
        "--label",
        "com.docker.compose.service=foreign-source",
        SOURCE_IMAGE,
        "python",
        "-u",
        "-c",
        script,
    ).stdout.strip()
    try:
        time.sleep(10)
        control = f"control-{uuid4().hex}"
        emit(stack, "source-a", [json.dumps({"id": control})])
        await_ids(stack, url, {control})
        all_events = json.dumps(query(stack, url, '{service=~".+"}'))
        assert control in all_events
        assert all(event not in all_events for event in foreign)
    finally:
        docker_command("rm", "-f", container)


@pytest.mark.integration
def test_origin_without_service_is_diagnosed(stack: Stack) -> None:
    gateway(stack)
    container = docker_command(
        "run",
        "-d",
        "--network",
        "none",
        "--label",
        f"com.docker.compose.project={stack.project}",
        SOURCE_IMAGE,
        "python",
        "-c",
        "import time; time.sleep(3600)",
    ).stdout.strip()
    try:
        failure = stack.run_service(
            "alloy",
            options=("--entrypoint", "/usr/local/bin/obs-tools"),
            command=("preflight", "--service", "alloy"),
        )
        assert json_object(failure.stderr)["code"] == "source_missing_compose_service"
    finally:
        docker_command("rm", "-f", container)


@pytest.mark.integration
def test_unreadable_log_driver_has_diagnostic(stack: Stack) -> None:
    gateway(stack)
    container = docker_command(
        "run",
        "-d",
        "--network",
        "none",
        "--log-driver",
        "none",
        "--label",
        f"com.docker.compose.project={stack.project}",
        "--label",
        "com.docker.compose.service=unsupported",
        SOURCE_IMAGE,
        "python",
        "-c",
        "import time; time.sleep(3600)",
    ).stdout.strip()
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            logs = stack.logs("alloy")
            events = [json_object(line) for line in logs.splitlines() if line.strip()]
            if any(
                event.get("level") == "error" and "logging driver" in str(event).lower()
                for event in events
            ):
                break
            time.sleep(1)
        else:
            raise AssertionError("Unsupported log driver not explicitly diagnosed")
    finally:
        docker_command("rm", "-f", container)


@pytest.mark.integration
def test_parsing_preserves_lines_context_and_instance(stack: Stack) -> None:
    url = gateway(stack)
    before = time.time_ns()
    expected: dict[str, str] = {}
    for _ in range(4):
        event_id = uuid4().hex
        event: dict[str, object] = {
            "id": event_id,
            "distributed_context": True,
            "trace_id": uuid4().hex,
            "span_id": uuid4().hex[:16],
            "severity": "info",
            "timestamp": "2001-01-01T00:00:00Z",
            "message": "a\u00e7\u00e3o with whitespace",
        }
        validate_fixture_context(event)
        expected["  " + json.dumps(event, ensure_ascii=False) + "  "] = "json"
        for prefix in ("text-", "{invalid-"):
            event_id = uuid4().hex
            expected[prefix + event_id] = "text_or_invalid_json"
    extra = uuid4().hex
    expected.update(
        {
            json.dumps({"no_message": extra}): "json",
            json.dumps([extra, 1]): "json",
            json.dumps(extra): "json",
            "42": "json",
            "true": "json",
            "null": "json",
        }
    )
    duplicate = json.dumps({"id": "duplicate-" + uuid4().hex})
    expected[duplicate] = "json"
    emit(stack, "source-a", list(expected))
    emit(stack, "source-a", [duplicate])
    expected_counts = Counter(list(expected))
    expected_counts[duplicate] += 1
    deadline = time.monotonic() + 60
    while True:
        rows = [
            row
            for row in log_rows(query(stack, url))
            if row[0].get("service") == "source-a"
        ]
        counts = Counter(line for _, _, line in rows)
        if counts == expected_counts:
            break
        assert time.monotonic() < deadline, (
            "Expected source lines and duplicate counts not visible within 60s: "
            + repr(counts - expected_counts)
            + repr(expected_counts - counts)
        )
        time.sleep(1)
    source = stack.compose("ps", "-q", "source-a").stdout.strip()
    name = (
        docker_command("inspect", "--format", "{{.Name}}", source)
        .stdout.strip()
        .lstrip("/")
    )
    assert {line for _, _, line in rows} == set(expected)
    assert sum(line == duplicate for _, _, line in rows) == 2
    for labels, timestamp, line in rows:
        assert labels["parse_status"] == expected[line]
        assert before <= int(timestamp) <= time.time_ns()
    by_instance = query(
        stack,
        url,
        f'{{project="{stack.project}",service="source-a"}} | container_id="{source}" | container_name="{name}"',
    )
    assert {line for _, _, line in log_rows(by_instance)} == set(expected)
    series = read_api(
        stack, url, "/loki/api/v1/series", {"match[]": f'{{project="{stack.project}"}}'}
    )
    indexed = series.get("data")
    assert isinstance(indexed, list) and indexed
    for item in indexed:
        assert isinstance(item, dict)
        assert set(item) == {"project", "service", "stream", "parse_status"}

    stack.compose("up", "-d", "--force-recreate", "source-a")
    new_source = stack.compose("ps", "-q", "source-a").stdout.strip()
    assert new_source != source
    new_id = "recreated-" + uuid4().hex
    emit(stack, "source-a", [json.dumps({"id": new_id})])
    await_ids(stack, url, {new_id})
    old_rows = query(
        stack,
        url,
        f'{{project="{stack.project}",service="source-a"}} | container_id="{source}"',
    )
    new_rows = query(
        stack,
        url,
        f'{{project="{stack.project}",service="source-a"}} | container_id="{new_source}"',
    )
    assert {line for _, _, line in log_rows(old_rows)} == set(expected)
    assert new_id in json.dumps(new_rows)
    assert not any(line in expected for _, _, line in log_rows(new_rows))
