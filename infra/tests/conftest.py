"""Fixtures compartilhadas dos testes de aceite da camada de observabilidade.

Os testes rodam contra a stack em execução (base + core + obs). As credenciais e
portas vêm do ambiente do processo e, como fallback, do `.env` da raiz do
repositório (o mesmo arquivo passado ao Compose com `--env-file`).

Dependências: Docker Engine com Compose v2 no `PATH` e a stack já no ar.
Limitações: os testes `disruptive` reiniciam serviços e não devem rodar em
paralelo com outros testes.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pytest

INFRA_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = INFRA_DIR.parent
ENV_FILE = Path(os.environ.get("JV_ENV_FILE", REPO_ROOT / ".env"))
PROBE_IMAGE = "busybox:1.37.0-musl"
LOKI_IMAGE = "grafana/loki:3.7.8"

BASE_FILES: tuple[str, ...] = ("compose.yaml", "compose.core.yaml", "compose.obs.yaml")
LLM_FILE = "compose.llm.yaml"
ALL_FILES: tuple[str, ...] = (*BASE_FILES, LLM_FILE)
OBS_SERVICES: tuple[str, ...] = ("socket-proxy", "loki", "loki-gateway", "alloy")
ALLOWED_LABELS: frozenset[str] = frozenset(
    {"compose_project", "compose_service", "container", "stream", "service_name"}
)


def _read_env_file(path: Path) -> dict[str, str]:
    """Lê um arquivo `.env` simples (`CHAVE=valor`).

    Args:
        path: Caminho do arquivo.

    Returns:
        Mapa das variáveis definidas; vazio se o arquivo não existir.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class StackEnv:
    """Configuração do ambiente sob teste.

    Attributes:
        user: Usuário do gateway do Loki.
        password: Senha do gateway do Loki.
        loki_port: Porta publicada do gateway.
        host_ip: IP de bind das portas publicadas.
        project: Nome do projeto Compose.
        values: Todas as variáveis efetivas (`.env` sobreposto pelo ambiente).
    """

    user: str
    password: str
    loki_port: int
    host_ip: str
    project: str
    values: Mapping[str, str] = field(repr=False)

    @property
    def base_url(self) -> str:
        """URL base do gateway autenticado."""
        return f"http://{self.host_ip}:{self.loki_port}"


@dataclass
class LogLine:
    """Uma linha devolvida pelo Loki.

    Attributes:
        ts_ns: Timestamp da entrada, em nanossegundos.
        line: Conteúdo da linha.
        labels: Rótulos do stream e metadados estruturados/derivados.
    """

    ts_ns: int
    line: str
    labels: dict[str, str]


@pytest.fixture(scope="session")
def env() -> StackEnv:
    """Carrega credenciais e portas do ambiente, com fallback no `.env`.

    Returns:
        A configuração do ambiente sob teste.

    Raises:
        pytest.fail: Se as credenciais do gateway não estiverem definidas.
    """
    values = {**_read_env_file(ENV_FILE), **os.environ}
    user = values.get("LOKI_GATEWAY_USER", "")
    gateway_secret = values.get("LOKI_GATEWAY_PASSWORD", "")
    if not user or not gateway_secret:
        pytest.fail(
            "LOKI_GATEWAY_USER e LOKI_GATEWAY_PASSWORD são obrigatórios "
            f"(ambiente ou {ENV_FILE}).",
            pytrace=False,
        )
    return StackEnv(
        user=user,
        password=gateway_secret,
        loki_port=int(values.get("LOKI_PORT") or 3100),
        host_ip=values.get("HOST_IP") or "127.0.0.1",
        project=values.get("COMPOSE_PROJECT_NAME") or "jhonny_v",
        values=values,
    )


@pytest.fixture(scope="session")
def loki(env: StackEnv) -> Iterator[httpx.Client]:
    """Cliente HTTP autenticado no gateway do Loki.

    Args:
        env: Configuração do ambiente.

    Yields:
        Um `httpx.Client` com `base_url` e `auth` configurados.
    """
    with httpx.Client(
        base_url=env.base_url, auth=(env.user, env.password), timeout=30.0
    ) as client:
        yield client


