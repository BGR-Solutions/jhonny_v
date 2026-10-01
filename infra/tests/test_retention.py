"""Retenção configurável e validação fail-fast (US1: FR-012)."""

from __future__ import annotations

import subprocess

import pytest

from .conftest import INFRA_DIR, LOKI_IMAGE, run

CONFIG = INFRA_DIR / "loki" / "config.yaml"


def _verify(retention: str | None) -> subprocess.CompletedProcess[str]:
    # Sem o arquivo, o Docker criaria um diretório vazio no lugar do bind mount.
    assert CONFIG.is_file(), f"{CONFIG} não existe"
    cmd = ["docker", "run", "--rm"]
    if retention is not None:
        cmd += ["-e", f"LOKI_RETENTION_PERIOD={retention}"]
    cmd += [
        "-v",
        f"{CONFIG}:/etc/loki/config.yaml:ro",
        LOKI_IMAGE,
        "-config.file=/etc/loki/config.yaml",
        "-config.expand-env=true",
        "-verify-config",
        "-print-config-stderr",
    ]
    return run(cmd, check=False, timeout=120)


@pytest.mark.parametrize(
    ("retention", "expected"), [("72h", "retention_period: 3d"), (None, "1w")]
)
def test_retention_is_applied(retention: str | None, expected: str) -> None:
    """A variável define a retenção; sem ela, o default é 7d (`1w`)."""
    proc = _verify(retention)
    assert proc.returncode == 0, proc.stderr[-2000:]
    retention_lines = [
        line.strip()
        for line in proc.stderr.splitlines()
        if line.strip().startswith("retention_period:")
    ]
    assert retention_lines, "retention_period ausente da configuração impressa"
    assert retention_lines[0].endswith(expected), retention_lines


def test_invalid_retention_fails_fast() -> None:
    """Um valor inválido aborta a inicialização com mensagem clara."""
    proc = _verify("abc")
    assert proc.returncode != 0
    assert "not a valid duration string" in proc.stderr + proc.stdout
