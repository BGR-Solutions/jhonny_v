"""Sequência constitucional e gates de aprovação do fluxo SDD."""

from __future__ import annotations

import re

from .conftest import REPO_ROOT


def test_sdd_steps_and_blocking_review_gates() -> None:
    """As sete etapas são ordenadas e cada gate rejeitado aborta o fluxo."""
    workflow = (REPO_ROOT / ".specify/workflows/speckit/workflow.yml").read_text(
        encoding="utf-8"
    )
    assert re.findall(r"command: speckit\.(\w+)", workflow) == [
        "specify",
        "clarify",
        "plan",
        "checklist",
        "tasks",
        "analyze",
        "implement",
    ]
    steps = re.split(r"\n  - id: ", workflow)[1:]
    assert [step.splitlines()[0] for step in steps] == [
        "specify",
        "clarify",
        "review-spec",
        "plan",
        "checklist",
        "review-plan",
        "tasks",
        "analyze",
        "review-analysis",
        "implement",
    ]
    for step in steps:
        if step.splitlines()[0].startswith("review-"):
            assert "type: gate" in step
            assert "options: [approve, reject]" in step
            assert "on_reject: abort" in step
