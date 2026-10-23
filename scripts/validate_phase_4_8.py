from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALIDATION_SCRIPTS = [
    "scripts/validate_phase_4_2.py",
    "scripts/validate_phase_4_3.py",
    "scripts/validate_phase_4_4.py",
    "scripts/validate_phase_4_5.py",
    "scripts/validate_phase_4_6.py",
    "scripts/validate_phase_4_7.py",
]


def run_validation_script(script: str) -> bool:
    script_path = ROOT / script

    print("=" * 72)
    print(f"RUNNING {script}")
    print("=" * 72)

    if not script_path.exists():
        print(f"Validation script missing: {script_path}")
        return False

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=ROOT,
        check=False,
    )

    if result.returncode != 0:
        print()
        print(f"{script} : FAIL")
        return False

    print()
    print(f"{script} : PASS")
    return True


def main() -> int:
    print("=" * 72)
    print("PHASE 4.8 — PHASE 4 INTEGRATION VALIDATION")
    print("=" * 72)
    print()
    print("Integration scope:")
    print("  Real Docker telemetry")
    print("  PostgreSQL telemetry storage")
    print("  Telemetry aggregation")
    print("  Telemetry query and retrieval")
    print("  Metrics and health signals")
    print("  Kafka observability event pipeline")
    print("  Evidence integrity")
    print("  Autonomous-action boundary")
    print()

    results: dict[str, bool] = {}

    for script in VALIDATION_SCRIPTS:
        passed = run_validation_script(script)
        results[script] = passed

        if not passed:
            print()
            print("=" * 72)
            print("PHASE 4.8 — INTEGRATION VALIDATION FAILED")
            print("=" * 72)
            print()
            print(f"Failed validation: {script}")
            print()
            print("Do NOT proceed to Phase 5.")
            return 1

    print()
    print("=" * 72)
    print("PHASE 4.8 — INTEGRATION RESULTS")
    print("=" * 72)

    for script, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{script:<45} : {status}")

    print()
    print("=" * 72)
    print("PHASE 4 INTEGRATION BOUNDARY")
    print("=" * 72)
    print("Real telemetry collection       : PASS")
    print("Telemetry persistence           : PASS")
    print("Telemetry aggregation           : PASS")
    print("Telemetry retrieval             : PASS")
    print("Health signal generation        : PASS")
    print("Observability event generation  : PASS")
    print("Kafka publication               : PASS")
    print("Kafka consumption               : PASS")
    print("Evidence integrity              : PASS")
    print("Prediction generated            : NONE")
    print("Decision generated              : NONE")
    print("Remediation executed            : NONE")
    print("Autonomous action executed      : NONE")
    print("Phase boundary                  : PASS")

    print()
    print("=" * 72)
    print("PHASE 4.8 — COMPLETE: PASS")
    print("=" * 72)
    print()
    print("PHASE 4 — OBSERVABILITY & TELEMETRY: COMPLETE")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())