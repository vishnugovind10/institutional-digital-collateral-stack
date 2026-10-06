from digital_collateral.core import (
    CollateralAsset,
    CustodyAuthorization,
    CustodyStatus,
    EligibilityPolicy,
    EvidenceClass,
    LedgerViews,
    LiquidityProfile,
    Obligation,
    ObserverScope,
    Scenario,
    Valuation,
)

BASE_COLLATERAL = CollateralAsset(
    asset_id="UST-2026-A",
    asset_type="US_TREASURY_TOKEN",
    gross_value=10_000_000,
    restricted=False,
    custodian="SYNTHETIC_CUSTODIAN",
)

BASE_POLICY = EligibilityPolicy(allowed_asset_types=("US_TREASURY_TOKEN",))
BASE_VALUATION = Valuation(valuation_timestamp="2026-01-01T00:00:00Z", haircut=0.02)
APPROVED_CUSTODY = CustodyAuthorization(status=CustodyStatus.APPROVED, signer="policy-engine")
MATCHED_LEDGERS = LedgerViews(
    asset_ledger="SETTLED",
    settlement_ledger="SETTLED",
    custody_intent="SETTLED",
)
SELF_EVIDENT = ObserverScope(
    classification=EvidenceClass.SELF_EVIDENT,
    evidence_complete=True,
    externally_observable=True,
)


SCENARIOS: dict[str, Scenario] = {
    "canonical-success": Scenario(
        name="24/7 Margin Collateral Mobilization",
        transaction_id="COLL-2026-0001",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=9_000_000,
            reuse_depth=1.05,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000), Obligation(interval=2, amount=4_000_000)),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=SELF_EVIDENT,
    ),
    "temporal-liquidity-failure": Scenario(
        name="Synchronized margin calls",
        transaction_id="COLL-2026-0002",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=8_000_000,
            reuse_depth=1.05,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000), Obligation(interval=1, amount=4_000_000)),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=ObserverScope(EvidenceClass.TRUST_REQUIRED, evidence_complete=False, externally_observable=False),
    ),
    "staggered-success": Scenario(
        name="Staggered margin calls",
        transaction_id="COLL-2026-0003",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=8_000_000,
            reuse_depth=1.05,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000), Obligation(interval=2, amount=4_000_000)),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=SELF_EVIDENT,
    ),
    "cash-leg-failure": Scenario(
        name="Asset ready, cash unavailable",
        transaction_id="COLL-2026-0004",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=9_000_000,
            reuse_depth=1.0,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000),),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=SELF_EVIDENT,
        cash_available=False,
    ),
    "restricted-collateral": Scenario(
        name="Restricted collateral denied",
        transaction_id="COLL-2026-0005",
        collateral=CollateralAsset("PRIV-FUND-2026-A", "PRIVATE_FUND_TOKEN", 10_000_000, True, "SYNTHETIC_CUSTODIAN"),
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=9_000_000,
            reuse_depth=1.0,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000),),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=SELF_EVIDENT,
    ),
    "reconciliation-divergence": Scenario(
        name="Ledger state divergence",
        transaction_id="COLL-2026-0006",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=9_000_000,
            reuse_depth=1.0,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000),),
        ),
        ledgers=LedgerViews("SETTLED", "SETTLED", "AUTHORIZED_ONLY"),
        observer=SELF_EVIDENT,
    ),
    "evidence-incomplete": Scenario(
        name="Settlement with incomplete evidence",
        transaction_id="COLL-2026-0007",
        collateral=BASE_COLLATERAL,
        policy=BASE_POLICY,
        valuation=BASE_VALUATION,
        custody=APPROVED_CUSTODY,
        liquidity=LiquidityProfile(
            available=9_000_000,
            reuse_depth=1.0,
            shock=1.0,
            obligations=(Obligation(interval=1, amount=4_000_000),),
        ),
        ledgers=MATCHED_LEDGERS,
        observer=ObserverScope(EvidenceClass.TRUST_REQUIRED, evidence_complete=False, externally_observable=False),
    ),
}
