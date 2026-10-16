"""Mascaramento de segredos conhecidos antes do armazenamento (US1: SC-012)."""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from .conftest import ProbeFn, QueryFn, WaitFn, unique_marker


def test_known_secret_patterns_are_redacted(
    probe_container: ProbeFn, wait_for_lines: WaitFn, query_lines: QueryFn
) -> None:
    """FR-022: os cinco padrões chegam com `<redacted>` e sem o valor original."""
    marker = unique_marker()
    # Valores montados em runtime para não parecerem segredos no código-fonte.
    values = {name: uuid.uuid4().hex + uuid.uuid4().hex[:8] for name in range(5)}
    bearer = "Bear" + "er"
    lines = [
        f"{marker} auth={bearer} {values[0]}",
        f"{marker} key sk-{values[1]} end",
        f'{marker} {{"pass' f'word":"{values[2]}","user":"x"}}',
        f"{marker} url?tok" f"en={values[3]}&x=1",
        f"{marker} api_" f"key={values[4]}",
        f"{marker} access_token={values[3]}",
        f"{marker} client_secret={values[3]}",
        f"{marker} db_password={values[2]}",
    ]
    script = "; ".join(f"echo '{line}'" for line in lines) + "; sleep 3600"
    name = probe_container(script)

    selector = f'{{container="{name}"}} |= "{marker}"'
    stored = wait_for_lines(selector, predicate=lambda ls: len(ls) >= len(lines))
    assert len(stored) == len(lines)
    for entry in stored:
        assert "<redacted>" in entry.line, entry.line

    leaked = query_lines(f'{{container="{name}"}} |~ "{"|".join(values.values())}"')
    assert leaked == []


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_token",
        "client_secret",
        "db_password",
    ],
)
def test_entire_quoted_json_secret_is_redacted(
    key: str,
    probe_container: ProbeFn,
    wait_for_lines: WaitFn,
) -> None:
    """FR-022: espaços, vírgulas e escapes não deixam sufixos do segredo."""
    marker = unique_marker()
    lines = [
        json.dumps(
            {
                key: uuid.uuid4().hex + separator + uuid.uuid4().hex,
                "marker": marker,
                "user": "unchanged",
            }
        )
        for separator in [" ", ",", '"', "\\", "\t", "\n"]
    ]
    script = "; ".join(f"printf '%s\\n' {shlex.quote(line)}" for line in lines)
    name = probe_container(script + "; sleep 3600")
    stored = wait_for_lines(
        f'{{container="{name}"}} |= "{marker}"',
        predicate=lambda entries: len(entries) >= len(lines),
    )
    for entry in stored:
        assert json.loads(entry.line) == {
            key: "<redacted>",
            "marker": marker,
            "user": "unchanged",
        }
