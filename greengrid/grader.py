import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.greengrid_environment import GreengridEnvironment
from models import GreengridAction

MAX_POSSIBLE = {"easy": 5.0, "medium": 8.0, "hard": 10.0}

def greedy_action(env):
    if not env.job_queue:
        return "no-op"
    job = env.job_queue[0]
    available = [d for d in env.datacenters if d["online"]]
    if not available:
        return "no-op"
    best = min(available, key=lambda d: d["carbon_intensity"])
    return f"assign {job['job_id']} to {best['name']}"

def grade(task):
    env = GreengridEnvironment(task=task)
    env.reset()
    total = 0.0
    for _ in range(env.max_steps):
        action_str = greedy_action(env)
        if action_str == "no-op":
            break
        result = env.step(GreengridAction(message=action_str))
        total += result.reward
        if result.done:
            break
    score = round(min(max(total / MAX_POSSIBLE.get(task, 5.0), 0.0), 1.0), 4)
    return score

def run_all():
    print("GreenGrid Grader Results:")
    for task in ["easy", "medium", "hard"]:
        print(f"  {task:8s} → {grade(task):.4f}")
    print("Done!")

if __name__ == "__main__":
    run_all()