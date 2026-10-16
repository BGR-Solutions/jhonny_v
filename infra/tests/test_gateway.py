"""Gateway autenticado e isolamento do Loki (US1: SC-010, FR-015)."""

from __future__ import annotations

import json
import subprocess

import httpx
import pytest

from .conftest import PROBE_IMAGE, StackEnv, run, service_container


def test_requires_credentials(env: StackEnv) -> None:
    """Sem credencial ou com credencial inválida → 401; válida → 200."""
    url = f"{env.base_url}/loki/api/v1/labels"
    assert httpx.get(url, timeout=10).status_code == 401
    assert httpx.get(url, auth=(env.user, "wrong"), timeout=10).status_code == 401
    assert httpx.get(url, auth=("wrong", "wrong"), timeout=10).status_code == 401
    ok = httpx.get(url, auth=(env.user, env.password), timeout=10)
    assert ok.status_code == 200, ok.text


def test_ready_is_public(env: StackEnv) -> None:
    """`GET /ready` responde 200 sem credencial (healthcheck)."""
    assert httpx.get(f"{env.base_url}/ready", timeout=10).status_code == 200


def test_port_bound_only_to_loopback(env: StackEnv) -> None:
    """A porta publicada está ligada só ao loopback."""
    out = run(["docker", "port", service_container(env, "loki"), "3100/tcp"]).stdout
    bindings = [b for b in out.split() if b]
    assert bindings, "nenhuma porta publicada"
    assert all(b.startswith("127.") for b in bindings), bindings


def _non_loopback_host_ip() -> str:
    addresses = subprocess.run(
        ["hostname", "-I"], capture_output=True, text=True, check=True
    ).stdout.split()
    for address in addresses:
        if ":" not in address and not address.startswith(("127.", "172.17.")):
            return address
    pytest.fail(f"sem IP não-loopback no host: {addresses}", pytrace=False)


def test_not_reachable_from_non_loopback_ip(env: StackEnv) -> None:
    """Um acesso pelo IP não-loopback do host falha."""
    host_ip = _non_loopback_host_ip()
    with pytest.raises(httpx.TransportError):
        httpx.get(f"http://{host_ip}:{env.loki_port}/ready", timeout=5)


def _wget_from_core(env: StackEnv, url: str) -> subprocess.CompletedProcess[str]:
    return run(
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
            url,
        ],
        check=False,
    )


def test_loki_backend_not_reachable_from_core_network(env: StackEnv) -> None:
    """O Loki (3101) só escuta no loopback; o gateway (3100) responde na rede."""
    assert _wget_from_core(env, "http://loki:3100/ready").returncode == 0
    assert _wget_from_core(env, "http://loki:3101/ready").returncode != 0


def test_gateway_shares_loki_namespace(env: StackEnv) -> None:
    """O gateway usa `network_mode: service:loki` (Decision 12)."""
    info = json.loads(
        run(["docker", "inspect", service_container(env, "loki-gateway")]).stdout
    )[0]
    assert info["HostConfig"]["NetworkMode"].startswith("container:")