def run(
    args: Sequence[str],
    *,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    timeout: float = 600,
) -> subprocess.CompletedProcess[str]:
    """Executa um comando e captura a saída.

    Args:
        args: Comando e argumentos.
        check: Se `True`, falha o teste quando o código de saída for ≠ 0.
        env: Variáveis extras para o processo.
        timeout: Tempo máximo em segundos.

    Returns:
        O processo concluído.
    """
    proc = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
        cwd=INFRA_DIR,
        env={**os.environ, **(env or {})},
        timeout=timeout,
        check=False,
    )
    if check and proc.returncode != 0:
        pytest.fail(
            f"comando falhou ({proc.returncode}): {' '.join(args)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}",
            pytrace=False,
        )
    return proc


ComposeFn = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture(scope="session")
def compose() -> ComposeFn:
    """Executor de `docker compose` com o `.env` da raiz e os arquivos da stack.

    Returns:
        Função `compose(*args, files=BASE_FILES, env=None, check=True)`.
    """

    def _compose(
        *args: str,
        files: Sequence[str] = BASE_FILES,
        env: Mapping[str, str] | None = None,
        check: bool = True,
        timeout: float = 600,
    ) -> subprocess.CompletedProcess[str]:
        cmd = ["docker", "compose"]
        if ENV_FILE.is_file():
            cmd += ["--env-file", str(ENV_FILE)]
        for name in files:
            cmd += ["-f", name]
        return run([*cmd, *args], check=check, env=env, timeout=timeout)

    return _compose


def _parse_streams(payload: dict[str, Any]) -> list[LogLine]:
    lines: list[LogLine] = []
    for stream in payload["data"]["result"]:
        labels = dict(stream.get("stream", {}))
        for value in stream.get("values", []):
            extra = value[2] if len(value) > 2 else {}
            merged = dict(labels)
            for group in ("structuredMetadata", "parsed"):
                merged.update(extra.get(group, {}) if isinstance(extra, dict) else {})
            lines.append(LogLine(ts_ns=int(value[0]), line=value[1], labels=merged))
    lines.sort(key=lambda item: item.ts_ns)
    return lines


QueryFn = Callable[..., list[LogLine]]


@pytest.fixture(scope="session")
def query_lines(loki: httpx.Client) -> QueryFn:
    """Consulta `query_range` e devolve as linhas com rótulos e metadados.

    Args:
        loki: Cliente autenticado.

    Returns:
        Função `query_lines(logql, since=600.0, limit=5000)`.
    """

    def _query(logql: str, since: float = 600.0, limit: int = 5000) -> list[LogLine]:
        now = time.time_ns()
        resp = loki.get(
            "/loki/api/v1/query_range",
            params={
                "query": logql,
                "start": str(now - int(since * 1e9)),
                "end": str(now + int(5e9)),
                "limit": str(limit),
                "direction": "forward",
            },
            headers={"X-Loki-Response-Encoding-Flags": "categorize-labels"},
        )
        resp.raise_for_status()
        return _parse_streams(resp.json())

    return _query


WaitFn = Callable[..., list[LogLine]]


@pytest.fixture(scope="session")
def wait_for_lines(query_lines: QueryFn) -> WaitFn:
    """Faz polling de 1 s até o predicado valer ou o tempo esgotar.

    Args:
        query_lines: Função de consulta.

    Returns:
        Função `wait_for_lines(logql, predicate=bool, timeout=60.0, since=600.0)`
        que devolve as linhas da última consulta ou falha o teste no timeout.
    """

    def _wait(
        logql: str,
        predicate: Callable[[list[LogLine]], bool] = bool,
        timeout: float = 60.0,
        since: float = 600.0,
    ) -> list[LogLine]:
        deadline = time.monotonic() + timeout
        lines: list[LogLine] = []
        while True:
            lines = query_lines(logql, since=since)
            if predicate(lines):
                return lines
            if time.monotonic() >= deadline:
                pytest.fail(
                    f"timeout de {timeout}s esperando {logql!r}; "
                    f"última consulta devolveu {len(lines)} linha(s)",
                    pytrace=False,
                )
            time.sleep(1)

    return _wait


