"""
GreenGrid Inference Script
"""
import asyncio
import os
import textwrap
from typing import List, Optional
from openai import OpenAI

try:
    from greengrid.client import GreengridEnv
    from greengrid.models import GreengridAction
except ImportError:
    from client import GreengridEnv
    from models import GreengridAction

IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "greengrid:latest")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "dummy")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "greengrid-v0"
MAX_STEPS = 10
TEMPERATURE = 0.3
MAX_TOKENS = 50
SUCCESS_SCORE_THRESHOLD = 0.3
MAX_TOTAL_REWARD = 5.0

SYSTEM_PROMPT = textwrap.dedent("""
    You are a carbon-aware data center job scheduler.
    You see a list of data centers with carbon intensity values and a job queue.
    Your goal: assign jobs to data centers with the LOWEST carbon_intensity.
    Always pick the data center with lowest carbon that is NOT [OFFLINE].
    Reply with EXACTLY: assign <job_id> to <DatacenterName>
    Example: assign job_0_0 to Oregon
    Only one assignment per message. No explanation needed.
""").strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def get_action(client: OpenAI, obs: str, reward: float, history: List[str]) -> str:
    history_block = "\n".join(history[-3:]) if history else "None"
    user_prompt = textwrap.dedent(f"""
        Current state:
        {obs}
        Last reward: {reward:.2f}
        Recent history:
        {history_block}
        Your assignment command:
    """).strip()
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return text if text else "assign job_0_0 to Oregon"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "assign job_0_0 to Oregon"


async def run_task(task: str):
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    env = await GreengridEnv.from_docker_image(IMAGE_NAME)

    try:
        result = await env.reset()
        last_obs = result.observation.echoed_message
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            action_str = get_action(client, last_obs, last_reward, history)
            result = await env.step(GreengridAction(message=action_str))

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step
            last_obs = result.observation.echoed_message
            last_reward = reward

            log_step(step, action_str, reward, done, error)
            history.append(f"Step {step}: {action_str!r} -> {reward:+.2f}")

            if done:
                break

        score = min(max(sum(rewards) / MAX_TOTAL_REWARD, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success, steps_taken, score, rewards)

    return score


async def main():
    for task in ["easy", "medium", "hard"]:
        print(f"\n[DEBUG] Running task: {task}", flush=True)
        score = await run_task(task)
        print(f"[DEBUG] {task} final score: {score:.4f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())