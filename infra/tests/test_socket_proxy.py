"""Proxy de socket só leitura e isolamento de rede (US1: SC-008, SC-009, FR-009)."""

from __future__ import annotations

import pytest

from .conftest import PROBE_IMAGE, ComposeFn, StackEnv, inspect, run, service_container

PROBE = """
exec 3<>/dev/tcp/socket-proxy/2375
printf '%s %s HTTP/1.0\\r\\nHost: socket-proxy\\r\\n\\r\\n' "$1" "$2" >&3
IFS= read -r status <&3
echo "$status"
"""


@pytest.fixture(scope="module")
def proxy_status(compose: ComposeFn):
    """Devolve o código HTTP do proxy para (método, caminho), a partir do Alloy."""

    def _status(method: str, path: str) -> int:
        out = compose(
            "exec", "-T", "alloy", "bash", "-c", PROBE, "probe", method, path
        ).stdout
        return int(out.split()[1])

    return _status


@pytest.fixture(scope="module")
def api_prefix() -> str:
    """Prefixo versionado da API do Docker (ex.: `/v1.48`)."""
    version = run(["docker", "version", "--format", "{{.Server.APIVersion}}"])
    return f"/v{version.stdout.strip()}"


@pytest.mark.parametrize(
    ("method", "path", "expected"),
    [
        ("POST", "/containers/create", 405),
        ("DELETE", "/containers/x", 405),
        ("GET", "/images/json", 403),
        ("GET", "/info", 403),
        ("GET", "/containers/x/archive", 403),
    ],
)
def test_denied_requests(proxy_status, method: str, path: str, expected: int) -> None:
    """SC-008: escrita → 405; leitura fora da allowlist → 403."""
    assert proxy_status(method, path) == expected


@pytest.mark.parametrize("versioned", [False, True], ids=["plain", "versioned"])
def test_allowlisted_paths(
    proxy_status, api_prefix: str, env: StackEnv, versioned: bool
) -> None:
    """Cada caminho da allowlist responde 200, com e sem `/v1.NN`."""
    container_id = inspect(service_container(env, "loki"))["Id"]
    network_id = run(
        ["docker", "network", "inspect", "-f", "{{.Id}}", f"{env.project}-core"]
    ).stdout.strip()
    prefix = api_prefix if versioned else ""
    checks = [
        ("GET", "/_ping"),
        ("HEAD", "/_ping"),
        ("GET", "/version"),
        ("GET", "/containers/json"),
        ("GET", f"/containers/{container_id}/json"),
        ("GET", f"/containers/{container_id}/logs?stdout=1&tail=1"),
        ("GET", "/networks"),
        ("GET", f"/networks/{network_id}"),
    ]
    results = {f"{m} {prefix}{p}": proxy_status(m, prefix + p) for m, p in checks}
    assert all(code == 200 for code in results.values()), results


def test_collector_does_not_mount_docker_socket(env: StackEnv) -> None:
    """O `alloy` não monta o socket do Docker."""
    mounts = inspect(service_container(env, "alloy"))["Mounts"]
    assert not [m for m in mounts if "docker.sock" in m.get("Source", "")], mounts


def test_proxy_network_membership(env: StackEnv) -> None:
    """O proxy está só na `docker-api`, que contém só `socket-proxy` e `alloy`."""
    proxy = inspect(service_container(env, "socket-proxy"))
    assert set(proxy["NetworkSettings"]["Networks"]) == {f"{env.project}-docker-api"}

    network = run(
        [
            "docker",
            "network",
            "inspect",
            "-f",
            "{{range .Containers}}{{.Name}} {{end}}",
            f"{env.project}-docker-api",
        ]
    ).stdout.split()
    assert sorted(network) == sorted(
        [service_container(env, "socket-proxy"), service_container(env, "alloy")]
    )


def test_proxy_unreachable_from_core_network(env: StackEnv) -> None:
    """SC-009: um contêiner na rede core não alcança o proxy."""
    proc = run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            f"{env.project}-core",
            PROBE_IMAGE,
            "wget",
            "-T",
            "5",
            "-qO-",
            "http://socket-proxy:2375/_ping",
        ],
        check=False,
    )
    assert proc.returncode != 0


def test_proxy_runs_unprivileged(env: StackEnv) -> None:
    """O proxy roda como `65534:<DOCKER_GID>` com rootfs somente leitura."""
    proxy = inspect(service_container(env, "socket-proxy"))
    assert proxy["Config"]["User"] == f"65534:{env.values['DOCKER_GID']}"
    assert proxy["HostConfig"]["ReadonlyRootfs"] is True
    assert proxy["HostConfig"]["CapDrop"] == ["ALL"]
