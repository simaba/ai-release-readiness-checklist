"""Core validation logic for airc release readiness checker."""
from __future__ import annotations
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ChecklistValidationError(Exception):
    """Raised when the configuration file itself is invalid."""
    pass


REQUIRED_SECTIONS = ["metadata", "model_validation", "governance", "infrastructure"]

REQUIRED_METADATA = ["project", "version", "environment", "regulated_industry", "risk_classification"]

# Gates that must be True for a PASS (not None or False)
REQUIRED_GATES_BY_RISK = {
    "high": [
        "model_validation.performance.bias_evaluation_complete",
        "governance.approvals.technical_review",
        "governance.approvals.ai_governance_review",
        "governance.approvals.legal_review",
        "governance.documentation.model_card_complete",
        "governance.documentation.risk_assessment_complete",
        "infrastructure.testing.unit_tests_passing",
        "infrastructure.testing.security_scan_passed",
        "infrastructure.rollback.rollback_plan_documented",
        "incident_readiness.runbook_complete",
    ],
    "medium": [
        "model_validation.performance.bias_evaluation_complete",
        "governance.approvals.technical_review",
        "governance.documentation.risk_assessment_complete",
        "infrastructure.testing.unit_tests_passing",
        "infrastructure.rollback.rollback_plan_documented",
    ],
    "low": [
        "governance.approvals.technical_review",
        "infrastructure.testing.unit_tests_passing",
    ],
}

INDUSTRY_EXTRA_GATES = {
    "healthcare": ["governance.regulatory.hipaa_assessment_complete"],
    "finance": ["governance.regulatory.sr_11_7_compliance"],
    "insurance": ["governance.regulatory.sr_11_7_compliance"],
    "government": ["governance.approvals.legal_review"],
}


def _get_nested(d: dict, key_path: str, default=None):
    """Traverse a nested dict with dot-separated key path."""
    keys = key_path.split(".")
    val = d
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k, default)
    return val


@dataclass
class GateResult:
    gate: str
    value: Any
    passed: bool
    required: bool


@dataclass
class ValidationResult:
    project: str
    version: str
    environment: str
    risk_classification: str
    regulated_industry: str
    gates: list[GateResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates if g.required)

    @property
    def failed_count(self) -> int:
        return sum(1 for g in self.gates if g.required and not g.passed)

    @property
    def passed_count(self) -> int:
        return sum(1 for g in self.gates if g.passed)

    @property
    def total_gates(self) -> int:
        return len(self.gates)


def validate_checklist(
    config_path: Path,
    strict: bool = False,
    industry_override: str | None = None,
) -> ValidationResult:
    """Validate a release checklist YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file.
        strict: If True, treat all unconfigured gates as failures.
        industry_override: Override the industry from the config file.

    Returns:
        ValidationResult with gate-by-gate results.

    Raises:
        ChecklistValidationError: If the configuration file is structurally invalid.
    """
    try:
        config = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        raise ChecklistValidationError(f"Invalid YAML in {config_path}: {e}") from e

    if not isinstance(config, dict):
        raise ChecklistValidationError(f"{config_path} does not contain a YAML mapping at the top level.")

    # Check required sections
    missing = [s for s in REQUIRED_SECTIONS if s not in config]
    if missing:
        raise ChecklistValidationError(f"Missing required sections: {', '.join(missing)}")

    meta = config.get("metadata", {})
    project = meta.get("project", "Unknown Project")
    version = meta.get("version", "Unknown")
    environment = meta.get("environment", "Unknown")
    risk = meta.get("risk_classification", "high").lower()
    industry = industry_override or meta.get("regulated_industry", "general").lower()

    result = ValidationResult(
        project=project,
        version=version,
        environment=environment,
        risk_classification=risk,
        regulated_industry=industry,
    )

    required_gates = set(REQUIRED_GATES_BY_RISK.get(risk, REQUIRED_GATES_BY_RISK["high"]))
    required_gates.update(INDUSTRY_EXTRA_GATES.get(industry, []))

    # Collect all gates from config
    all_gate_paths: list[str] = []
    def _collect_paths(d, prefix=""):
        for k, v in d.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                _collect_paths(v, path)
            else:
                all_gate_paths.append(path)

    for section in REQUIRED_SECTIONS:
        if isinstance(config.get(section), dict):
            _collect_paths(config[section], section)
    if isinstance(config.get("incident_readiness"), dict):
        _collect_paths(config["incident_readiness"], "incident_readiness")

    for gate_path in sorted(set(all_gate_paths)):
        value = _get_nested(config, gate_path)
        is_required = gate_path in required_gates
        passed = value is True if not strict else value is True
        result.gates.append(GateResult(
            gate=gate_path,
            value=value,
            passed=bool(value) if not is_required else (value is True),
            required=is_required,
        ))

    return result
