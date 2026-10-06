# Security

## Supported versions

Version `0.1.x` receives security fixes for the reference implementation.

## Reporting

Open a private security advisory on GitHub or contact the repository owner through GitHub. Do not include real credentials, production infrastructure details, or customer data in reports.

## Security assumptions

- Inputs are synthetic unless explicitly marked otherwise.
- Evidence integrity is SHA-256 hash integrity over deterministic JSON, not a legal attestation.
- Observer scope is explicit and may be incomplete.
- No secret material is required to run the project.

## What this project does not secure

This project does not secure real funds, custody workflows, private keys, bank systems, market data feeds, production ledgers, HSMs, MPC deployments, or regulatory reporting.

## Secret handling

Do not commit private keys, API keys, customer data, private URLs, internal hostnames, descriptors, credentials, or confidential source material.

## Dependency security

The runtime implementation uses only the Python standard library. Development dependencies are limited to `pytest` and `ruff`.

## Replay and tampering

Evidence includes an integrity hash and tests reject tampering. The hash does not prove completeness, legal finality, or external truth.

## Production custody guarantee

There is none. The custody module is a policy boundary for deterministic scenarios only.
