"""
GreenGrid Benchmark & Baseline Evaluation Suite.

Evaluates algorithmic scheduling heuristics across difficulty tiers
(Easy, Medium, Hard) to establish reference performance baselines.
"""

import os
import random
import sys
from typing import Callable, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import GreengridAction
from server.greengrid_environment import GreengridEnvironment

MAX_EXPECTED_REWARD = {"easy": 5.0, "medium": 8.0, "hard": 10.0}


def policy_random(env: GreengridEnvironment) -> str:
    """Stochastic baseline policy."""
    if not env.job_queue:
        return "no-op"
    job = env.job_queue[0]
    online_dcs = [d for d in env.datacenters if d["online"]]
    if not online_dcs:
        return "no-op"
    chosen = random.choice(online_dcs)
    return f"assign {job['job_id']} to {chosen['name']}"


def policy_greedy_carbon(env: GreengridEnvironment) -> str:
    """Greedy carbon minimization policy."""
    if not env.job_queue:
        return "no-op"
    job = env.job_queue[0]
    online_dcs = [d for d in env.datacenters if d["online"]]
    if not online_dcs:
        return "no-op"
    best = min(online_dcs, key=lambda d: d["carbon_intensity"])
    return f"assign {job['job_id']} to {best['name']}"


def policy_balanced_heuristic(env: GreengridEnvironment) -> str:
    """Multi-objective policy balancing carbon, load limits, and dollar costs."""
    if not env.job_queue:
        return "no-op"
    # Sort queue by deadline urgency
    sorted_queue = sorted(env.job_queue, key=lambda j: (j["deadline"], -j["compute_units"]))
    job = sorted_queue[0]

    online_dcs = [d for d in env.datacenters if d["online"]]
    if not online_dcs:
        return "no-op"

    def score_datacenter(d: Dict) -> float:
        # Lower is better
        load_penalty = 50.0 if d["server_load"] + job["compute_units"] > 85.0 else 0.0
        return d["carbon_intensity"] * 0.7 + (d["cost_per_hour"] * 1000.0) * 0.3 + load_penalty

    best = min(online_dcs, key=score_datacenter)
    return f"assign {job['job_id']} to {best['name']}"


def evaluate_policy(policy_fn: Callable[[GreengridEnvironment], str], task: str, seed: int = 42) -> Dict:
    """Run an evaluation episode for a given policy and task tier."""
    env = GreengridEnvironment(task=task, seed=seed)
    env.reset()
    total_reward = 0.0

    for _ in range(env.max_steps):
        action_str = policy_fn(env)
        if action_str == "no-op":
            break
        result = env.step(GreengridAction(message=action_str))
        total_reward += result.reward
        if result.done:
            break

    score = round(min(max(total_reward / MAX_EXPECTED_REWARD.get(task, 5.0), 0.0), 1.0), 4)
    metrics = env._get_metrics_dict()
    metrics["normalized_score"] = score
    return metrics


def run_benchmark_suite():
    """Execute evaluation across all policies and difficulty tiers."""
    policies = {
        "Random Baseline": policy_random,
        "Greedy Carbon Min": policy_greedy_carbon,
        "Balanced Heuristic": policy_balanced_heuristic,
    }
    tasks = ["easy", "medium", "hard"]

    print("=" * 80)
    print("GreenGrid Algorithmic Baseline Benchmark")
    print("=" * 80)
    print(f"{'Policy':<22} | {'Task':<8} | {'Score':<8} | {'Completed':<10} | {'Failed':<8} | {'Carbon (kg)':<12}")
    print("-" * 80)

    for pol_name, pol_fn in policies.items():
        for task in tasks:
            res = evaluate_policy(pol_fn, task)
            print(
                f"{pol_name:<22} | {task.capitalize():<8} | {res['normalized_score']:<8.4f} | "
                f"{res['jobs_completed']:<10} | {res['jobs_failed']:<8} | {res['total_carbon_emitted_kg']:<12.4f}"
            )
        print("-" * 80)


if __name__ == "__main__":
    run_benchmark_suite()