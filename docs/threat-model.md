# Threat Model

## Protected assets

- Correct settlement state.
- Correct reconciliation result.
- Evidence integrity.
- Clear separation between assertion and verification.
- Explicit uncertainty when observer scope is incomplete.

## Threat actors

| Actor | Capability | Control |
|---|---|---|
| Malicious operator | Attempts to force success despite failure | State-machine invariants |
| Compromised service | Emits inconsistent state | Reconciliation comparison |
| Stale observer | Uses old or partial evidence | Evidence completeness boundary |
| Dishonest counterparty | Supplies unsupported claims | `TRUST_REQUIRED` classification |
| Inconsistent data source | Disagrees with another system | Divergence detection |
| Replay attacker | Reuses prior event | Duplicate transition rejection |
| Evidence tamperer | Edits proof artifact | Integrity hash verification |
| Timing manipulator | Synchronizes obligations | Peak liquidity calculation |

## Security goals

- Explicit state transitions.
- No silent reconciliation failure.
- Deterministic evidence.
- Tamper detection.
- Separation of assertion versus verification.
- No false `VERIFIED` status.

## Non-goals

- Legal finality.
- Real-world solvency.
- Full economic security.
- Network consensus security.
- Production custody security.
- HSM security.
- Regulatory compliance certification.
