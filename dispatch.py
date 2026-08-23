"""
GreenGrid Production Workload Dispatcher CLI.

Provides command-line interfaces for DevOps and ML engineers to evaluate,
benchmark, and route real compute workloads to the greenest global data center node.
"""

import argparse
import json
import sys
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from grid_data import GridTelemetryService, REGIONAL_PROFILES


class DispatchRequest(BaseModel):
    """Workload specification submitted for carbon-optimal routing."""
    job_id: str = Field(..., description="Unique compute job identifier")
    compute_units: float = Field(..., gt=0, description="Normalized compute resource requirements (e.g. GPU-hours)")
    deadline_hours: float = Field(default=4.0, gt=0, description="Maximum SLA execution window")
    priority: str = Field(default="medium", description="Priority tier: low, medium, high")
    hour_of_day: float = Field(default=14.0, ge=0.0, le=24.0, description="Current UTC hour")


class DispatchDecision(BaseModel):
    """Optimal routing recommendation with comparative carbon and cost metrics."""
    job_id: str
    optimal_region: str
    optimal_region_id: str
    instantaneous_carbon_g_kwh: float
    estimated_emissions_kg_co2: float
    estimated_cost_usd: float
    worst_case_region: str
    worst_case_emissions_kg_co2: float
    carbon_savings_percent: float
    dispatch_status: str


class WorkloadDispatcher:
    """Evaluates real regional grid telemetry and computes optimal workload placement."""

    def __init__(self):
        self.telemetry = GridTelemetryService()

    def route_workload(self, request: DispatchRequest) -> DispatchDecision:
        nodes = self.telemetry.get_all_nodes_telemetry(hour_of_day=request.hour_of_day)

        # Compute carbon and cost for each region
        evaluations: List[Dict] = []
        for node in nodes:
            # Formula: Emissions (kg) = (compute_units * carbon_intensity * PUE * 0.1 kWh per unit) / 1000
            power_consumption_kwh = request.compute_units * node["pue"] * 0.45  # e.g., 450W per unit
            carbon_kg = (power_consumption_kwh * node["carbon_intensity"]) / 1000.0
            cost_usd = power_consumption_kwh * node["cost_per_kwh_usd"]

            evaluations.append({
                "name": node["name"],
                "region_id": node["region_id"],
                "carbon_intensity": node["carbon_intensity"],
                "carbon_kg": carbon_kg,
                "cost_usd": cost_usd,
            })

        # Find best (minimum carbon) and worst (maximum carbon)
        best_node = min(evaluations, key=lambda x: x["carbon_kg"])
        worst_node = max(evaluations, key=lambda x: x["carbon_kg"])

        savings_pct = 0.0
        if worst_node["carbon_kg"] > 0:
            savings_pct = ((worst_node["carbon_kg"] - best_node["carbon_kg"]) / worst_node["carbon_kg"]) * 100.0

        return DispatchDecision(
            job_id=request.job_id,
            optimal_region=best_node["name"],
            optimal_region_id=best_node["region_id"],
            instantaneous_carbon_g_kwh=best_node["carbon_intensity"],
            estimated_emissions_kg_co2=round(best_node["carbon_kg"], 4),
            estimated_cost_usd=round(best_node["cost_usd"], 4),
            worst_case_region=worst_node["name"],
            worst_case_emissions_kg_co2=round(worst_node["carbon_kg"], 4),
            carbon_savings_percent=round(savings_pct, 1),
            dispatch_status="ROUTED_OPTIMAL",
        )

    def print_grid_status(self, hour: float = 14.0):
        nodes = self.telemetry.get_all_nodes_telemetry(hour_of_day=hour)
        print("=" * 88)
        print(f"GreenGrid Live Regional Telemetry (Simulated UTC Hour: {hour:04.1f})")
        print("=" * 88)
        print(f"{'Data Center':<14} | {'Region ID':<10} | {'Operator':<24} | {'Carbon (gCO2/kWh)':<18} | {'Cost ($/kWh)':<12}")
        print("-" * 88)
        for n in nodes:
            print(f"{n['name']:<14} | {n['region_id']:<10} | {n['grid_operator']:<24} | {n['carbon_intensity']:<18.1f} | ${n['cost_per_kwh_usd']:<12.3f}")
        print("=" * 88)


def main():
    parser = argparse.ArgumentParser(description="GreenGrid Production Workload Dispatcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Status Command
    status_parser = subparsers.add_parser("status", help="Display real-time regional grid carbon metrics")
    status_parser.add_argument("--hour", type=float, default=14.0, help="UTC Hour (0-24)")

    # Dispatch Command
    dispatch_parser = subparsers.add_parser("dispatch", help="Route a compute workload to optimal green region")
    dispatch_parser.add_argument("--job-id", type=str, required=True, help="Job identifier")
    dispatch_parser.add_argument("--compute-units", type=float, required=True, help="Compute units (e.g. GPU hours)")
    dispatch_parser.add_argument("--deadline", type=float, default=4.0, help="SLA deadline in hours")
    dispatch_parser.add_argument("--priority", type=str, choices=["low", "medium", "high"], default="medium")
    dispatch_parser.add_argument("--hour", type=float, default=14.0, help="Current UTC hour")
    dispatch_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()
    dispatcher = WorkloadDispatcher()

    if args.command == "status":
        dispatcher.print_grid_status(hour=args.hour)

    elif args.command == "dispatch":
        req = DispatchRequest(
            job_id=args.job_id,
            compute_units=args.compute_units,
            deadline_hours=args.deadline,
            priority=args.priority,
            hour_of_day=args.hour,
        )
        decision = dispatcher.route_workload(req)

        if args.json:
            print(decision.model_dump_json(indent=2))
        else:
            print("=" * 72)
            print(f"GreenGrid Optimal Workload Placement: {decision.job_id}")
            print("=" * 72)
            print(f"  Target Data Center     : {decision.optimal_region} ({decision.optimal_region_id})")
            print(f"  Instantaneous Carbon   : {decision.instantaneous_carbon_g_kwh:.1f} gCO2/kWh")
            print(f"  Estimated Carbon Total : {decision.estimated_emissions_kg_co2:.4f} kg CO2e")
            print(f"  Estimated Energy Cost  : ${decision.estimated_cost_usd:.4f}")
            print(f"  Carbon Savings         : {decision.carbon_savings_percent:.1f}% reduction vs {decision.worst_case_region}")
            print(f"  Routing Status         : {decision.dispatch_status}")
            print("=" * 72)


if __name__ == "__main__":
    main()
