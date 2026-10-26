"""Structural contracts; runtime qualification is separate."""

from pathlib import Path

import pytest
import yaml
from conftest import (
    NGINX_IMAGE,
    ROOT,
    SOURCE_IMAGE,
    Stack,
    docker_command,
    json_object,
    validate_fixture_context,
)


def load_mapping(path: Path) -> dict[str, object]:
    value: object = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), f"Expected mapping in {path.name}"
    return {str(key): item for key, item in value.items()}


def test_observability_contract() -> None:
    path = ROOT / "infra" / "compose.obs.yaml"
    assert path.is_file(), "Observability overlay has not been implemented"
    document = load_mapping(path)
    services = document.get("services")
    assert isinstance(services, dict)
    assert set(services) == {"loki", "alloy", "logs-gateway", "docker-log-proxy"}
    expected_networks = {
        "docker-log-proxy": {"obs-docker"},
        "loki": {"obs-storage"},
        "logs-gateway": {"obs-ingest", "obs-storage", "obs-edge"},
        "alloy": {"obs-docker", "obs-ingest"},
    }
    expected_dependencies = {
        "docker-log-proxy": set(),
        "loki": set(),
        "logs-gateway": {"loki"},
        "alloy": {"docker-log-proxy", "logs-gateway"},
    }
    networks = document.get("networks")
    assert isinstance(networks, dict)
    assert set(networks) == {"obs-docker", "obs-storage", "obs-ingest", "obs-edge"}
    for network, settings in networks.items():
        assert isinstance(settings, dict)
        assert settings.get("internal") is (network != "obs-edge")
    for name, service in services.items():
        assert isinstance(service, dict), name
        assert service.get("build")
        assert service.get("image")
        assert service.get("healthcheck")
        assert service.get("networks")
        assert service.get("volumes")
        assert service.get("restart") == "unless-stopped"
        attached = service.get("networks")
        assert isinstance(attached, list)
        assert set(attached) == expected_networks[name]
        assert "env_file" in service
        assert "depends_on" in service
        assert service.get("pull_policy") == "never"
        assert service.get("tmpfs")
        assert service.get("mem_limit") in {"128m", "512m", "1g"}
        dependencies = service.get("depends_on")
        assert isinstance(dependencies, dict)
        assert set(dependencies) == expected_dependencies[name]
        for dependency in dependencies.values():
            assert isinstance(dependency, dict)
            assert dependency.get("condition") == "service_healthy"
        mounts = service.get("volumes")
        assert isinstance(mounts, list)
        for mount in mounts:
            if isinstance(mount, dict):
                assert mount.get("read_only") is True
                assert mount.get("type") == "bind"
            else:
                assert isinstance(mount, str)
                assert mount in {"loki-data:/loki", "alloy-data:/var/lib/alloy"}
        build = service.get("build")
        assert isinstance(build, dict)
        assert build["context"] == "./obs-tools"
        assert build["target"] == (name if name in {"loki", "alloy"} else "nginx")
        health = service.get("healthcheck")
        assert isinstance(health, dict)
        assert health["interval"] == "5s"
        assert health["timeout"] == "3s"
        assert health["retries"] == 12
        assert health["start_period"] == "30s"
        command = health.get("test")
        assert isinstance(command, list)
        assert command[:3] == ["CMD", "/usr/local/bin/obs-tools", "probe"]
        if name != "logs-gateway":
            assert not service.get("ports")
        else:
            assert service["ports"] == ["127.0.0.1:${LOKI_PORT:-3100}:8080"]
    volumes = document.get("volumes")
    assert isinstance(volumes, dict)
    assert set(volumes) == {"loki-data", "alloy-data"}


def test_base_is_not_modified_by_observability() -> None:
    document = load_mapping(ROOT / "infra" / "compose.yaml")
    assert not document.get("services")
    networks = document.get("networks")
    assert isinstance(networks, dict)
    assert "jhonny-core" in networks


def test_tool_images() -> None:
    from conftest import docker_command, json_object

    for image in (
        "jhonny-v/loki-health:3.7.9-1",
        "jhonny-v/alloy-health:1.21.2-1",
        "jhonny-v/nginx-obs:1.30.6-1",
    ):
        result = docker_command("image", "inspect", image, "--format", "{{json .}}")
        info = json_object(result.stdout)
        assert info["Architecture"] == "amd64"
        config = info.get("Config")
        assert isinstance(config, dict)
        entrypoint = config.get("Entrypoint")
        assert isinstance(entrypoint, list)
        assert entrypoint[0] == "/usr/local/bin/obs-tools"
        assert config.get("User", "") == ("10001" if "loki-health" in image else "")
        failure = docker_command(
            "run",
            "--rm",
            "--entrypoint",
            "/usr/local/bin/obs-tools",
            image,
            "preflight",
            "--service",
            "unknown",
            expected_code=1,
        )
        assert json_object(failure.stderr)["code"] == "unknown_service"


