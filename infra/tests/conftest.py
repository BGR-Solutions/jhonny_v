"""Isolated, typed infrastructure validation fixtures."""

from __future__ import annotations

import json
import os
import secrets
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUILDER = "golang:1.27.2@sha256:820153096fda4de6ac1b7194d12e416b7dd8f4e9a33d17e0345b111b945162d8"
NGINX_IMAGE = "jhonny-v/nginx-obs:1.30.6-1"
SOURCE_IMAGE = "python:3.12.12-alpine3.22@sha256:848ba4413eb897e225159b8fc1b02094576cbae4aa73fc13142608ae2c8c0e32"


def network_request(
    network: str,
    url: str,
    user: str = "",
    password: str = "",
    method: str = "GET",
    body: str | None = None,
) -> dict[str, object]:
    """Run an authorized private HTTP probe without credentials in argv/env."""
    script = r"""
import base64,json,sys,urllib.request,urllib.error
p=json.load(sys.stdin)
h={}
if p["user"]:
    h["Authorization"]="Basic "+base64.b64encode((p["user"]+":"+p["password"]).encode()).decode()
if p["body"] is not None:
    h["Content-Type"]="application/json"
r=urllib.request.Request(p["url"],headers=h,method=p["method"],
    data=p["body"].encode() if p["body"] is not None else None)
try:
    response=urllib.request.urlopen(r,timeout=5)
except urllib.error.HTTPError as e:
    response=e
with response:
    json.dump({"status":response.code,"allow":response.headers.get("Allow"),
        "challenge":response.headers.get("WWW-Authenticate"),
        "fixture":response.headers.get("X-Fixture"),
        "body":response.read().decode(errors="replace")},sys.stdout)
"""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            network,
            SOURCE_IMAGE,
            "python",
            "-c",
            script,
        ],
        input=json.dumps(
            {
                "url": url,
                "user": user,
                "password": password,
                "method": method,
                "body": body,
            }
        ).encode(),
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Private HTTP probe failed (exit={result.returncode})")
    return json_object(result.stdout.decode())


