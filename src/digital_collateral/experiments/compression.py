from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompressionWindow:
    name: str
    settlement_hours: float
    obligations: int
    total_obligation_value: int
    available_liquidity: int
    authorization_validity_hours: float
    evidence_automation: float


@dataclass(frozen=True)
class CompressionResult:
    window: str
    settlement_latency_hours: float
    liquidity_concentration: float
    peak_liquidity_demand: int
    state_divergence: float
    reconciliation_latency_hours: float
    authorization_validity: str
    evidence_completeness: float
    exception_frequency: float
    binding_constraint: str


WINDOWS = (
    CompressionWindow("30D", 720, 24, 120_000_000, 95_000_000, 168, 0.50),
    CompressionWindow("10D", 240, 24, 120_000_000, 95_000_000, 120, 0.58),
    CompressionWindow("T+2", 48, 24, 120_000_000, 95_000_000, 48, 0.66),
    CompressionWindow("T+1", 24, 24, 120_000_000, 95_000_000, 24, 0.74),
    CompressionWindow("T+0", 8, 24, 120_000_000, 95_000_000, 8, 0.82),
    CompressionWindow("Intraday", 2, 24, 120_000_000, 95_000_000, 4, 0.90),
    CompressionWindow("Continuous", 0.25, 24, 120_000_000, 95_000_000, 1, 0.96),
)


def run_compression_experiment(windows: tuple[CompressionWindow, ...] = WINDOWS) -> list[CompressionResult]:
    results: list[CompressionResult] = []
    for window in windows:
        concentration = min(1.0, 8 / window.settlement_hours) if window.settlement_hours else 1.0
        demand_multiplier = 0.35 + concentration
        peak_demand = round(window.total_obligation_value * demand_multiplier)
        divergence = round(min(0.25, 0.02 + concentration * 0.16), 4)
        reconciliation_latency = max(0.05, window.settlement_hours * (0.12 - window.evidence_automation * 0.05))
        authorization_validity = (
            "VALID" if window.authorization_validity_hours >= min(window.settlement_hours, 24) else "COMPRESSED"
        )
        liquidity_exception = peak_demand > window.available_liquidity
        evidence_gap = 1 - window.evidence_automation
        exception_frequency = min(1.0, (0.05 if liquidity_exception else 0.01) + divergence + evidence_gap * 0.12)
        binding = "LIQUIDITY" if liquidity_exception else "RECONCILIATION"
        if authorization_validity == "COMPRESSED":
            binding = "AUTHORIZATION"
        if window.evidence_automation < 0.7:
            binding = "EVIDENCE"
        results.append(
            CompressionResult(
                window=window.name,
                settlement_latency_hours=window.settlement_hours,
                liquidity_concentration=round(concentration, 4),
                peak_liquidity_demand=peak_demand,
                state_divergence=divergence,
                reconciliation_latency_hours=round(reconciliation_latency, 2),
                authorization_validity=authorization_validity,
                evidence_completeness=window.evidence_automation,
                exception_frequency=round(exception_frequency, 4),
                binding_constraint=binding,
            )
        )
    return results


def render_results(results: list[CompressionResult]) -> str:
    lines = [
        "SETTLEMENT COMPRESSION EXPERIMENT",
        "---------------------------------",
        "",
        "Evidence: public industry material describes T+1/continuous-settlement pressure.",
        "Model assumptions: synthetic obligation values, liquidity, automation and timing windows.",
        "Simulation results: generated deterministically by this repository.",
        "",
        "| Window | Peak Liquidity | Divergence | Recon Latency | Exceptions | Binding Constraint |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for result in results:
        lines.append(
            f"| {result.window} | {result.peak_liquidity_demand:,.0f} | {result.state_divergence:.1%} | "
            f"{result.reconciliation_latency_hours:.2f}h | {result.exception_frequency:.1%} | {result.binding_constraint} |"
        )
    return "\n".join(lines)


def main() -> int:
    results = run_compression_experiment()
    print(render_results(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