ProbeFn = Callable[..., str]


@pytest.fixture
def probe_container() -> Iterator[ProbeFn]:
    """Sobe contêineres busybox descartáveis e os remove no teardown.

    Yields:
        Função `probe_container(script, labels=None, network=None, detach=True,
        auto_remove=True)` que devolve o nome único (prefixo `qs-`) do contêiner.
    """
    created: list[str] = []

    def _probe(
        script: str,
        labels: Mapping[str, str] | None = None,
        network: str | None = None,
        detach: bool = True,
        auto_remove: bool = True,
    ) -> str:
        name = f"qs-{uuid.uuid4().hex[:10]}"
        cmd = ["docker", "run", "--name", name]
        if auto_remove:
            cmd.append("--rm")
        if detach:
            cmd.append("-d")
        for key, value in (labels or {}).items():
            cmd += ["--label", f"{key}={value}"]
        if network:
            cmd += ["--network", network]
        cmd += [PROBE_IMAGE, "sh", "-c", script]
        created.append(name)
        run(cmd, check=detach)
        return name

    yield _probe
    for name in created:
        run(["docker", "rm", "-f", name], check=False)


def inspect(name: str) -> dict[str, Any]:
    """Devolve o `docker inspect` de um contêiner.

    Args:
        name: Nome ou ID do contêiner.

    Returns:
        O primeiro objeto do `docker inspect`.
    """
    return json.loads(run(["docker", "inspect", name]).stdout)[0]


def service_container(env: StackEnv, service: str) -> str:
    """Nome do contêiner de um serviço Compose da stack.

    Args:
        env: Configuração do ambiente.
        service: Nome do serviço.

    Returns:
        O nome do contêiner (`<projeto>-<serviço>-1`).
    """
    return f"{env.project}-{service}-1"


def wait_healthy(names: Sequence[str], timeout: float = 180.0) -> None:
    """Espera os contêineres ficarem `healthy`.

    Args:
        names: Nomes dos contêineres.
        timeout: Tempo máximo em segundos.
    """
    deadline = time.monotonic() + timeout
    pending = list(names)
    while pending:
        pending = [
            n
            for n in pending
            if inspect(n)["State"].get("Health", {}).get("Status") != "healthy"
        ]
        if not pending:
            return
        if time.monotonic() >= deadline:
            pytest.fail(f"não ficaram healthy em {timeout}s: {pending}", pytrace=False)
        time.sleep(2)


@pytest.fixture(scope="session")
def llm_env(env: StackEnv) -> dict[str, str]:
    """Variáveis para subir a camada llm no perfil `validation` (SC-007).

    Args:
        env: Configuração do ambiente.

    Returns:
        Variáveis extras a passar ao `compose`.

    Raises:
        pytest.fail: Se `LITELLM_MASTER_KEY` não estiver definido. Nunca pula.
    """
    if not env.values.get("LITELLM_MASTER_KEY"):
        pytest.fail(
            "LITELLM_MASTER_KEY é obrigatório para validar a camada llm (SC-007); "
            f"defina-o no ambiente ou em {ENV_FILE}.",
            pytrace=False,
        )
    return {
        "OLLAMA_API_BASE": "http://ollama-local-mock:11435",
        "COMPOSE_PROFILES": "core,validation",
    }


def unique_marker(prefix: str = "qs") -> str:
    """Gera um marcador único para localizar linhas no Loki.

    Args:
        prefix: Prefixo do marcador.

    Returns:
        Um marcador como `qs-<hex>`.
    """
    return f"{prefix}-{uuid.uuid4().hex}"
