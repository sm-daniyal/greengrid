from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from openenv.core.env_server.types import Action, Observation


class DatacenterState(BaseModel):
    """Real-time operational metrics for a regional data center node."""
    name: str = Field(..., description="Regional identifier (e.g., Oregon, Virginia)")
    carbon_intensity: float = Field(..., description="Instantaneous emissions in gCO2/kWh")
    server_load: float = Field(..., description="Current compute utilization percentage (0-100%)")
    cost_per_hour: float = Field(..., description="Unit operating cost in USD/hour")
    online: bool = Field(default=True, description="Operational health status")


class JobItem(BaseModel):
    """Compute workload specification in the scheduling queue."""
    job_id: str = Field(..., description="Unique workload identifier")
    compute_units: int = Field(..., description="Required compute capacity allocation")
    deadline: int = Field(..., description="Remaining execution steps before SLA breach")
    priority: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Business criticality tier"
    )


class TelemetryMetrics(BaseModel):
    """Aggregate simulation performance and sustainability telemetry."""
    jobs_completed: int = Field(default=0, description="Successfully scheduled jobs")
    jobs_failed: int = Field(default=0, description="Jobs expired due to SLA breach")
    total_carbon_emitted: float = Field(default=0.0, description="Estimated total carbon in kg CO2e")
    total_cost_usd: float = Field(default=0.0, description="Aggregate compute cost incurred")
    cumulative_reward: float = Field(default=0.0, description="Total normalized reward accumulated")


class GreengridAction(Action):
    """Action payload submitted by the scheduling agent."""
    message: str = Field(
        ...,
        description="Command directive in standard format: assign <job_id> to <datacenter_name>"
    )


class GreengridObservation(Observation):
    """Observation telemetry returned to the scheduling agent."""
    echoed_message: str = Field(
        default="",
        description="Formatted text rendering of current state for LLM reasoning"
    )
    message_length: int = Field(
        default=0,
        description="Character count of previous action command"
    )
    step: int = Field(default=0, description="Current episode step count")
    max_steps: int = Field(default=10, description="Maximum step budget for current task tier")
    datacenters: Optional[List[Dict]] = Field(
        default=None,
        description="Structured telemetry for all monitored data centers"
    )
    job_queue: Optional[List[Dict]] = Field(
        default=None,
        description="Active unassigned workloads in the scheduling queue"
    )
    metrics: Optional[Dict] = Field(
        default=None,
        description="Aggregate performance and sustainability metrics"
    )
    last_status: Optional[str] = Field(
        default="",
        description="Structured execution code of the previous step"
    )