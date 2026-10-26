"""Authenticated gateway contracts exercised against real containers."""

import base64
import time
import urllib.error
import urllib.request

import pytest
from conftest import (
    NGINX_IMAGE,
    ROOT,
    SOURCE_IMAGE,
    Stack,
    docker_command,
    network_request,
)


def request(url: str, user: str = "", password: str = "", method: str = "GET") -> int:
    headers = {}
    if user:
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status: object = response.status
            assert isinstance(status, int)
            return status
    except urllib.error.HTTPError as exc:
        return exc.code


def gateway(stack: Stack) -> str:
    stack.compose("up", "-d", "--wait", "--wait-timeout", "120", timeout=180)
    address = stack.compose("port", "logs-gateway", "8080").stdout.strip()
    assert address.startswith("127.0.0.1:")
    return f"http://{address}"


@pytest.mark.integration
def test_gateway_precedence(stack: Stack) -> None:
    url = gateway(stack)
    assert request(url + "/unknown", method="POST") == 404
    assert request(url + "/loki/api/v1/labels") == 401
    assert request(url + "/loki/api/v1/labels", method="POST") == 401
    assert request(url + "/loki/api/v1/labels", "writer", stack.password) == 401
    assert request(url + "/loki/api/v1/labels", "reader", "invalid") == 401
    assert request(url + "/loki/api/v1/labels", "reader", stack.password, "POST") == 405
    assert request(url + "/loki/api/v1/labels", "reader", stack.password) == 200
    assert request(url + "/loki/api/v1/push", "reader", stack.password) == 404
    for path in (
        "/loki/api/v1/labels/",
        "/loki/api/v1/query_range/../push",
        "/loki/api/v1/%63onfig",
        "//config",
    ):
        assert request(url + path, "reader", stack.password) == 404


@pytest.mark.integration
def test_private_gateway_matrix(stack: Stack) -> None:
    gateway(stack)
    network = f"{stack.project}_obs-ingest"
    for port, path, user, password, other, other_password, allowed in (
        (
            8080,
            "/loki/api/v1/labels",
            "reader",
            stack.password,
            "writer",
            stack.write_password,
            "GET",
        ),
        (
            8081,
            "/loki/api/v1/push",
            "writer",
            stack.write_password,
            "reader",
            stack.password,
            "POST",
        ),
    ):
        url = f"http://logs-gateway:{port}"
        for method in ("GET", "POST", "HEAD", "DELETE"):
            assert (
                network_request(network, url + "/unknown", method=method)["status"]
                == 404
            )
            unauth = network_request(network, url + path, method=method)
            assert unauth["status"] == 401
            assert str(unauth["challenge"]).startswith("Basic ")
            assert (
                network_request(network, url + path, other, other_password, method)[
                    "status"
                ]
                == 401
            )
        forbidden = "POST" if allowed == "GET" else "GET"
        denied = network_request(network, url + path, user, password, forbidden)
        assert denied["status"] == 405
        assert denied["allow"] == allowed
        accepted = network_request(
            network,
            url + path,
            user,
            password,
            allowed,
            "{" if allowed == "POST" else None,
        )
        assert accepted["status"] == (200 if allowed == "GET" else 400)
        assert (
            network_request(network, url + "/config", user, password)["status"] == 404
        )
    with pytest.raises(RuntimeError, match="Private HTTP probe failed"):
        network_request(network, "http://logs-gateway:8082/ready")
    with pytest.raises(RuntimeError, match="Private HTTP probe failed"):
        network_request(f"{stack.project}_obs-test", "http://loki:3100/ready")


@pytest.mark.integration
def test_proxy_allowlist_uses_fake_daemon(project_name: str) -> None:
    network = project_name + "-api"
    volume = project_name + "-socket"
    server_name = project_name + "-daemon"
    proxy_name = project_name + "-proxy"
    ids: list[str] = []
    script = r"""
import http.server,socketserver
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header("X-Fixture","mock-daemon")
        self.end_headers()
        self.wfile.write(b"{}")
    do_POST=do_GET
    do_DELETE=do_GET
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("X-Fixture","mock-daemon")
        self.end_headers()
with socketserver.UnixStreamServer("/socket/docker.sock",Handler) as server:
    server.serve_forever()
"""
    docker_command("network", "create", "--internal", network)
    docker_command("volume", "create", volume)
    try:
        ids.append(
            docker_command(
                "run",
                "-d",
                "--name",
                server_name,
                "--network",
                network,
                "--mount",
                f"type=volume,source={volume},target=/socket",
                SOURCE_IMAGE,
                "python",
                "-c",
                script,
            ).stdout.strip()
        )
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            ready = docker_command(
                "exec",
                server_name,
                "python",
                "-c",
                "import os; raise SystemExit(0 if os.path.exists('/socket/docker.sock') else 1)",
                expected_code=None,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("Fake daemon socket did not become ready")
        ids.append(
            docker_command(
                "run",
                "-d",
                "--name",
                proxy_name,
                "--network",
                network,
                "--tmpfs",
                "/run/obs:mode=0700",
                "--mount",
                f"type=volume,source={volume},target=/mock,readonly",
                "--mount",
                f"type=bind,source={ROOT / 'infra' / 'docker-log-proxy' / 'nginx.conf'},target=/etc/nginx/nginx.conf,readonly",
                "--entrypoint",
                "/bin/sh",
                NGINX_IMAGE,
                "-c",
                "set -eu; ln -s /mock/docker.sock /var/run/docker.sock; "
                "exec /usr/local/bin/obs-tools run --service docker-log-proxy",
            ).stdout.strip()
        )
        for _ in range(30):
            result = docker_command(
                "exec",
                proxy_name,
                "/usr/local/bin/obs-tools",
                "probe",
                "http://127.0.0.1:2375/_ping",
                expected_code=None,
            )
            if result.returncode == 0:
                break
            time.sleep(0.1)
        else:
            diagnostics = docker_command("logs", proxy_name)
            raise AssertionError(
                "Proxy did not connect to the fake daemon: "
                + diagnostics.stdout
                + diagnostics.stderr
            )
        base = f"http://{proxy_name}:2375"
        for path in (
            "/_ping",
            "/version",
            "/networks",
            "/containers/json",
            "/containers/abcdef/json",
            "/v1.52/containers/abcdef/logs",
        ):
            for method in ("GET", "HEAD"):
                response = network_request(network, base + path, method=method)
                assert response["status"] == 200
                assert response["fixture"] == "mock-daemon"
            response = network_request(network, base + path, method="POST")
            assert response["status"] == 405
            assert response["fixture"] is None
        for path in (
            "/networks/abcdef",
            "/containers/abcdef/archive",
            "/images/json",
            "/secrets",
            "/containers/create",
            "/containers/abcdef/exec",
            "/containers/abcdef/start",
            "/containers/abcdef/stop",
            "/v1.52/images/json",
            "/containers/abcdef/%61rchive",
        ):
            for method in ("GET", "POST"):
                response = network_request(network, base + path, method=method)
                assert response["status"] == 404
                assert response["fixture"] is None
    finally:
        for container_id in reversed(ids):
            docker_command("rm", "-f", container_id)
        docker_command("volume", "rm", volume)
        docker_command("network", "rm", network)
