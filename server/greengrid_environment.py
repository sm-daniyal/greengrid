"""
GreenGrid Environment Server Implementation.

Simulates dynamic multi-region data center workload scheduling with real-time
carbon intensity fluctuations, compute capacity limits, operating cost constraints,
and SLA deadline enforcement.
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from models import GreengridAction, GreengridObservation
except ImportError:
    from ..models import GreengridAction, GreengridObservation

DATA_CENTERS_TOPOLOGY = [
    {"name": "Oregon",    "base_carbon": 120.0, "cost": 0.08, "capacity": 100.0},
    {"name": "Virginia",  "base_carbon": 380.0, "cost": 0.06, "capacity": 120.0},
    {"name": "Singapore", "base_carbon": 450.0, "cost": 0.10, "capacity": 90.0},
    {"name": "Frankfurt", "base_carbon": 280.0, "cost": 0.09, "capacity": 110.0},
    {"name": "Mumbai",    "base_carbon": 500.0, "cost": 0.05, "capacity": 130.0},
]


class GreengridEnvironment(Environment):
    """
    Carbon-Aware Multi-Datacenter Job Scheduling Environment.

    The agent coordinates compute workloads across geo-distributed data centers
    to minimize aggregate grid carbon footprint while satisfying latency,
    capacity, and SLA deadline constraints.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, task: str = "easy", seed: int = 42):
        self.task = task
        self.seed = seed
        self.rng = random.Random(self.seed)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._setup()

    def _setup(self):
        self.max_steps = {"easy": 10, "medium": 15, "hard": 20}.get(self.task, 10)
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_reward = 0.0
        self.total_carbon_emitted = 0.0
        self.total_cost_usd = 0.0

        self.datacenters: List[Dict] = [
            {
                "name": dc["name"],
                "carbon_intensity": round(dc["base_carbon"] + self.rng.uniform(-15.0, 15.0), 1),
                "server_load": round(self.rng.uniform(20.0, 50.0), 1),
                "cost_per_hour": dc["cost"],
                "capacity": dc["capacity"],
                "online": True,
            }
            for dc in DATA_CENTERS_TOPOLOGY
        ]
        self.job_queue: List[Dict] = self._generate_workloads(3)

    def reset(self) -> GreengridObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.rng = random.Random(self.seed)
        self._setup()
        obs_text = self._build_obs_text()
        return GreengridObservation(
            echoed_message=obs_text,
            message_length=0,
            step=0,
            max_steps=self.max_steps,
            datacenters=[dict(d) for d in self.datacenters],
            job_queue=[dict(j) for j in self.job_queue],
            metrics=self._get_metrics_dict(),
            last_status="[INIT] Environment initialized",
            done=False,
            reward=0.0,
        )

    def step(self, action: GreengridAction) -> GreengridObservation:
        self._state.step_count += 1
        raw_command = (action.message or "").strip()
        step_reward = 0.0
        status_code = ""

        job_id, dc_name = self._parse_directive(raw_command)

        if job_id is None or dc_name is None:
            step_reward = -0.2
            status_code = "[INVALID_SYNTAX] Format required: assign <job_id> to <DatacenterName>"
        else:
            job = next((j for j in self.job_queue if j["job_id"] == job_id), None)
            dc = next((d for d in self.datacenters if d["name"].lower() == dc_name.lower()), None)

            if job is None:
                step_reward = -0.2
                status_code = f"[JOB_NOT_FOUND] Job identifier '{job_id}' is not in active queue"
            elif dc is None:
                step_reward = -0.2
                status_code = f"[DATACENTER_NOT_FOUND] Datacenter identifier '{dc_name}' is unmapped"
            elif not dc["online"]:
                step_reward = -0.3
                status_code = f"[DATACENTER_OFFLINE] Datacenter '{dc['name']}' is offline"
            elif dc["server_load"] + job["compute_units"] > 100.0 and self.task == "hard":
                step_reward = -0.25
                status_code = f"[CAPACITY_EXCEEDED] Allocation exceeds 100% capacity on '{dc['name']}'"
            else:
                step_reward = self._compute_reward(job, dc)
                self.job_queue.remove(job)
                self.jobs_completed += 1

                # Track physical carbon and compute cost
                carbon_g = (dc["carbon_intensity"] * job["compute_units"] * 0.1)
                cost_usd = (dc["cost_per_hour"] * job["compute_units"] * 0.05)
                self.total_carbon_emitted += carbon_g / 1000.0  # convert to kg
                self.total_cost_usd += cost_usd

                dc["server_load"] = min(100.0, dc["server_load"] + job["compute_units"])
                status_code = f"[SUCCESS] Allocated {job_id} -> {dc['name']} (reward={step_reward:.3f})"

        self.total_reward += step_reward
        self._evolve_environment()

        # Inflow of new compute workloads
        if self._state.step_count % 2 == 0 and len(self.job_queue) < 5:
            self.job_queue += self._generate_workloads(1)

        # Decay deadlines and check SLA breaches
        for j in self.job_queue:
            j["deadline"] -= 1

        expired_workloads = [j for j in self.job_queue if j["deadline"] <= 0]
        for j in expired_workloads:
            self.job_queue.remove(j)
            self.jobs_failed += 1
            step_reward -= 0.25

        done = self._state.step_count >= self.max_steps
        obs_text = self._build_obs_text(status_code)

        return GreengridObservation(
            echoed_message=obs_text,
            message_length=len(raw_command),
            step=self._state.step_count,
            max_steps=self.max_steps,
            datacenters=[dict(d) for d in self.datacenters],
            job_queue=[dict(j) for j in self.job_queue],
            metrics=self._get_metrics_dict(),
            last_status=status_code,
            done=done,
            reward=round(step_reward, 4),
        )

    @property
    def state(self) -> State:
        return self._state

    def _parse_directive(self, msg: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            msg_lower = msg.lower()
            if "assign" in msg_lower and " to " in msg_lower:
                parts = msg_lower.split("assign")[1].split(" to ")
                job_id = parts[0].strip()
                dc = parts[1].strip()
                for d in self.datacenters:
                    if d["name"].lower() == dc:
                        return job_id, d["name"]
                return job_id, dc
        except Exception:
            pass
        return None, None

    def _compute_reward(self, job: Dict, dc: Dict) -> float:
        online_dcs = [d for d in self.datacenters if d["online"]]
        if not online_dcs:
            return 0.0

        max_carbon = max(d["carbon_intensity"] for d in online_dcs)
        min_carbon = min(d["carbon_intensity"] for d in online_dcs)

        # Carbon minimization term
        if max_carbon > min_carbon:
            carbon_score = (max_carbon - dc["carbon_intensity"]) / (max_carbon - min_carbon)
        else:
            carbon_score = 1.0

        reward = carbon_score * 0.55

        # Task-specific cost and SLA terms
        if self.task in ("medium", "hard"):
            max_cost = max(d["cost_per_hour"] for d in self.datacenters)
            cost_efficiency = (max_cost - dc["cost_per_hour"]) / max_cost
            reward += cost_efficiency * 0.25
            reward += 0.15 if job["deadline"] >= 2 else 0.05

        if self.task == "hard":
            if dc["server_load"] > 80.0:
                reward -= 0.20
            reward += {"low": 0.0, "medium": 0.05, "high": 0.10}.get(job["priority"], 0.0)

        return round(max(0.0, reward), 4)

    def _evolve_environment(self):
        step = self._state.step_count
        for dc in self.datacenters:
            # Diurnal pseudo-variance + stochastic shift
            diurnal_shift = 10.0 * math.sin((step / self.max_steps) * 2 * math.pi)
            stochastic_noise = self.rng.uniform(-10.0, 10.0)
            dc["carbon_intensity"] = round(
                max(40.0, min(650.0, dc["carbon_intensity"] + diurnal_shift + stochastic_noise)), 1
            )
            # Service workload completions
            dc["server_load"] = round(
                max(10.0, dc["server_load"] - self.rng.uniform(3.0, 9.0)), 1
            )
            if self.task == "hard":
                if self.rng.random() < 0.04:
                    dc["online"] = False
                elif not dc["online"] and self.rng.random() < 0.35:
                    dc["online"] = True

    def _generate_workloads(self, count: int) -> List[Dict]:
        jobs = []
        for i in range(count):
            p = self.rng.choice(["low", "medium", "high"])
            jobs.append({
                "job_id": f"job_{self._state.step_count}_{i}",
                "compute_units": self.rng.randint(2, 12),
                "deadline": self.rng.randint(3, 7),
                "priority": p,
            })
        return jobs

    def _get_metrics_dict(self) -> Dict:
        return {
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "total_carbon_emitted_kg": round(self.total_carbon_emitted, 4),
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cumulative_reward": round(self.total_reward, 4),
        }

    def _build_obs_text(self, status_line: str = "") -> str:
        step = self._state.step_count
        dc_lines = "\n".join(
            f"  {d['name']:12s} carbon={d['carbon_intensity']:5.1f} gCO2/kWh "
            f"load={d['server_load']:5.1f}% cost=${d['cost_per_hour']:.2f}/hr"
            f"{' [OFFLINE]' if not d['online'] else ''}"
            for d in self.datacenters
        )
        job_lines = "\n".join(
            f"  {j['job_id']:15s} units={j['compute_units']:2d} "
            f"deadline={j['deadline']:2d} priority={j['priority']}"
            for j in self.job_queue
        ) or "  [QUEUE_EMPTY]"

        header = f"=== GreenGrid Infrastructure Simulation [{self.task.upper()}] Step {step}/{self.max_steps} ==="
        body = (
            f"{header}\n\n"
            f"REGIONAL DATA CENTERS:\n{dc_lines}\n\n"
            f"ACTIVE WORKLOAD QUEUE:\n{job_lines}\n\n"
            f"TELEMETRY SUMMARY:\n"
            f"  Completed: {self.jobs_completed} | Failed: {self.jobs_failed} | "
            f"Carbon: {self.total_carbon_emitted:.3f} kg | Cost: ${self.total_cost_usd:.2f} | "
            f"Reward: {self.total_reward:.3f}\n"
        )
        if status_line:
            body += f"\nEXECUTION STATUS: {status_line}\n"

        body += (
            f"\nDIRECTIVE SYNTAX: assign <job_id> to <DatacenterName>\n"
            f"AVAILABLE REGIONS: Oregon, Virginia, Singapore, Frankfurt, Mumbai"
        )
        return body