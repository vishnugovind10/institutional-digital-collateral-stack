# Architecture

This repository models digital collateral as a coordination problem, not as a token contract alone.

## Layers

1. Collateral eligibility and asset representation.
2. Valuation and haircut.
3. Custody authorization.
4. Settlement state machine and DvP readiness.
5. Temporal liquidity risk.
6. Synchronization and observer scope.
7. Reconciliation.
8. Evidence and integrity verification.

## Design boundary

The implementation is intentionally thin. It defines interfaces and deterministic execution paths that make upstream concepts interoperable without copying those repositories. Production implementations would replace every local adapter with market data, custody, bank, ledger, and audit infrastructure.

## Control flow

```text
Collateral call
  -> eligibility
  -> valuation and haircut
  -> custody authorization
  -> DvP state transition
  -> temporal liquidity check
  -> finality classification
  -> reconciliation
  -> evidence hash and verifier
```

## Invariants

- Ineligible collateral cannot reach `SETTLEMENT_READY`.
- Cash-leg failure cannot reach `SETTLED`.
- A duplicate settlement event is rejected.
- State transition bypass is rejected.
- Reconciliation divergence cannot produce `VERIFIED`.
- Incomplete observer evidence cannot produce `VERIFIED`.
- Tampered evidence returns `FAILED`.
