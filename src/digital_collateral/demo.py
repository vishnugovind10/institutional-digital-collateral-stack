from __future__ import annotations

import argparse
import json
from pathlib import Path

from digital_collateral.control_plane import SettlementObligation, format_summary, summarize_results
from digital_collateral.core import result_to_json, run_scenario
from digital_collateral.scenarios import SCENARIOS


def money(value: int) -> str:
    return f"{value:,.0f}"


def render(result) -> str:
    concentration = "HIGH" if result.peak_liquidity_demand > result.available_liquidity else "MODERATE"
    return f"""INSTITUTIONAL DIGITAL COLLATERAL STACK
--------------------------------------

Scenario:
  name: {result.scenario}
  transaction: {result.transaction_id}

Collateral:
  status: {result.collateral_status}
  gross value: {money(result.gross_value)}
  haircut: {result.haircut:.1%}
  eligible value: {money(result.eligible_value)}

Custody:
  authorization: {result.custody_status}

Settlement:
  DvP state: {result.settlement_state}
  finality: {result.finality_state}

Liquidity:
  required aggregate: {money(result.required_liquidity)}
  peak demand: {money(result.peak_liquidity_demand)}
  available: {money(result.available_liquidity)}
  temporal concentration: {concentration}
  status: {result.liquidity_status}

Outcome:
  {result.settlement_state}

Reason:
  {result.reason}

Reconciliation:
  {result.reconciliation_status}

Evidence:
  {result.evidence_status}

Exception:
  category: {result.exception.category}
  code: {result.exception.code}
  failed_at: {result.exception.failed_at}
  recoverable: {result.exception.recoverable}
  escalation_required: {result.exception.escalation_required}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic digital collateral scenarios.")
    parser.add_argument("--scenario", default="canonical-success", choices=sorted(SCENARIOS))
    parser.add_argument("--json", action="store_true", help="print the full result JSON")
    parser.add_argument("--control-plane-summary", action="store_true", help="run a deterministic control-plane portfolio")
    parser.add_argument("--write-evidence", type=Path, help="write evidence JSON to this path")
    args = parser.parse_args(argv)

    if args.control_plane_summary:
        portfolio = [
            SettlementObligation(name, SCENARIOS[name])
            for name in (
                "canonical-success",
                "staggered-success",
                "securitisation-settlement",
                "temporal-liquidity-failure",
                "reconciliation-divergence",
                "evidence-incomplete",
            )
        ]
        print(format_summary(summarize_results([run_scenario(item.scenario) for item in portfolio])))
        return 0

    result = run_scenario(SCENARIOS[args.scenario])
    if args.write_evidence:
        args.write_evidence.parent.mkdir(parents=True, exist_ok=True)
        args.write_evidence.write_text(json.dumps(result.evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result_to_json(result) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
