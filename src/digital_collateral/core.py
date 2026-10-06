from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar


class CollateralStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


class CustodyStatus(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    STALE = "STALE"


class SettlementState(StrEnum):
    TRADE_CONFIRMED = "TRADE_CONFIRMED"
    COMPLIANCE_APPROVED = "COMPLIANCE_APPROVED"
    COLLATERAL_ELIGIBLE = "COLLATERAL_ELIGIBLE"
    ASSET_AVAILABLE = "ASSET_AVAILABLE"
    CASH_AVAILABLE = "CASH_AVAILABLE"
    CUSTODY_AUTHORIZED = "CUSTODY_AUTHORIZED"
    SETTLEMENT_READY = "SETTLEMENT_READY"
    SETTLING = "SETTLING"
    FINALITY_PENDING = "FINALITY_PENDING"
    SETTLED = "SETTLED"
    RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
    RECONCILED = "RECONCILED"
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    EXCEPTION = "EXCEPTION"
    ABSTAINED = "ABSTAINED"


class FinalityState(StrEnum):
    NONE = "NONE"
    TECHNICAL_FINAL = "TECHNICAL_FINAL"
    ECONOMIC_FINAL = "ECONOMIC_FINAL"
    LEGAL_FINAL_UNDETERMINED = "LEGAL_FINAL_UNDETERMINED"


class LiquidityStatus(StrEnum):
    SUFFICIENT = "SUFFICIENT"
    SHORTFALL = "SHORTFALL"


class ReconciliationStatus(StrEnum):
    MATCHED = "MATCHED"
    DIVERGED = "DIVERGED"
    PENDING = "PENDING"


class EvidenceStatus(StrEnum):
    DEMO = "DEMO"
    ASSERTED = "ASSERTED"
    PARTIAL = "PARTIAL"
    TRUST_REQUIRED = "TRUST_REQUIRED"
    BEYOND_HORIZON = "BEYOND_HORIZON"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class EvidenceClass(StrEnum):
    SELF_EVIDENT = "SELF_EVIDENT"
    OBSERVED = "OBSERVED"
    TRUST_REQUIRED = "TRUST_REQUIRED"
    BEYOND_HORIZON = "BEYOND_HORIZON"


@dataclass(frozen=True)
class CollateralAsset:
    asset_id: str
    asset_type: str
    gross_value: int
    restricted: bool
    custodian: str


@dataclass(frozen=True)
class EligibilityPolicy:
    allowed_asset_types: tuple[str, ...]
    allow_restricted: bool = False


@dataclass(frozen=True)
class Valuation:
    valuation_timestamp: str
    haircut: float


@dataclass(frozen=True)
class CustodyAuthorization:
    status: CustodyStatus
    signer: str
    fresh: bool = True


@dataclass(frozen=True)
class Obligation:
    interval: int
    amount: int


@dataclass(frozen=True)
class LiquidityProfile:
    available: int
    reuse_depth: float
    shock: float
    obligations: tuple[Obligation, ...]


@dataclass(frozen=True)
class ObserverScope:
    classification: EvidenceClass
    evidence_complete: bool
    externally_observable: bool


@dataclass(frozen=True)
class LedgerViews:
    asset_ledger: str
    settlement_ledger: str
    custody_intent: str


@dataclass(frozen=True)
class Scenario:
    name: str
    transaction_id: str
    collateral: CollateralAsset
    policy: EligibilityPolicy
    valuation: Valuation
    custody: CustodyAuthorization
    liquidity: LiquidityProfile
    ledgers: LedgerViews
    observer: ObserverScope
    cash_available: bool = True


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    transaction_id: str
    collateral_status: CollateralStatus
    gross_value: int
    haircut: float
    eligible_value: int
    custody_status: CustodyStatus
    required_liquidity: int
    peak_liquidity_demand: int
    available_liquidity: int
    liquidity_status: LiquidityStatus
    settlement_state: SettlementState
    finality_state: FinalityState
    reconciliation_status: ReconciliationStatus
    evidence_status: EvidenceStatus
    reason: str
    evidence: dict[str, Any]


class SettlementStateMachine:
    allowed: ClassVar[dict[SettlementState, set[SettlementState]]] = {
        SettlementState.TRADE_CONFIRMED: {
            SettlementState.COMPLIANCE_APPROVED,
            SettlementState.EXCEPTION,
            SettlementState.ABSTAINED,
        },
        SettlementState.COMPLIANCE_APPROVED: {
            SettlementState.COLLATERAL_ELIGIBLE,
            SettlementState.EXCEPTION,
            SettlementState.ABSTAINED,
        },
        SettlementState.COLLATERAL_ELIGIBLE: {SettlementState.ASSET_AVAILABLE},
        SettlementState.ASSET_AVAILABLE: {SettlementState.CASH_AVAILABLE, SettlementState.EXCEPTION},
        SettlementState.CASH_AVAILABLE: {SettlementState.CUSTODY_AUTHORIZED},
        SettlementState.CUSTODY_AUTHORIZED: {SettlementState.SETTLEMENT_READY},
        SettlementState.SETTLEMENT_READY: {SettlementState.SETTLING, SettlementState.EXCEPTION},
        SettlementState.SETTLING: {SettlementState.FINALITY_PENDING, SettlementState.EXCEPTION},
        SettlementState.FINALITY_PENDING: {SettlementState.SETTLED, SettlementState.EXCEPTION},
        SettlementState.SETTLED: {
            SettlementState.RECONCILIATION_PENDING,
            SettlementState.EXCEPTION,
        },
        SettlementState.RECONCILIATION_PENDING: {
            SettlementState.RECONCILED,
            SettlementState.EXCEPTION,
        },
        SettlementState.RECONCILED: {SettlementState.EVIDENCE_VERIFIED, SettlementState.ABSTAINED},
        SettlementState.EVIDENCE_VERIFIED: set(),
        SettlementState.EXCEPTION: set(),
        SettlementState.ABSTAINED: set(),
    }

    def __init__(self) -> None:
        self.state = SettlementState.TRADE_CONFIRMED
        self.history = [self.state]

    def transition(self, next_state: SettlementState) -> None:
        if next_state == self.state:
            raise ValueError(f"duplicate settlement event: {next_state}")
        if next_state not in self.allowed[self.state]:
            raise ValueError(f"invalid transition: {self.state} -> {next_state}")
        self.state = next_state
        self.history.append(next_state)


def evaluate_eligibility(asset: CollateralAsset, policy: EligibilityPolicy) -> CollateralStatus:
    if asset.gross_value <= 0:
        raise ValueError("collateral gross value must be positive")
    if asset.asset_type not in policy.allowed_asset_types:
        return CollateralStatus.INELIGIBLE
    if asset.restricted and not policy.allow_restricted:
        return CollateralStatus.INELIGIBLE
    return CollateralStatus.ELIGIBLE


def eligible_value(asset: CollateralAsset, valuation: Valuation) -> int:
    if valuation.haircut < 0 or valuation.haircut >= 1:
        raise ValueError("haircut must be in the range [0, 1)")
    return round(asset.gross_value * (1 - valuation.haircut))


def required_liquidity(profile: LiquidityProfile) -> int:
    if profile.available < 0:
        raise ValueError("available liquidity cannot be negative")
    if profile.reuse_depth < 1:
        raise ValueError("reuse depth must be at least 1")
    if profile.shock <= 0:
        raise ValueError("shock must be positive")
    if any(o.amount <= 0 for o in profile.obligations):
        raise ValueError("obligations must be positive")
    total = sum(o.amount for o in profile.obligations)
    return round(total * profile.reuse_depth * profile.shock)


def peak_liquidity_demand(profile: LiquidityProfile) -> int:
    buckets: dict[int, int] = {}
    for obligation in profile.obligations:
        buckets[obligation.interval] = buckets.get(obligation.interval, 0) + obligation.amount
    if not buckets:
        raise ValueError("at least one obligation is required")
    return round(max(buckets.values()) * profile.reuse_depth * profile.shock)


def reconcile(ledgers: LedgerViews) -> ReconciliationStatus:
    states = {ledgers.asset_ledger, ledgers.settlement_ledger, ledgers.custody_intent}
    return ReconciliationStatus.MATCHED if len(states) == 1 else ReconciliationStatus.DIVERGED


def classify_evidence(
    settlement: SettlementState,
    reconciliation: ReconciliationStatus,
    observer: ObserverScope,
) -> EvidenceStatus:
    if observer.classification == EvidenceClass.BEYOND_HORIZON:
        return EvidenceStatus.BEYOND_HORIZON
    if observer.classification == EvidenceClass.TRUST_REQUIRED or not observer.evidence_complete:
        return EvidenceStatus.TRUST_REQUIRED
    if reconciliation == ReconciliationStatus.DIVERGED:
        return EvidenceStatus.FAILED
    if settlement == SettlementState.EVIDENCE_VERIFIED and observer.classification == EvidenceClass.SELF_EVIDENT:
        return EvidenceStatus.VERIFIED
    if settlement in {SettlementState.EXCEPTION, SettlementState.ABSTAINED}:
        return EvidenceStatus.PARTIAL
    return EvidenceStatus.ASSERTED


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def generate_evidence(result: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "schema_version": "0.1",
        "transaction_id": result["transaction_id"],
        "observed_at": "2026-01-01T00:00:00Z",
        "collateral": {
            "asset_id": result["asset_id"],
            "gross_value": result["gross_value"],
            "haircut": result["haircut"],
            "eligible_value": result["eligible_value"],
            "status": result["collateral_status"],
        },
        "liquidity": {
            "required": result["required_liquidity"],
            "peak_demand": result["peak_liquidity_demand"],
            "available": result["available_liquidity"],
            "status": result["liquidity_status"],
        },
        "settlement": {
            "state": result["settlement_state"],
            "finality": result["finality_state"],
        },
        "reconciliation": {"status": result["reconciliation_status"]},
        "evidence": {
            "status": result["evidence_status"],
            "classification": result["evidence_classification"],
        },
    }
    evidence["integrity_hash"] = canonical_hash(evidence)
    return evidence


def verify_evidence(evidence: dict[str, Any]) -> EvidenceStatus:
    candidate = dict(evidence)
    expected = candidate.pop("integrity_hash", None)
    if expected != canonical_hash(candidate):
        return EvidenceStatus.FAILED
    status = EvidenceStatus(evidence["evidence"]["status"])
    if status == EvidenceStatus.VERIFIED:
        if evidence["reconciliation"]["status"] != ReconciliationStatus.MATCHED:
            return EvidenceStatus.FAILED
        if evidence["settlement"]["state"] != SettlementState.EVIDENCE_VERIFIED:
            return EvidenceStatus.FAILED
        if evidence["evidence"]["classification"] != EvidenceClass.SELF_EVIDENT:
            return EvidenceStatus.FAILED
    return status


def run_scenario(scenario: Scenario) -> ScenarioResult:
    valuation_time = datetime.fromisoformat(scenario.valuation.valuation_timestamp)
    if valuation_time.tzinfo is None:
        raise ValueError("valuation timestamp must be timezone-aware")
    now = datetime(2026, 1, 1, tzinfo=UTC)
    if valuation_time > now:
        raise ValueError("valuation timestamp cannot be in the future for deterministic scenarios")

    collateral_status = evaluate_eligibility(scenario.collateral, scenario.policy)
    eligible = eligible_value(scenario.collateral, scenario.valuation)
    required = required_liquidity(scenario.liquidity)
    peak = peak_liquidity_demand(scenario.liquidity)
    liquidity_status = (
        LiquidityStatus.SUFFICIENT if peak <= scenario.liquidity.available else LiquidityStatus.SHORTFALL
    )
    reconciliation_status = ReconciliationStatus.PENDING
    finality = FinalityState.NONE
    machine = SettlementStateMachine()
    reason = "OK"

    machine.transition(SettlementState.COMPLIANCE_APPROVED)
    if collateral_status != CollateralStatus.ELIGIBLE:
        machine.transition(SettlementState.EXCEPTION)
        reason = "COLLATERAL_INELIGIBLE"
    elif not scenario.cash_available:
        machine.transition(SettlementState.COLLATERAL_ELIGIBLE)
        machine.transition(SettlementState.ASSET_AVAILABLE)
        machine.transition(SettlementState.EXCEPTION)
        reason = "CASH_LEG_UNAVAILABLE"
    elif scenario.custody.status != CustodyStatus.APPROVED or not scenario.custody.fresh:
        machine.transition(SettlementState.COLLATERAL_ELIGIBLE)
        machine.transition(SettlementState.ASSET_AVAILABLE)
        machine.transition(SettlementState.CASH_AVAILABLE)
        machine.transition(SettlementState.EXCEPTION)
        reason = "CUSTODY_NOT_AUTHORIZED"
    elif liquidity_status == LiquidityStatus.SHORTFALL:
        machine.transition(SettlementState.COLLATERAL_ELIGIBLE)
        machine.transition(SettlementState.ASSET_AVAILABLE)
        machine.transition(SettlementState.CASH_AVAILABLE)
        machine.transition(SettlementState.CUSTODY_AUTHORIZED)
        machine.transition(SettlementState.SETTLEMENT_READY)
        machine.transition(SettlementState.EXCEPTION)
        reason = "SYNCHRONIZED_LIQUIDITY_SHORTFALL"
        reconciliation_status = ReconciliationStatus.PENDING
    else:
        machine.transition(SettlementState.COLLATERAL_ELIGIBLE)
        machine.transition(SettlementState.ASSET_AVAILABLE)
        machine.transition(SettlementState.CASH_AVAILABLE)
        machine.transition(SettlementState.CUSTODY_AUTHORIZED)
        machine.transition(SettlementState.SETTLEMENT_READY)
        machine.transition(SettlementState.SETTLING)
        machine.transition(SettlementState.FINALITY_PENDING)
        machine.transition(SettlementState.SETTLED)
        finality = FinalityState.ECONOMIC_FINAL
        machine.transition(SettlementState.RECONCILIATION_PENDING)
        reconciliation_status = reconcile(scenario.ledgers)
        if reconciliation_status == ReconciliationStatus.MATCHED:
            machine.transition(SettlementState.RECONCILED)
            if scenario.observer.evidence_complete:
                machine.transition(SettlementState.EVIDENCE_VERIFIED)
            else:
                machine.transition(SettlementState.ABSTAINED)
                reason = "EVIDENCE_INCOMPLETE"
        else:
            machine.transition(SettlementState.EXCEPTION)
            reason = "RECONCILIATION_DIVERGENCE"

    evidence_status = classify_evidence(machine.state, reconciliation_status, scenario.observer)
    raw = {
        "transaction_id": scenario.transaction_id,
        "asset_id": scenario.collateral.asset_id,
        "gross_value": scenario.collateral.gross_value,
        "haircut": scenario.valuation.haircut,
        "eligible_value": eligible,
        "collateral_status": collateral_status,
        "required_liquidity": required,
        "peak_liquidity_demand": peak,
        "available_liquidity": scenario.liquidity.available,
        "liquidity_status": liquidity_status,
        "settlement_state": machine.state,
        "finality_state": finality,
        "reconciliation_status": reconciliation_status,
        "evidence_status": evidence_status,
        "evidence_classification": scenario.observer.classification,
    }
    evidence = generate_evidence({k: str(v) if isinstance(v, StrEnum) else v for k, v in raw.items()})
    return ScenarioResult(
        scenario=scenario.name,
        transaction_id=scenario.transaction_id,
        collateral_status=collateral_status,
        gross_value=scenario.collateral.gross_value,
        haircut=scenario.valuation.haircut,
        eligible_value=eligible,
        custody_status=scenario.custody.status,
        required_liquidity=required,
        peak_liquidity_demand=peak,
        available_liquidity=scenario.liquidity.available,
        liquidity_status=liquidity_status,
        settlement_state=machine.state,
        finality_state=finality,
        reconciliation_status=reconciliation_status,
        evidence_status=evidence_status,
        reason=reason,
        evidence=evidence,
    )


def result_to_json(result: ScenarioResult) -> str:
    def encode(value: Any) -> Any:
        if isinstance(value, StrEnum):
            return str(value)
        return value

    return json.dumps(asdict(result), default=encode, indent=2, sort_keys=True)