def docker_command(
    *args: str, timeout: float = 30, expected_code: int | None = 0
) -> subprocess.CompletedProcess[str]:
    """Run a bounded Docker command without exposing captured output on failure."""
    result = subprocess.run(
        ["docker", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    if expected_code is not None and result.returncode != expected_code:
        raise RuntimeError(f"Docker command failed (exit={result.returncode})")
    return result


def json_object(text: str) -> dict[str, object]:
    """Decode an object while rejecting untyped or unexpected payloads."""
    value: object = json.loads(text)
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise ValueError("Expected a JSON object")
    return {str(key): item for key, item in value.items()}


def validate_fixture_context(event: dict[str, object]) -> None:
    """Reject declared distributed contexts without original trace/span IDs."""
    if event.get("distributed_context"):
        for name, size in (("trace_id", 32), ("span_id", 16)):
            value = event.get(name)
            if (
                not isinstance(value, str)
                or len(value) != size
                or any(char not in "0123456789abcdef" for char in value)
                or set(value) == {"0"}
            ):
                raise ValueError(f"fixture_invalid_{name}")


@pytest.fixture
def project_name() -> str:
    """Return a test-owned Compose identity, never the operator identity."""
    return f"jhonny-v-obs-test-{uuid4().hex[:12]}"


@pytest.fixture
def private_dir(tmp_path: Path) -> Path:
    """Provide a fixture-owned directory; Linux permission checks occur in runtime."""
    directory = tmp_path / "observability"
    directory.mkdir(mode=0o700)
    return directory


@dataclass(frozen=True)
class Stack:
    """Fixture-owned resources and ephemeral credentials."""

    project: str
    password: str = field(repr=False)
    write_password: str = field(repr=False)
    secret_volume: str
    retention: str = "336h"
    overlays: tuple[Path, ...] = ()

    def logs(self, *services: str, tail: int | None = None) -> str:
        """Read both Docker application streams and redact fixture credentials."""
        options = ("--tail", str(tail)) if tail is not None else ()
        result = self.compose(
            "logs", "--no-log-prefix", "--no-color", *options, *services
        )
        return (
            (result.stdout + "\n" + result.stderr)
            .replace(self.password, "[redacted]")
            .replace(self.write_password, "[redacted]")
        )

    def run_service(
        self,
        service: str,
        *,
        options: tuple[str, ...] = (),
        command: tuple[str, ...] = (),
        expected_code: int = 1,
    ) -> subprocess.CompletedProcess[str]:
        """Capture application streams independently of Compose progress output."""
        cid = self.compose(
            "run",
            "-d",
            "--no-deps",
            *options,
            service,
            *command,
        ).stdout.strip()
        if len(cid) != 64 or any(char not in "0123456789abcdef" for char in cid):
            raise RuntimeError("Compose did not return a container ID")
        try:
            docker_command("update", "--restart=no", cid)
            status = docker_command("wait", cid).stdout.strip()
            if not status.isdecimal():
                raise RuntimeError("Container wait returned an invalid status")
            logs = docker_command("logs", cid)
            if int(status) != expected_code:
                raise AssertionError(
                    f"{service} exited {status}, expected {expected_code}"
                )
            return subprocess.CompletedProcess(
                args=[service],
                returncode=int(status),
                stdout=logs.stdout,
                stderr=logs.stderr,
            )
        finally:
            docker_command("rm", "-f", cid)

    def compose(
        self, *args: str, expected_code: int = 0, timeout: float = 150
    ) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env.update(
            COMPOSE_PROJECT_NAME=self.project,
            OBS_TEST_SECRETS_VOLUME=self.secret_volume,
            OBS_READ_USER="reader",
            OBS_WRITE_USER="writer",
            LOKI_RETENTION_PERIOD=self.retention,
        )
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-p",
                self.project,
                "-f",
                str(ROOT / "infra" / "compose.yaml"),
                "-f",
                str(ROOT / "infra" / "compose.obs.yaml"),
                "-f",
                str(ROOT / "infra" / "compose.obs.test.yaml"),
                *[arg for overlay in self.overlays for arg in ("-f", str(overlay))],
                *args,
            ],
            env=env,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        if result.returncode != expected_code:
            detail = result.stderr.replace(self.password, "[redacted]").replace(
                self.write_password, "[redacted]"
            )
            if args and args[0] == "up":
                diagnostics = self.logs(
                    "docker-log-proxy", "logs-gateway", "loki", "alloy", tail=8
                )
                detail += "\n" + diagnostics
            raise RuntimeError(
                f"Fixture Compose failed (exit={result.returncode}): {detail}"
            )
        return result


@pytest.fixture
def stack(project_name: str) -> Iterator[Stack]:
    """Prepare test-owned secrets on Linux storage; never relax host ACLs."""
    docker_command("version", "--format", "{{.Server.Os}}")
    volume = f"{project_name}-secrets"
    password = secrets.token_urlsafe(36)
    write_password = secrets.token_urlsafe(36)
    fixture = Stack(project_name, password, write_password, volume)
    docker_command("volume", "create", "--label", f"obs.test={project_name}", volume)
    try:
        # The helper reads passwords over stdin, never via argv, env or logs.
        source = r"""package main
import("bufio";"os";"path/filepath";"golang.org/x/crypto/bcrypt")
func main(){
 input:=bufio.NewReader(os.Stdin)
 r,err:=input.ReadString('\n');if err!=nil{panic("stdin")}
 p,err:=input.ReadString('\n');if err!=nil{panic("stdin")}
 r=r[:len(r)-1]
 p=p[:len(p)-1]
 h,err:=bcrypt.GenerateFromPassword([]byte(p),12);if err!=nil{panic("hash")}
 rh,err:=bcrypt.GenerateFromPassword([]byte(r),12);if err!=nil{panic("hash")}
 if os.Chmod("/secrets",0700)!=nil{panic("mode")}
 for n,v:=range map[string]string{"read.htpasswd":"reader:"+string(rh)+"\n","write.htpasswd":"writer:"+string(h)+"\n","write-password":p}{
 if os.WriteFile(filepath.Join("/secrets",n),[]byte(v),0600)!=nil{panic("write")}
 }
}"""
        # One stdin carries helper source then password using an explicit delimiter.
        script = "umask 077\ncat > /tmp/provision.go <<'GO'\n" + source + "\nGO\n"
        script += (
            "cat > /tmp/password <<'PASSWORD'\n"
            + password
            + "\n"
            + write_password
            + "\nPASSWORD\n"
        )
        script += "go run /tmp/provision.go < /tmp/password\n"
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-i",
                "--mount",
                f"type=volume,source={volume},target=/secrets",
                "--mount",
                f"type=bind,source={ROOT / 'infra' / 'obs-tools'},target=/src,readonly",
                "--workdir",
                "/src",
                BUILDER,
                "sh",
            ],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode:
            detail = (
                result.stderr.decode("utf-8", errors="replace")
                .replace(password, "[redacted]")
                .replace(write_password, "[redacted]")
            )
            raise RuntimeError(f"Ephemeral credential provisioning failed: {detail}")
        yield fixture
    finally:
        if (ROOT / "infra" / "compose.obs.yaml").exists():
            fixture.compose("down", "--volumes", "--remove-orphans")
        docker_command("volume", "rm", volume)


