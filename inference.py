"""
GreenGrid LLM Agent Evaluation and Inference Harness.

Connects open-weights or proprietary LLM agents to the GreenGrid environment
via the OpenAI-compatible endpoint, evaluating decision quality against carbon-aware
workload scheduling benchmarks.
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
TEMPERATURE = 0.2
MAX_TOKENS = 64
SUCCESS_SCORE_THRESHOLD = 0.35
MAX_TOTAL_REWARD = 5.0

SYSTEM_PROMPT = textwrap.dedent("""
    You are an automated carbon-aware infrastructure controller.
    Your objective is to schedule batch compute jobs onto regional data centers to minimize grid carbon emissions and operating costs while adhering to SLA deadlines.

    Operational Directives:
    1. Select data centers with the LOWEST instantaneous carbon_intensity that are marked ONLINE.
    2. Respect server capacity; avoid assigning heavy compute units to data centers exceeding 80% server_load.
    3. Output EXACTLY one directive command in this format:
       assign <job_id> to <DatacenterName>
    4. Example output: assign job_0_0 to Oregon
    5. Do not output explanations or conversational filler.
""").strip()


def log_start(task: str, env_name: str, model: str) -> None:
    print(f"[START] task={task} benchmark={env_name} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "none"
    print(f"[STEP] step={step:02d} action={action!r} reward={reward:+.3f} done={str(done).lower()} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:+.2f}" for r in rewards)
    status_label = "PASSED" if success else "FAILED"
    print(f"[EVAL] status={status_label} steps={steps} score={score:.4f} rewards=[{rewards_str}]", flush=True)


def get_action(client: OpenAI, obs: str, reward: float, history: List[str]) -> str:
    history_block = "\n".join(history[-3:]) if history else "none"
    user_prompt = textwrap.dedent(f"""
        CURRENT INFRASTRUCTURE TELEMETRY:
        {obs}

        LAST STEP REWARD: {reward:+.3f}
        RECENT DIRECTIVES:
        {history_block}

        ISSUE NEXT DIRECTIVE:
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
        print(f"[WARN] Inference request failed: {exc}", flush=True)
        return "assign job_0_0 to Oregon"


async def run_task(task: str) -> float:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task, env_name=BENCHMARK, model=MODEL_NAME)
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

            rewards.append(reward)
            steps_taken = step
            last_obs = result.observation.echoed_message
            last_reward = reward

            log_step(step, action_str, reward, done, None)
            history.append(f"Step {step}: {action_str} -> {reward:+.2f}")

            if done:
                break

        score = min(max(sum(rewards) / MAX_TOTAL_REWARD, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[WARN] Client close exception: {e}", flush=True)
        log_end(success, steps_taken, score, rewards)

    return score


async def main():
    print("=" * 80)
    print("GreenGrid LLM Agent Evaluation Session")
    print("=" * 80)
    for task in ["easy", "medium", "hard"]:
        score = await run_task(task)
        print(f"[RESULT] Task '{task}': Normalized Score = {score:.4f}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())