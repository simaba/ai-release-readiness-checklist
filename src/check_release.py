from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("Please install pyyaml: pip install pyyaml")

REQUIRED = {
    "low": [
        "intended_operating_conditions",
        "known_limitations",
        "monitoring_defined",
        "monitoring_owner_named",
        "post_release_review_plan",
    ],
    "medium": [
        "intended_operating_conditions",
        "known_limitations",
        "uncertainty_handling",
        "degraded_mode_validated",
        "monitoring_defined",
        "escalation_path_defined",
        "monitoring_owner_named",
        "post_release_review_plan",
    ],
    "high": [
        "intended_operating_conditions",
        "known_limitations",
        "uncertainty_handling",
        "degraded_mode_validated",
        "monitoring_defined",
        "human_override_operational",
        "incident_response_playbook",
        "rollback_tested",
        "accountable_approver_named",
        "post_release_review_plan",
    ],
}

CRITICAL = {
    "low": {"monitoring_defined"},
    "medium": {"degraded_mode_validated", "monitoring_defined"},
    "high": {
        "degraded_mode_validated",
        "incident_response_playbook",
        "rollback_tested",
        "accountable_approver_named",
    },
}

def evaluate(config: dict) -> tuple[str, list[str]]:
    tier = config["risk_tier"]
    checks = config.get("checks", {})
    missing = [c for c in REQUIRED[tier] if not checks.get(c, False)]
    critical_missing = [c for c in missing if c in CRITICAL[tier]]

    if not missing:
        return "GO", missing
    if critical_missing:
        return "NO_GO", missing
    return "CONDITIONAL_GO", missing

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python src/check_release.py <config.yaml>")

    path = Path(sys.argv[1])
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    decision, missing = evaluate(data)

    print(f"Feature: {data.get('feature_name')}")
    print(f"Risk tier: {data.get('risk_tier')}")
    print(f"Decision: {decision}")
    print("Missing checks:")
    if missing:
        for item in missing:
            print(f"- {item}")
    else:
        print("- None")

if __name__ == "__main__":
    main()
