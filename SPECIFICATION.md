# Specification

## Domain interfaces

- `CollateralAsset`: asset identifier, type, gross value, restriction status, and custodian.
- `EligibilityPolicy`: allowed collateral types and restricted-asset policy.
- `Valuation`: timestamped haircut.
- `CustodyAuthorization`: policy decision and freshness.
- `LiquidityProfile`: available liquidity, reuse depth, shock, and timed obligations.
- `LedgerViews`: asset ledger, settlement ledger, and custody intent state.
- `ObserverScope`: evidence classification and completeness.

## Evidence statuses

| Status | Meaning |
|---|---|
| `DEMO` | Fixture-only demonstration output |
| `ASSERTED` | Internally recorded but not independently proven |
| `PARTIAL` | Useful evidence exists, but settlement is not complete |
| `TRUST_REQUIRED` | Verification depends on another party or missing boundary |
| `BEYOND_HORIZON` | Required state is outside the observer's scope |
| `VERIFIED` | Internally consistent, matched, complete, and self-evident |
| `FAILED` | Hash, reconciliation, or verification rule failed |

## Scenario contract

Every scenario must return:

- transaction identifier
- collateral identifier
- valuation timestamp
- eligibility result
- haircut
- gross collateral
- eligible collateral
- aggregate and peak liquidity demand
- available liquidity
- settlement state
- finality state
- reconciliation result
- evidence classification
- integrity hash