def assert_json_failure(
    stdout: str, stderr: str, sentinel: str = ""
) -> list[dict[str, object]]:
    events = [
        json_object(line)
        for line in (stdout + "\n" + stderr).splitlines()
        if line.strip()
    ]
    assert events
    assert all(event.get("level") for event in events)
    assert any(event.get("code") for event in events)
    if sentinel:
        assert sentinel not in stdout + stderr
    return events


@pytest.mark.integration
def test_direct_start_rejects_retention(stack: Stack) -> None:
    failure = stack.run_service("loki", options=("-e", "LOKI_RETENTION_PERIOD=25h"))
    assert_json_failure(failure.stdout, failure.stderr)
    assert json_object(failure.stderr)["code"] == "invalid_retention"


@pytest.mark.integration
@pytest.mark.parametrize("scenario", ["missing", "empty", "mismatch", "permissions"])
def test_secret_rotation_revalidates_on_start(stack: Stack, scenario: str) -> None:
    valid = stack.run_service(
        "logs-gateway",
        options=("--entrypoint", "/usr/local/bin/obs-tools"),
        command=("preflight", "--service", "logs-gateway"),
        expected_code=0,
    )
    assert not valid.stdout and not valid.stderr
    scripts = {
        "missing": "import os; os.remove('/secrets/write-password')",
        "empty": "from pathlib import Path; Path('/secrets/write-password').write_bytes(b'')",
        "mismatch": "from pathlib import Path; Path('/secrets/write-password').write_bytes(b'private-sentinel-password-never-log-1234')",
        "permissions": "import os; os.chmod('/secrets/read.htpasswd',0o644)",
    }
    docker_command(
        "run",
        "--rm",
        "--mount",
        f"type=volume,source={stack.secret_volume},target=/secrets",
        SOURCE_IMAGE,
        "python",
        "-c",
        scripts[scenario],
    )
    failure = stack.run_service("logs-gateway")
    events = assert_json_failure(failure.stdout, failure.stderr, "private-sentinel")
    assert events[-1]["stage"] == "run"
    assert events[-1]["service"] == "logs-gateway"


@pytest.mark.integration
@pytest.mark.parametrize("service", ["loki", "alloy", "logs-gateway"])
def test_invalid_native_config_is_json(
    stack: Stack, tmp_path: Path, service: str
) -> None:
    if service == "alloy":
        stack.compose("up", "-d", "--wait", "docker-log-proxy")
    file = tmp_path / "invalid-config"
    sentinel = "private-sentinel-must-not-leak"
    file.write_text(f"invalid-directive-{sentinel};\n", encoding="utf-8")
    target = {
        "loki": "/etc/loki/config.yaml",
        "alloy": "/etc/alloy/config.alloy",
        "logs-gateway": "/etc/nginx/templates/nginx.conf.template",
    }[service]
    failure = stack.run_service(service, options=("-v", f"{file}:{target}:ro"))
    events = assert_json_failure(failure.stdout, failure.stderr, sentinel)
    assert any(event.get("stage") == "native" for event in events)
    assert any(event.get("code") == "engine_exit_failed" for event in events)


@pytest.mark.integration
def test_proxy_missing_socket_fails_before_engine() -> None:
    failure = docker_command(
        "run",
        "--rm",
        NGINX_IMAGE,
        "run",
        "--service",
        "docker-log-proxy",
        expected_code=1,
    )
    assert_json_failure(failure.stdout, failure.stderr)
    assert json_object(failure.stderr)["code"] == "docker_socket_unavailable"


@pytest.mark.integration
def test_read_only_storage_is_rejected(stack: Stack) -> None:
    volume = stack.project + "-read-only"
    docker_command("volume", "create", volume)
    try:
        failure = docker_command(
            "run",
            "--rm",
            "-e",
            "LOKI_RETENTION_PERIOD=336h",
            "--mount",
            f"type=volume,source={volume},target=/loki,readonly",
            "--mount",
            f"type=bind,source={ROOT / 'infra' / 'loki' / 'config.yaml'},target=/etc/loki/config.yaml,readonly",
            "jhonny-v/loki-health:3.7.9-1",
            expected_code=1,
        )
        assert json_object(failure.stderr)["code"] == "volume_not_writable"
    finally:
        docker_command("volume", "rm", volume)


@pytest.mark.integration
def test_component_logs_are_json_not_files(stack: Stack) -> None:
    stack.compose("up", "-d", "--wait", "--wait-timeout", "120", timeout=180)
    for service in ("docker-log-proxy", "loki", "logs-gateway", "alloy"):
        cid = stack.compose("ps", "-q", service).stdout.strip()
        logs = docker_command("logs", cid)
        for line in (logs.stdout + "\n" + logs.stderr).splitlines():
            if line.strip():
                assert json_object(line)
        changed = docker_command("diff", cid).stdout.splitlines()
        assert not any(
            entry.endswith(".log") or "/var/log/" in entry for entry in changed
        ), f"{service} changed a local log path"


def test_missing_distributed_context_is_instrumentation_failure() -> None:
    event: dict[str, object] = {"distributed_context": True}
    with pytest.raises(ValueError, match="fixture_invalid_trace_id"):
        validate_fixture_context(event)
    assert event == {"distributed_context": True}
    validate_fixture_context({"message": "No distributed context declared"})
