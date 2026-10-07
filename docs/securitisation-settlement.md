# Securitisation Settlement

The securitisation scenarios model a generic synthetic institutional workflow:

```text
Originator
  -> Asset Pool
  -> Eligibility
  -> Valuation
  -> SPV / Issuer
  -> Collateral Authorization
  -> Cash Leg
  -> DvP Settlement
  -> Reconciliation
  -> Evidence
```

## Commands

```bash
python -m digital_collateral.demo --scenario securitisation-settlement
python -m digital_collateral.demo --scenario securitisation-settlement-failure
python -m digital_collateral.demo --scenario securitisation-ineligible
python -m digital_collateral.demo --scenario securitisation-cash-failure
python -m digital_collateral.demo --scenario securitisation-authorization-failure
python -m digital_collateral.demo --scenario securitisation-reconciliation-divergence
```

## Boundaries

The scenario is synthetic and generic. It does not imply PwC partnership, PwC validation, access to PwC systems, production bank integration, regulatory certification, or replication of any proprietary securitisation settlement product.

