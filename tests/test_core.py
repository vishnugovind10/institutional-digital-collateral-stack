import pytest

from digital_collateral.control_plane import SettlementObligation, summarize_results
from digital_collateral.core import (
    CollateralAsset,
    CustodyStatus,
    EligibilityPolicy,
    EvidenceStatus,
    ExceptionCategory,
    ExceptionCode,
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
from digital_collateral.experiments.compression import run_compression_experiment
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


@pytest.mark.parametrize(
    ("name", "state", "reason", "category", "code"),
    [
        ("securitisation-settlement", SettlementState.EVIDENCE_VERIFIED, "OK", ExceptionCategory.NONE, ExceptionCode.NONE),
        (
            "securitisation-settlement-failure",
            SettlementState.EXCEPTION,
            "SYNCHRONIZED_LIQUIDITY_SHORTFALL",
            ExceptionCategory.LIQUIDITY,
            ExceptionCode.TEMPORAL_CONCENTRATION,
        ),
        (
            "securitisation-ineligible",
            SettlementState.EXCEPTION,
            "COLLATERAL_INELIGIBLE",
            ExceptionCategory.ASSET,
            ExceptionCode.INELIGIBLE,
        ),
        (
            "securitisation-cash-failure",
            SettlementState.EXCEPTION,
            "CASH_LEG_UNAVAILABLE",
            ExceptionCategory.SETTLEMENT,
            ExceptionCode.DVP_FAILURE,
        ),
        (
            "securitisation-authorization-failure",
            SettlementState.EXCEPTION,
            "CUSTODY_NOT_AUTHORIZED",
            ExceptionCategory.CUSTODY,
            ExceptionCode.AUTHORIZATION_CONFLICT,
        ),
        (
            "securitisation-reconciliation-divergence",
            SettlementState.EXCEPTION,
            "RECONCILIATION_DIVERGENCE",
            ExceptionCategory.STATE,
            ExceptionCode.LEDGER_DIVERGENCE,
        ),
    ],
)
def test_securitisation_scenarios(name, state, reason, category, code):
    result = run_scenario(SCENARIOS[name])
    assert result.settlement_state == state
    assert result.reason == reason
    assert result.exception.category == category
    assert result.exception.code == code


def test_control_plane_summary_aggregates_obligations_and_exceptions():
    obligations = [
        SettlementObligation(name, SCENARIOS[name])
        for name in ("canonical-success", "securitisation-settlement", "temporal-liquidity-failure")
    ]
    summary = summarize_results([run_scenario(obligation.scenario) for obligation in obligations])
    assert summary.obligations == 3
    assert summary.settlement_ready == 2
    assert summary.exceptions == 1
    assert summary.settlement_success_rate == pytest.approx(2 / 3)
    assert summary.status == "DEGRADED"


def test_compression_experiment_orders_windows_and_constraints():
    results = run_compression_experiment()
    by_window = {result.window: result for result in results}
    assert [result.window for result in results] == ["30D", "10D", "T+2", "T+1", "T+0", "Intraday", "Continuous"]
    assert by_window["30D"].settlement_latency_hours > by_window["T+1"].settlement_latency_hours
    assert by_window["Continuous"].liquidity_concentration > by_window["T+1"].liquidity_concentration
    assert by_window["Continuous"].peak_liquidity_demand > by_window["30D"].peak_liquidity_demand
    assert by_window["Continuous"].binding_constraint == "LIQUIDITY"


def test_staggered_liquidity_still_succeeds_after_control_plane_upgrade():
    staggered = run_scenario(SCENARIOS["staggered-success"])
    synchronized = run_scenario(SCENARIOS["temporal-liquidity-failure"])
    assert staggered.peak_liquidity_demand < synchronized.peak_liquidity_demand
    assert staggered.settlement_state == SettlementState.EVIDENCE_VERIFIED
    assert synchronized.settlement_state == SettlementState.EXCEPTION
