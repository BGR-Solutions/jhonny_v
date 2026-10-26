"""Continuous retention qualification: physical objects, never forced flush."""

import json
import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from conftest import (
    ROOT,
    SOURCE_IMAGE,
    Stack,
    docker_command,
    json_object,
    network_request,
    storage_snapshot,
)
from test_obs_access import gateway
from test_obs_config import load_mapping
from test_obs_ingestion import query, read_api

SECOND = 1_000_000_000
DAY = 86400 * SECOND


def test_retention_parameters() -> None:
    from conftest import ROOT

    config = load_mapping(ROOT / "infra" / "loki" / "config.yaml")
    ingester = config.get("ingester")
    compactor = config.get("compactor")
    assert isinstance(ingester, dict) and isinstance(compactor, dict)
    for key, value in {
        "max_chunk_age": "3m",
        "chunk_idle_period": "1m",
        "flush_check_period": "30s",
        "chunk_retain_period": "0s",
    }.items():
        assert ingester.get(key) == value
    for compactor_key, compactor_value in {
        "compaction_interval": "30s",
        "apply_retention_interval": "1m",
        "retention_delete_delay": "3m",
        "retention_enabled": True,
        "delete_request_store": "filesystem",
    }.items():
        assert compactor.get(compactor_key) == compactor_value
    storage = config.get("storage_config")
    limits = config.get("limits_config")
    assert isinstance(storage, dict) and isinstance(limits, dict)
    shipper = storage.get("tsdb_shipper")
    assert isinstance(shipper, dict)
    assert shipper.get("resync_interval") == "30s"
    assert limits.get("query_timeout") == "1m"


def push(stack: Stack, service: str, values: list[tuple[int, str]]) -> None:
    response = network_request(
        f"{stack.project}_obs-ingest",
        "http://logs-gateway:8081/loki/api/v1/push",
        "writer",
        stack.write_password,
        "POST",
        json.dumps(
            {
                "streams": [
                    {
                        "stream": {
                            "project": stack.project,
                            "service": service,
                            "stream": "stdout",
                            "parse_status": "json",
                        },
                        "values": [
                            [str(timestamp), json.dumps({"id": event})]
                            for timestamp, event in values
                        ],
                    }
                ]
            }
        ),
    )
    assert response["status"] == 204, "Synthetic retention sample rejected"


def retention_query(stack: Stack, url: str, first: int) -> str:
    result = read_api(
        stack,
        url,
        "/loki/api/v1/query_range",
        {
            "query": f'{{project="{stack.project}",service=~"retention-.+"}}',
            "start": str(first - SECOND),
            "end": str(time.time_ns()),
            "limit": "5000",
        },
    )
    return json.dumps(result)


@pytest.mark.integration
def test_storage_observer_measures_removal(
    stack: Stack, storage_observer: Callable[[], str]
) -> None:
    volume = f"{stack.project}_loki-data"
    docker_command("volume", "create", "--label", f"obs.test={stack.project}", volume)
    observer = storage_observer()
    removed = docker_command(
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=volume,source={volume},target=/data",
        SOURCE_IMAGE,
        "python",
        "-c",
        (
            "import pathlib,time,json;"
            "p=pathlib.Path('/data/compactor/retention/test/markers/fixture');"
            "p.parent.mkdir(parents=True);p.touch();time.sleep(1);"
            "p.unlink();print(json.dumps({'removed_at':time.time()}))"
        ),
    )
    actual = json_object(removed.stdout).get("removed_at")
    assert isinstance(actual, (float, int))
    events = [
        json_object(line)
        for line in docker_command("logs", observer).stdout.splitlines()
    ]
    assert len(events) == 1
    assert events[0].get("path") == "compactor/retention/test/markers/fixture"
    observed = events[0].get("removed_at")
    assert isinstance(observed, (float, int))
    assert 0 <= observed - actual <= 0.5, "Observer missed subsecond removal timing"


