from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from digital_collateral.core import (
    EvidenceStatus,
    Scenario,
    ScenarioResult,
    SettlementState,
    run_scenario,
)


class ControlPlaneStatus(StrEnum):
    OPERATIONAL = "OPERATIONAL"
    DEGRADED = "DEGRADED"
    EXCEPTION = "EXCEPTION"


@dataclass(frozen=True)
class SettlementObligation:
    obligation_id: str
    scenario: Scenario


@dataclass(frozen=True)
class ControlPlaneSummary:
    obligations: int
    settlement_ready: int
    settling: int
    exceptions: int
    collateral_value: int
    eligible_value: int
    liquidity_available: int
    peak_liquidity_demand: int
    settlement_success_rate: float
    evidence_verified_rate: float
    reconciliation_divergence_rate: float
    status: ControlPlaneStatus


def execute_obligation(obligation: SettlementObligation) -> ScenarioResult:
    return run_scenario(obligation.scenario)


def summarize_results(results: list[ScenarioResult]) -> ControlPlaneSummary:
    if not results:
        raise ValueError("at least one result is required")
    obligations = len(results)
    exceptions = sum(1 for result in results if result.settlement_state == SettlementState.EXCEPTION)
    successful = sum(1 for result in results if result.settlement_state == SettlementState.EVIDENCE_VERIFIED)
    verified = sum(1 for result in results if result.evidence_status == EvidenceStatus.VERIFIED)
    diverged = sum(1 for result in results if result.reason == "RECONCILIATION_DIVERGENCE")
    settlement_ready = sum(
        1
        for result in results
        if result.settlement_state in {SettlementState.SETTLING, SettlementState.SETTLED, SettlementState.RECONCILED, SettlementState.EVIDENCE_VERIFIED}
    )
    settling = sum(1 for result in results if result.settlement_state == SettlementState.SETTLING)
    status = ControlPlaneStatus.OPERATIONAL
    if exceptions:
        status = ControlPlaneStatus.DEGRADED if successful else ControlPlaneStatus.EXCEPTION
    return ControlPlaneSummary(
        obligations=obligations,
        settlement_ready=settlement_ready,
        settling=settling,
        exceptions=exceptions,
        collateral_value=sum(result.gross_value for result in results),
        eligible_value=sum(result.eligible_value for result in results),
        liquidity_available=sum(result.available_liquidity for result in results),
        peak_liquidity_demand=sum(result.peak_liquidity_demand for result in results),
        settlement_success_rate=successful / obligations,
        evidence_verified_rate=verified / obligations,
        reconciliation_divergence_rate=diverged / obligations,
        status=status,
    )


def format_summary(summary: ControlPlaneSummary) -> str:
    return f"""INSTITUTIONAL SETTLEMENT CONTROL PLANE
--------------------------------------

Obligations                 {summary.obligations}
Settlement Ready            {summary.settlement_ready}
Settling                    {summary.settling}
Exceptions                  {summary.exceptions}

Collateral Value        {summary.collateral_value:,.0f}
Eligible Value          {summary.eligible_value:,.0f}
Liquidity Available     {summary.liquidity_available:,.0f}
Peak Liquidity Demand   {summary.peak_liquidity_demand:,.0f}

Settlement Success      {summary.settlement_success_rate:.1%}
Evidence Verified       {summary.evidence_verified_rate:.1%}
Reconciliation Divergence {summary.reconciliation_divergence_rate:.1%}

Control Plane Status:
{summary.status}
"""
