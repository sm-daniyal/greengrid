# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Greengrid Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

import random
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from models import GreengridAction, GreengridObservation
except ImportError:
    from models import GreengridAction, GreengridObservation

DATA_CENTERS = [
    {"name": "Oregon",    "base_carbon": 120, "cost": 0.08},
    {"name": "Virginia",  "base_carbon": 380, "cost": 0.06},
    {"name": "Singapore", "base_carbon": 450, "cost": 0.10},
    {"name": "Frankfurt", "base_carbon": 280, "cost": 0.09},
    {"name": "Mumbai",    "base_carbon": 500, "cost": 0.05},
]

class GreengridEnvironment(Environment):
    """
    GreenGrid: Carbon-Aware Data Center Job Scheduler.
    Agent routes compute jobs to minimize carbon emissions.
    """
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, task: str = "easy"):
        self.task = task
        self.rng = random.Random(42)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._setup()

    def _setup(self):
        self.max_steps = {"easy": 10, "medium": 15, "hard": 20}[self.task]
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.total_reward = 0.0
        self.datacenters = [
            {
                "name": dc["name"],
                "carbon_intensity": round(dc["base_carbon"] + self.rng.uniform(-20, 20), 1),
                "server_load": round(self.rng.uniform(20, 60), 1),
                "cost_per_hour": dc["cost"],
                "online": True,
            }
            for dc in DATA_CENTERS
        ]
        self.job_queue = self._new_jobs(3)

    def reset(self) -> GreengridObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.rng = random.Random(42)
        self._setup()
        obs_text = self._build_obs_text()
        return GreengridObservation(
            echoed_message=obs_text,
            message_length=0,
            done=False,
            reward=0.0,
        )

    def step(self, action: GreengridAction) -> GreengridObservation:
        self._state.step_count += 1
        msg = action.message.strip()
        reward = 0.0
        info_line = ""

        job_id, dc_name = self._parse(msg)

        if job_id is None:
            reward = -0.2
            info_line = "❌ Invalid format. Use: assign <job_id> to <DatacenterName>"
        else:
            job = next((j for j in self.job_queue if j["job_id"] == job_id), None)
            dc = next((d for d in self.datacenters
                      if d["name"].lower() == dc_name.lower()), None)

            if job is None:
                reward = -0.2
                info_line = f"❌ Job '{job_id}' not found"
            elif dc is None:
                reward = -0.2
                info_line = f"❌ Datacenter '{dc_name}' not found"
            elif not dc["online"]:
                reward = -0.3
                info_line = f"❌ {dc_name} is OFFLINE"
            else:
                reward = self._compute_reward(job, dc)
                self.job_queue.remove(job)
                self.jobs_completed += 1
                dc["server_load"] = min(100, dc["server_load"] + job["compute_units"])
                info_line = f"✅ Assigned {job_id} to {dc['name']} | reward={reward:.2f}"

        self.total_reward += reward
        self._evolve()

        if self._state.step_count % 2 == 0 and len(self.job_queue) < 5:
            self.job_queue += self._new_jobs(1)

        for j in self.job_queue:
            j["deadline"] -= 1
        expired = [j for j in self.job_queue if j["deadline"] <= 0]
        for j in expired:
            self.job_queue.remove(j)
            self.jobs_failed += 1
            reward -= 0.2

        done = self._state.step_count >= self.max_steps

        obs_text = self._build_obs_text(info_line)
        return GreengridObservation(
            echoed_message=obs_text,
            message_length=len(msg),
            done=done,
            reward=round(reward, 4),
        )

    @property
    def state(self) -> State:
        return self._state

    def _parse(self, msg: str):
        try:
            msg_lower = msg.lower()
            if "assign" in msg_lower and " to " in msg_lower:
                parts = msg_lower.split("assign")[1].split(" to ")
                job_id = parts[0].strip()
                dc = parts[1].strip()
                # match original case dc name
                for d in self.datacenters:
                    if d["name"].lower() == dc:
                        return job_id, d["name"]
                return job_id, dc
        except Exception:
            pass
        return None, None

    def _compute_reward(self, job, dc):
        max_c = max(d["carbon_intensity"] for d in self.datacenters if d["online"])
        carbon_ratio = (max_c - dc["carbon_intensity"]) / max_c
        reward = carbon_ratio * 0.5

        if self.task in ("medium", "hard"):
            max_cost = max(d["cost_per_hour"] for d in self.datacenters)
            reward += ((max_cost - dc["cost_per_hour"]) / max_cost) * 0.3
            reward += 0.2 if job["deadline"] > 2 else 0.05

        if self.task == "hard":
            if dc["server_load"] > 80:
                reward -= 0.3
            reward += {"low": 0.0, "medium": 0.1, "high": 0.2}[job["priority"]]

        return round(max(0.0, reward), 4)

    def _evolve(self):
        for dc in self.datacenters:
            dc["carbon_intensity"] = max(50, min(600,
                dc["carbon_intensity"] + self.rng.uniform(-15, 15)))
            dc["server_load"] = max(0, dc["server_load"] - self.rng.uniform(2, 8))
            if self.task == "hard":
                if self.rng.random() < 0.05:
                    dc["online"] = False
                elif not dc["online"] and self.rng.random() < 0.3:
                    dc["online"] = True

    def _new_jobs(self, n: int):
        jobs = []
        for i in range(n):
            p = self.rng.choice(["low", "medium", "high"])
            jobs.append({
                "job_id": f"job_{self._state.step_count}_{i}",
                "compute_units": self.rng.randint(1, 10),
                "deadline": self.rng.randint(3, 7),
                "priority": p,
            })
        return jobs

    def _build_obs_text(self, info: str = "") -> str:
        step = self._state.step_count
        dc_lines = "\n".join(
            f"  {d['name']:12s} carbon={d['carbon_intensity']:5.0f} gCO2/kWh "
            f"load={d['server_load']:4.0f}% cost=${d['cost_per_hour']}/hr"
            f"{' [OFFLINE]' if not d['online'] else ''}"
            for d in self.datacenters
        )
        job_lines = "\n".join(
            f"  {j['job_id']:15s} units={j['compute_units']:2d} "
            f"deadline={j['deadline']} priority={j['priority']}"
            for j in self.job_queue
        ) or "  (no pending jobs)"

        text = (
            f"=== GreenGrid [{self.task.upper()}] Step {step}/{self.max_steps} ===\n\n"
            f"DATA CENTERS:\n{dc_lines}\n\n"
            f"JOB QUEUE:\n{job_lines}\n\n"
            f"Stats: completed={self.jobs_completed} failed={self.jobs_failed} "
            f"total_reward={self.total_reward:.2f}\n"
        )
        if info:
            text += f"\nLast action: {info}\n"
        text += (
            f"\nACTION FORMAT: assign <job_id> to <DatacenterName>\n"
            f"EXAMPLE: assign job_0_0 to Oregon\n"
            f"DATACENTERS: Oregon, Virginia, Singapore, Frankfurt, Mumbai"
        )
        return text