@pytest.mark.integration
@pytest.mark.retention
def test_continuous_physical_retention(
    stack: Stack,
    tmp_path: Path,
    record_property: Callable[[str, object], None],
    storage_observer: Callable[[], str],
) -> None:
    config = load_mapping(ROOT / "infra" / "loki" / "config.yaml")
    config["querier"] = {"query_ingesters_within": "0s"}
    ingester = config.get("ingester")
    assert isinstance(ingester, dict)
    # Loki compares the infinite-lookback sentinel to time.Duration(-1).
    ingester["query_store_max_look_back_period"] = "-1ns"
    config_path = tmp_path / "retention-config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    overlay = tmp_path / "compose.retention.yaml"
    overlay.write_text(
        yaml.safe_dump(
            {
                "services": {
                    "loki": {
                        "volumes": [
                            {
                                "type": "bind",
                                "source": str(config_path),
                                "target": "/etc/loki/config.yaml",
                                "read_only": True,
                            }
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    stack = replace(stack, retention="24h", overlays=(overlay,))
    url = gateway(stack)
    active_response = network_request(
        f"{stack.project}_obs-storage", "http://loki:3100/config"
    )
    active_body = active_response.get("body")
    assert isinstance(active_body, str)
    active: object = yaml.safe_load(active_body)
    assert isinstance(active, dict)
    active_querier = active.get("querier")
    assert isinstance(active_querier, dict)
    active_ingester = active.get("ingester")
    assert isinstance(active_ingester, dict)
    assert active_ingester.get("query_store_max_look_back_period") == "-1ns"
    # Loki's config endpoint omits this field when its duration is zero.
    assert "query_ingesters_within" not in active_querier
    cid = stack.compose("ps", "-q", "loki").stdout.strip()
    identity = docker_command(
        "inspect", "--format", "{{.State.StartedAt}} {{.RestartCount}}", cid
    ).stdout
    observer = storage_observer()
    now = time.time_ns()
    sample = [
        (now - DAY + seconds * SECOND, f"retention-{uuid4().hex}")
        for seconds in (180, 210, 300, 240)
    ]
    push(stack, "retention-separate", [sample[0]])
    push(stack, "retention-mixed", sample[1:])
    control = f"control-{uuid4().hex}"
    push(stack, "retention-control", [(now, control)])
    visible_deadline = time.monotonic() + 60
    while time.monotonic() < visible_deadline:
        initial = retention_query(stack, url, sample[0][0])
        if all(event in initial for _, event in sample) and control in initial:
            break
        time.sleep(1)
    else:
        metrics = network_request(
            f"{stack.project}_obs-storage", "http://loki:3100/metrics"
        ).get("body")
        assert isinstance(metrics, str)
        details = {
            "query_data": json.loads(initial).get("data"),
            "sample_timestamps": [stamp for stamp, _ in sample],
            "snapshot": storage_snapshot(stack),
            "active_querier": active_querier,
            "active_ingester": active.get("ingester"),
            "recent_query": query(stack, url),
            "ingestion_metrics": [
                line
                for line in metrics.splitlines()
                if line.startswith(
                    (
                        "loki_distributor_lines_received_total",
                        "loki_ingester_memory_streams",
                        "loki_ingester_memory_chunks",
                        "loki_discarded",
                    )
                )
            ],
            "loki_logs": stack.logs("loki", tail=100),
        }
        raise AssertionError(
            "Retention samples not confirmed before expiration: " + json.dumps(details)
        )

    timestamps = {timestamp // 1_000_000 for timestamp, _ in sample}
    expected_tables = {f"index_{timestamp // DAY}" for timestamp, _ in sample}
    covered: set[int] = set()
    observed: dict[str, float] = {}
    valid_paths: set[str] = set()
    deletion_times: dict[str, float] = {}
    marker_paths: set[str] = set()
    marker_created: dict[str, float] = {}
    marker_removed: dict[str, float] = {}
    first_marker: float | None = None
    max_amplitude = 0
    saw_index = False
    first_flush: float | None = None
    index_seen: float | None = None
    deadline = max(timestamp + DAY for timestamp, _ in sample) / SECOND + 1800
    next_emit = time.monotonic() + 30
    while time.time() <= deadline:
        snapshot = storage_snapshot(stack)
        snapshot_at = time.time()
        removal_events = docker_command("logs", observer)
        assert not removal_events.stderr.strip(), "Storage observer reported an error"
        physical_removals: dict[str, float] = {}
        for line in removal_events.stdout.splitlines():
            event = json_object(line)
            path, removed_at = event.get("path"), event.get("removed_at")
            assert isinstance(path, str) and isinstance(removed_at, (float, int))
            physical_removals[path] = float(removed_at)
        chunks, indexes, markers = (
            snapshot.get("chunks"),
            snapshot.get("indexes"),
            snapshot.get("markers"),
        )
        assert (
            isinstance(chunks, list)
            and isinstance(indexes, list)
            and isinstance(markers, list)
        )
        current: set[str] = set()
        for raw in chunks:
            assert isinstance(raw, dict)
            path, start, end = (
                raw.get("path"),
                raw.get("from_ms"),
                raw.get("through_ms"),
            )
            assert (
                isinstance(path, str)
                and isinstance(start, int)
                and isinstance(end, int)
            )
            current.add(path)
            relevant = {stamp for stamp in timestamps if start <= stamp <= end}
            if relevant:
                max_amplitude = max(max_amplitude, end - start)
                assert (
                    end - start <= 240_000
                ), "Mixed-age chunk exceeded the 4m amplitude budget"
                covered.update(relevant)
                observed.setdefault(path, min(relevant) / 1000 + 86400 + 1800)
                if first_flush is None:
                    first_flush = time.time()
                    assert first_flush - now / SECOND <= 120, "Flush exceeded 2m budget"
            if start >= now // 1_000_000 - 1000:
                valid_paths.add(path)
        assert valid_paths <= current, "Unexpired physical chunks disappeared"
        seen_tables = {
            table
            for table in expected_tables
            if any(
                isinstance(index, dict)
                and "/" + table + "/" in "/" + str(index.get("path"))
                for index in indexes
            )
        }
        if seen_tables == expected_tables and first_flush is not None:
            saw_index = True
            if index_seen is None:
                index_seen = time.time()
                assert (
                    index_seen - first_flush <= 1020
                ), "Index publication exceeded 17m"
        if first_flush is not None and not saw_index:
            assert time.time() - first_flush <= 1020, "Index publication exceeded 17m"
        if first_flush is None:
            assert time.time() - now / SECOND <= 120, "Flush exceeded 2m budget"
        if not deletion_times:
            for marker in markers:
                assert isinstance(marker, dict)
                path = marker.get("path")
                assert isinstance(path, str)
                if "/markers/" in "/" + path:
                    marker_paths.add(path)
                    name = path.rsplit("/", 1)[-1]
                    assert name.isdecimal(), "Unexpected deletion marker name"
                    marker_created.setdefault(path, int(name) / SECOND)
                    if first_marker is None:
                        first_marker = time.time()
        if index_seen is not None:
            eligible = max(index_seen, sample[0][0] / SECOND + 86400)
            if first_marker is None:
                assert time.time() - eligible <= 120, "Retention marking exceeded 2m"
            else:
                assert first_marker - eligible <= 120, "Retention marking exceeded 2m"
        for path, object_deadline in observed.items():
            if path not in current:
                assert path in physical_removals, "Physical removal not observed"
                deletion_times.setdefault(path, physical_removals[path])
                assert (
                    deletion_times[path] <= object_deadline
                ), "Physical deletion exceeded individual 30m deadline"
            else:
                assert (
                    time.time() <= object_deadline
                ), "Expired physical chunk remains after individual deadline"
        text = retention_query(stack, url, sample[0][0])
        assert control in text, "Unexpired control event lost"
        live_markers = {
            str(marker["path"]) for marker in markers if isinstance(marker, dict)
        }
        for path, created in marker_created.items():
            if path in physical_removals:
                marker_removed.setdefault(path, physical_removals[path])
            elif path not in live_markers:
                assert path in physical_removals, "Marker removal not observed"
            removed_or_now = marker_removed.get(path, snapshot_at)
            assert (
                removed_or_now - created <= 270
            ), "Sweeper exceeded 1m30s after 3m delay"
        if (
            covered == timestamps
            and observed
            and valid_paths
            and saw_index
            and marker_paths
            and not (marker_paths & live_markers)
            and set(observed) <= set(deletion_times)
            and all(event not in text for _, event in sample)
        ):
            record_property("observed_old_chunks", len(observed))
            record_property("covered_sample_timestamps", len(covered))
            record_property("observed_marker_files", len(marker_paths))
            record_property("max_chunk_amplitude_seconds", max_amplitude / 1000)
            record_property(
                "max_sweeper_after_delete_delay_seconds",
                max(
                    marker_removed[path] - created - 180
                    for path, created in marker_created.items()
                ),
            )
            record_property(
                "retention_marking_seconds",
                (
                    first_marker - max(index_seen, sample[0][0] / SECOND + 86400)
                    if first_marker and index_seen
                    else None
                ),
            )
            record_property(
                "first_flush_seconds",
                first_flush - now / SECOND if first_flush else None,
            )
            record_property(
                "index_publish_seconds",
                index_seen - first_flush if index_seen and first_flush else None,
            )
            record_property(
                "max_removal_after_expiration_seconds",
                max(
                    deletion_times[path] - (object_deadline - 1800)
                    for path, object_deadline in observed.items()
                ),
            )
            break
        assert (
            docker_command(
                "inspect", "--format", "{{.State.StartedAt}} {{.RestartCount}}", cid
            ).stdout
            == identity
        ), "Retention qualification restarted Loki"
        if time.monotonic() >= next_emit:
            current_time = time.time_ns()
            push(
                stack,
                "retention-mixed",
                [(current_time - DAY + 300 * SECOND, f"continuous-{uuid4().hex}")],
            )
            push(stack, "retention-control", [(current_time, f"fresh-{uuid4().hex}")])
            next_emit = time.monotonic() + 30
        time.sleep(10)
    else:
        raise AssertionError(
            "Retention did not remove observed chunks and markers before individual deadlines"
        )
