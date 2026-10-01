"""Subida saudável da camada, sozinha e combinada (US1: SC-007, FR-013).

Recria a stack três vezes e, ao final, restaura a combinação padrão
(base + core + obs) usada pelos demais testes.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import pytest

from .conftest import (
    ALL_FILES,
    LLM_FILE,
    OBS_SERVICES,
    ComposeFn,
    StackEnv,
    inspect,
    service_container,
)

pytestmark = [pytest.mark.disruptive, pytest.mark.slow]

BASE_OBS = ("compose.yaml", "compose.obs.yaml")
BASE_CORE_LLM = ("compose.yaml", "compose.core.yaml", LLM_FILE)
UP = ("up", "-d", "--build", "--wait", "--wait-timeout", "600")


@pytest.fixture(scope="module", autouse=True)
def restore_default_stack(
    compose: ComposeFn, llm_env: dict[str, str]
) -> Iterator[None]:
    """Restaura base + core + obs no fim do módulo."""
    yield
    compose("down", "--remove-orphans", files=ALL_FILES, env=llm_env)
    compose(*UP)


def _assert_obs_healthy(env: StackEnv) -> None:
    started: dict[str, str] = {}
    for service in OBS_SERVICES:
        info = inspect(service_container(env, service))
        assert info["State"]["Health"]["Status"] == "healthy", service
        assert info["RestartCount"] == 0, service
        started[service] = info["State"]["StartedAt"]
    assert started["loki"] < started["loki-gateway"] < started["alloy"], started
    assert started["socket-proxy"] < started["alloy"], started


def _recreate(compose: ComposeFn, env: dict[str, str], *steps: Sequence[str]) -> None:
    compose("down", "--remove-orphans", files=ALL_FILES, env=env)
    for files in steps:
        compose(*UP, files=files, env=env)


def test_obs_alone(env: StackEnv, compose: ComposeFn, llm_env: dict[str, str]) -> None:
    """Base + obs sobe saudável."""
    _recreate(compose, llm_env, BASE_OBS)
    _assert_obs_healthy(env)


def test_all_layers_together(
    env: StackEnv, compose: ComposeFn, llm_env: dict[str, str]
) -> None:
    """Base + core + llm + obs sobe saudável."""
    _recreate(compose, llm_env, ALL_FILES)
    _assert_obs_healthy(env)


def test_obs_added_last(
    env: StackEnv, compose: ComposeFn, llm_env: dict[str, str]
) -> None:
    """Base + core + llm no ar, e a obs adicionada por último."""
    _recreate(compose, llm_env, BASE_CORE_LLM, ALL_FILES)
    _assert_obs_healthy(env)
