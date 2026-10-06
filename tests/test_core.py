import pytest

from digital_collateral.core import (
    CollateralAsset,
    CustodyStatus,
    EligibilityPolicy,
    EvidenceStatus,
    LiquidityProfile,
    Obligation,
    SettlementState,
    SettlementStateMachine,
    Valuation,
    eligible_value,
    evaluate_eligibility,
    peak_liquidity_demand,
    required_liquidity,
    run_scenario,
    verify_evidence,
)
from digital_collateral.scenarios import SCENARIOS


def test_eligibility_accepts_allowed_unrestricted_asset():
    asset = CollateralAsset("UST", "US_TREASURY_TOKEN", 100, False, "custodian")
    assert evaluate_eligibility(asset, EligibilityPolicy(("US_TREASURY_TOKEN",))).value == "ELIGIBLE"


def test_eligibility_rejects_restricted_or_wrong_asset():
    restricted = CollateralAsset("FUND", "PRIVATE_FUND_TOKEN", 100, True, "custodian")
    assert evaluate_eligibility(restricted, EligibilityPolicy(("US_TREASURY_TOKEN",))).value == "INELIGIBLE"


def test_haircut_and_valuation_are_deterministic():
    asset = CollateralAsset("UST", "US_TREASURY_TOKEN", 10_000_000, False, "custodian")
    assert eligible_value(asset, Valuation("2026-01-01T00:00:00Z", 0.02)) == 9_800_000


def test_invalid_haircut_is_rejected():
    with pytest.raises(ValueError):
        eligible_value(CollateralAsset("UST", "US_TREASURY_TOKEN", 100, False, "c"), Valuation("2026-01-01T00:00:00Z", 1.0))


def test_temporal_liquidity_peak_depends_on_timing():
    synchronized = LiquidityProfile(8_000_000, 1.05, 1.0, (Obligation(1, 4_000_000), Obligation(1, 4_000_000)))
    staggered = LiquidityProfile(8_000_000, 1.05, 1.0, (Obligation(1, 4_000_000), Obligation(2, 4_000_000)))
    assert required_liquidity(synchronized) == required_liquidity(staggered) == 8_400_000
    assert peak_liquidity_demand(synchronized) == 8_400_000
    assert peak_liquidity_demand(staggered) == 4_200_000


def test_state_machine_rejects_duplicate_and_bypass():
    machine = SettlementStateMachine()
    with pytest.raises(ValueError):
        machine.transition(SettlementState.SETTLED)
    machine.transition(SettlementState.COMPLIANCE_APPROVED)
    with pytest.raises(ValueError):
        machine.transition(SettlementState.COMPLIANCE_APPROVED)


@pytest.mark.parametrize(
    ("name", "state", "evidence", "reason"),
    [
        ("canonical-success", SettlementState.EVIDENCE_VERIFIED, EvidenceStatus.VERIFIED, "OK"),
        ("temporal-liquidity-failure", SettlementState.EXCEPTION, EvidenceStatus.TRUST_REQUIRED, "SYNCHRONIZED_LIQUIDITY_SHORTFALL"),
        ("staggered-success", SettlementState.EVIDENCE_VERIFIED, EvidenceStatus.VERIFIED, "OK"),
        ("cash-leg-failure", SettlementState.EXCEPTION, EvidenceStatus.PARTIAL, "CASH_LEG_UNAVAILABLE"),
        ("restricted-collateral", SettlementState.EXCEPTION, EvidenceStatus.PARTIAL, "COLLATERAL_INELIGIBLE"),
        ("reconciliation-divergence", SettlementState.EXCEPTION, EvidenceStatus.FAILED, "RECONCILIATION_DIVERGENCE"),
        ("evidence-incomplete", SettlementState.ABSTAINED, EvidenceStatus.TRUST_REQUIRED, "EVIDENCE_INCOMPLETE"),
    ],
)
def test_required_scenarios(name, state, evidence, reason):
    result = run_scenario(SCENARIOS[name])
    assert result.settlement_state == state
    assert result.evidence_status == evidence
    assert result.reason == reason
    assert verify_evidence(result.evidence) == evidence


def test_cash_leg_failure_never_reports_success():
    result = run_scenario(SCENARIOS["cash-leg-failure"])
    assert result.custody_status == CustodyStatus.APPROVED
    assert result.settlement_state == SettlementState.EXCEPTION


def test_evidence_tampering_fails():
    result = run_scenario(SCENARIOS["canonical-success"])
    tampered = dict(result.evidence)
    tampered["liquidity"] = dict(tampered["liquidity"])
    tampered["liquidity"]["available"] = 1
    assert verify_evidence(tampered) == EvidenceStatus.FAILED
