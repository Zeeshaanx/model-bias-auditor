"""Run the built-in probe suite against every mock calibration mode and print the result.

This is the shortest honest answer to "do these disparity scores mean anything?". It plants
known ground truth in the target, runs the whole suite, and shows what the evaluators did
with it.

    cd backend
    python scripts/calibrate.py

Expected:

    fair      0 findings   - identical output must score zero, or the tool cries wolf
    biased    a finding on exactly the probes carrying a planted marker, and nowhere else
    refusing  refusal_rate dominant on exactly those probes
    noisy     findings everywhere - these are artifacts of hash-seeded variation, not bias

No API key, no database and no network required.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.evaluators.registry import evaluator_registry
from app.probes.base import ProbeContext
from app.probes.registry import probe_registry
from app.services.target_adapters import (
    _DEFAULT_PLANTED_MARKERS,
    target_adapter_registry,
)

MODES = ["fair", "biased", "refusing", "noisy"]


def is_marked(probe) -> bool:
    return any(
        marker in " ".join(subs.values())
        for subs in probe.groups.values()
        for marker in _DEFAULT_PLANTED_MARKERS
    )


async def run_mode(mode: str) -> list[dict]:
    adapter = target_adapter_registry.get("mock")
    evaluator = evaluator_registry.get("composite-disparity")
    configuration = {"model_name": "mock-model", "mode": mode}

    rows = []
    for probe in probe_registry.list():
        case = await probe.generate(ProbeContext())
        responses = {
            variant.group: await adapter.complete(variant.prompt, configuration)
            for variant in case.variants
        }
        result = await evaluator.evaluate(await probe.execute(case, responses))
        rows.append(
            {
                "probe": probe.id,
                "marked": is_marked(probe),
                "score": result["disparity_score"],
                "severity": result["severity"],
                "metric": result["dominant_metric"],
                "arms": result["arm_count"],
                "low_signal": result["low_signal"],
            }
        )
    return rows


async def main() -> None:
    threshold = get_settings().disparity_warning_threshold
    print(f"Warning threshold: {threshold}  |  probes: {len(probe_registry.list())}\n")

    for mode in MODES:
        rows = await run_mode(mode)
        findings = [row for row in rows if row["score"] >= threshold]
        marked = [row for row in rows if row["marked"]]

        print(f"=== mode: {mode} ===")
        print(f"  findings                  : {len(findings)} / {len(rows)}")
        if mode in ("biased", "refusing"):
            hit = sum(1 for row in marked if row["score"] >= threshold)
            stray = sum(1 for row in rows if not row["marked"] and row["score"] >= threshold)
            print(f"  planted probes that fired : {hit} / {len(marked)}   (want all)")
            print(f"  unplanted probes that fired: {stray}              (want 0)")
        if mode == "fair" and findings:
            print("  FAILED: identical output produced findings")
        for row in sorted(findings, key=lambda r: -r["score"])[:4]:
            flag = " low-signal" if row["low_signal"] else ""
            print(
                f"    {row['score']:.3f} {row['severity']:<9}{row['metric']:<34}"
                f"{row['arms']} arms{flag}  {row['probe']}"
            )
        print()

    print(
        "Reminder: passing calibration shows the evaluators react correctly to a signal\n"
        "planted in synthetic text. It does not show that the metrics are meaningful on\n"
        "real model output."
    )


if __name__ == "__main__":
    asyncio.run(main())
