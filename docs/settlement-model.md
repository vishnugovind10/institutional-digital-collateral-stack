# Settlement Model

The settlement model is explicit because institutional settlement cannot be reduced to a single success flag.

## States

```text
TRADE_CONFIRMED
COMPLIANCE_APPROVED
COLLATERAL_ELIGIBLE
ASSET_AVAILABLE
CASH_AVAILABLE
CUSTODY_AUTHORIZED
SETTLEMENT_READY
SETTLING
FINALITY_PENDING
SETTLED
RECONCILIATION_PENDING
RECONCILED
EVIDENCE_VERIFIED
EXCEPTION
ABSTAINED
```

## Rule

A scenario must move through allowed transitions only. `EXCEPTION` captures operational failure. `ABSTAINED` captures incomplete certainty without pretending that failure or success is proven.

## Control-plane exception model

`EXCEPTION` results are classified into asset, custody, liquidity, state, settlement, or evidence categories. The classification is explanatory metadata; it does not replace the settlement state machine.
