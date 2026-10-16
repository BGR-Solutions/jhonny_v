"""Contratos de credenciais obrigatórias e isolamento por serviço."""

from __future__ import annotations

import json
import uuid

import pytest

from .conftest import ComposeFn, StackEnv, run, service_container

CORE_SECRETS = ("POSTGRES_PASSWORD", "REDIS_PASSWORD", "RABBITMQ_DEFAULT_PASS")


@pytest.mark.parametrize("variable", CORE_SECRETS)
@pytest.mark.parametrize("value", [None, ""])
def test_core_rejects_missing_or_empty_secret(
    variable: str, value: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Compose recusa iniciar core sem cada credencial externa."""
    credentials = {key: uuid.uuid4().hex for key in CORE_SECRETS}
    monkeypatch.delenv(variable, raising=False)
    if value is None:
        credentials.pop(variable)
    else:
        credentials[variable] = value
    result = run(
        [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-f",
            "compose.yaml",
            "-f",
            "compose.core.yaml",
            "config",
            "--quiet",
        ],
        env=credentials,
        check=False,
    )
    assert result.returncode != 0
    assert variable in result.stderr


def test_litellm_does_not_load_shared_env(compose: ComposeFn, env: StackEnv) -> None:
    """O proxy recebe apenas as variáveis explicitamente declaradas."""
    result = compose(
        "config",
        "--format",
        "json",
        files=("compose.yaml", "compose.llm.yaml"),
        env={"LITELLM_MASTER_KEY": uuid.uuid4().hex},
    )
    variables = json.loads(result.stdout)["services"]["litellm"]["environment"]
    assert not set((*CORE_SECRETS, "LOKI_GATEWAY_PASSWORD")) & variables.keys()
    assert env.password not in variables.values()


def test_redis_requires_authentication(env: StackEnv) -> None:
    """Redis nega PING anônimo e aceita a credencial fornecida no ambiente."""
    container = service_container(env, "redis")
    anonymous = run(["docker", "exec", container, "redis-cli", "ping"])
    assert "NOAUTH" in anonymous.stdout
    authenticated = run(
        [
            "docker",
            "exec",
            container,
            "sh",
            "-c",
            'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping',
        ]
    )
    assert authenticated.stdout.strip() == "PONG"
