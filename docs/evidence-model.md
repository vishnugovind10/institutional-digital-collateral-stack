# Evidence Model

Evidence is generated as deterministic JSON with an `integrity_hash`.

## Classifications

- `SELF_EVIDENT`: visible and re-derivable within the configured observer boundary.
- `OBSERVED`: visible but not independently authoritative.
- `TRUST_REQUIRED`: depends on a counterparty or external assertion.
- `BEYOND_HORIZON`: required state is outside the observer's view.

## False-verification rule

`VERIFIED` is only valid when:

- settlement reached `EVIDENCE_VERIFIED`
- reconciliation is `MATCHED`
- observer classification is `SELF_EVIDENT`
- the integrity hash validates

All other complete-but-not-independent cases must use `ASSERTED`, `TRUST_REQUIRED`, `PARTIAL`, `BEYOND_HORIZON`, or `FAILED`.
