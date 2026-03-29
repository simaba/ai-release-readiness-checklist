# AI Release Readiness Checklist

A practical, risk-tiered checklist for AI-enabled feature launches.

## Why this repository exists

AI systems need release readiness checks that go beyond ordinary software quality gates.
This repository provides:
- checklists by risk tier,
- machine-readable config examples,
- a simple CLI to evaluate readiness.

## Contents

- `checklists/low-risk.md`
- `checklists/medium-risk.md`
- `checklists/high-risk.md`
- `configs/medium-risk-example.yaml`
- `configs/high-risk-example.yaml`
- `src/check_release.py`

## Example usage

```bash
python src/check_release.py configs/medium-risk-example.yaml
```
