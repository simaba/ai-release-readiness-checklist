"""Report rendering for airc validation results."""
from __future__ import annotations
import json
import sys
from airc.validator import ValidationResult


def render_report(result: ValidationResult, output_format: str = "text", full_report: bool = False):
    """Render a validation result to stdout."""
    if output_format == "json":
        _render_json(result)
    elif output_format == "markdown":
        _render_markdown(result, full_report)
    else:
        _render_text(result, full_report)


def _render_text(result: ValidationResult, full_report: bool):
    print(f"\n{'='*60}")
    print(f"  AI Release Readiness Report")
    print(f"  Project: {result.project} v{result.version}")
    print(f"  Environment: {result.environment}")
    print(f"  Industry: {result.regulated_industry} | Risk: {result.risk_classification}")
    print(f"{'='*60}")

    required_gates = [g for g in result.gates if g.required]
    print(f"\nRequired Gates: {result.passed_count}/{result.total_gates} satisfied")
    print(f"Required: {len(required_gates) - result.failed_count}/{len(required_gates)} passed")

    if result.failed_count > 0:
        print("\n❌ Failed Required Gates:")
        for g in required_gates:
            if not g.passed:
                print(f"   • {g.gate} (current: {g.value})")

    if full_report:
        print("\n✅ Passing Gates:")
        for g in result.gates:
            if g.passed:
                status = "REQUIRED" if g.required else "optional"
                print(f"   ✓ {g.gate} [{status}]")


def _render_markdown(result: ValidationResult, full_report: bool):
    lines = [
        f"# Release Readiness Report",
        f"",
        f"| Field | Value |",
        f"|---|---|",
        f"| Project | {result.project} v{result.version} |",
        f"| Environment | {result.environment} |",
        f"| Industry | {result.regulated_industry} |",
        f"| Risk Classification | {result.risk_classification} |",
        f"| Status | {'✅ PASSED' if result.passed else '❌ FAILED'} |",
        f"",
        f"## Gate Summary",
        f"",
        f"- **Total gates:** {result.total_gates}",
        f"- **Passing:** {result.passed_count}",
        f"- **Failed (required):** {result.failed_count}",
        f"",
    ]

    required_failed = [g for g in result.gates if g.required and not g.passed]
    if required_failed:
        lines += ["## ❌ Failed Required Gates", ""]
        for g in required_failed:
            lines.append(f"- `{g.gate}` — current value: `{g.value}`")
        lines.append("")

    if full_report:
        lines += ["## All Gates", "", "| Gate | Value | Required | Status |", "|---|---|---|---|"]
        for g in result.gates:
            status = "✅" if g.passed else "❌"
            req = "Required" if g.required else "Optional"
            lines.append(f"| `{g.gate}` | `{g.value}` | {req} | {status} |")

    print("\n".join(lines))


def _render_json(result: ValidationResult):
    out = {
        "project": result.project,
        "version": result.version,
        "environment": result.environment,
        "regulated_industry": result.regulated_industry,
        "risk_classification": result.risk_classification,
        "passed": result.passed,
        "passed_count": result.passed_count,
        "failed_count": result.failed_count,
        "total_gates": result.total_gates,
        "gates": [
            {"gate": g.gate, "value": g.value, "passed": g.passed, "required": g.required}
            for g in result.gates
        ],
    }
    print(json.dumps(out, indent=2))