def storage_snapshot(stack: Stack) -> dict[str, object]:
    """Inspect only the fixture's Loki volume, read-only and without payloads."""
    volume = f"{stack.project}_loki-data"
    docker_command("volume", "inspect", "--format", "{{.Name}}", volume)
    script = r"""
import base64,json,pathlib,re
root=pathlib.Path("/data")
chunks=[]
for path in (root/"chunks"/"fake").glob("*/*"):
    if not path.is_file():
        continue
    tail=base64.b64decode(path.name,validate=True).decode("ascii")
    if not re.fullmatch(r"[0-9a-f]+:[0-9a-f]+:[0-9a-f]+",tail):
        raise ValueError("unexpected chunk key")
    start,end,_=tail.split(":")
    stat=path.stat()
    chunks.append({"path":str(path.relative_to(root)),"from_ms":int(start,16),
        "through_ms":int(end,16),"mtime":stat.st_mtime,"size":stat.st_size})
def files(folder):
    return [{"path":str(p.relative_to(root)),"mtime":p.stat().st_mtime}
        for p in folder.rglob("*") if p.is_file()]
json.dump({"chunks":chunks,"markers":files(root/"compactor"),
    "indexes":files(root/"chunks"/"index")},__import__("sys").stdout)
"""
    result = docker_command(
        "run",
        "--rm",
        "--network",
        "none",
        "--mount",
        f"type=volume,source={volume},target=/data,readonly",
        SOURCE_IMAGE,
        "python",
        "-c",
        script,
    )
    return json_object(result.stdout)


@pytest.fixture
def storage_observer(stack: Stack) -> Iterator[Callable[[], str]]:
    """Observe removals at 50ms resolution without writing to the Loki volume."""
    containers: list[str] = []

    def start() -> str:
        volume = f"{stack.project}_loki-data"
        docker_command("volume", "inspect", "--format", "{{.Name}}", volume)
        script = r"""
import json,pathlib,time
root=pathlib.Path("/data")
previous=set()
deadline=time.monotonic()+3000
while time.monotonic()<deadline:
    current={str(p.relative_to(root)) for p in (root/"chunks"/"fake").glob("*/*")
        if p.is_file()}
    current.update(str(p.relative_to(root))
        for p in (root/"compactor"/"retention").glob("*/markers/*") if p.is_file())
    observed=time.time()
    for path in previous-current:
        print(json.dumps({"path":path,"removed_at":observed}),flush=True)
    previous=current
    time.sleep(.05)
"""
        cid = docker_command(
            "run",
            "-d",
            "--network",
            "none",
            "--label",
            f"obs.test={stack.project}",
            "--mount",
            f"type=volume,source={volume},target=/data,readonly",
            SOURCE_IMAGE,
            "python",
            "-u",
            "-c",
            script,
        ).stdout.strip()
        containers.append(cid)
        assert (
            docker_command(
                "inspect", "--format", "{{.State.Running}}", cid
            ).stdout.strip()
            == "true"
        ), "Read-only storage observer failed to start"
        return cid

    try:
        yield start
    finally:
        for cid in containers:
            docker_command("rm", "-f", cid)
