# Liquidity Model

The model is deterministic and intentionally small.

```text
required_liquidity = obligation_amount * reuse_depth * shock
```

Aggregate requirement measures total demand. Peak demand measures the largest interval after obligations are bucketed by time.

## Synchronized case

Two obligations of 4,000,000 arrive in the same interval:

```text
peak = 8,000,000 * 1.05 = 8,400,000
available = 8,000,000
outcome = EXCEPTION
```

## Staggered case

The same obligations arrive in separate intervals:

```text
peak = 4,000,000 * 1.05 = 4,200,000
available = 8,000,000
outcome = EVIDENCE_VERIFIED
```

The balance-sheet totals are the same. Timing changes the binding constraint.
