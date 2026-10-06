"""Executable reference architecture for institutional digital collateral."""

from digital_collateral.core import run_scenario, verify_evidence
from digital_collateral.scenarios import SCENARIOS

__all__ = ["SCENARIOS", "run_scenario", "verify_evidence"]
