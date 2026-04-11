# 🌱 GreenGrid-v0: Carbon-Aware Data Center Job Scheduler


## What Is GreenGrid?

GreenGrid is a reinforcement learning environment where an AI agent learns to route computing jobs across global data centers — choosing locations with the lowest carbon intensity to reduce environmental impact.

This is a real problem. Every time you use Google, Meta, or any major tech platform, thousands of computing jobs are being routed across data centers around the world. Smart scheduling can dramatically reduce carbon emissions without sacrificing performance.

GreenGrid gives AI researchers a standardized environment to train and test agents that solve this problem.

---

## The Problem It Solves

Data centers consume about 1-2% of global electricity. At any moment:
- Oregon might be running on 80% solar (low carbon )(featured)
- Virginia might be running on coal (high carbon )
- Mumbai might be cheap but very carbon-heavy 

A smart agent learns to say:
> "Don't run this job in Virginia right now — send it to Oregon where solar energy is peaking."

---

## How It Works

The agent sees this every step:
=== GreenGrid [EASY] Step 3/10 ===
DATA CENTERS:
Oregon       carbon=118 gCO2/kWh  load= 45%  cost=$0.08/hr
Virginia     carbon=392 gCO2/kWh  load= 60%  cost=$0.06/hr
Singapore    carbon=461 gCO2/kWh  load= 35%  cost=$0.10/hr
Frankfurt    carbon=271 gCO2/kWh  load= 50%  cost=$0.09/hr
Mumbai       carbon=498 gCO2/kWh  load= 25%  cost=$0.05/hr
JOB QUEUE:
job_0_0   units= 5  deadline=4  priority=high
job_0_1   units= 3  deadline=6  priority=low
Stats: completed=2  failed=0  total_reward=0.84
ACTION FORMAT: assign <job_id> to <DatacenterName>
EXAMPLE:       assign job_0_0 to Oregon

The agent responds with:
assign job_0_0 to Oregon

And gets rewarded based on how smart that decision was.

---

## The 3 Tasks

### Task 1 — Easy: Carbon Minimizer
- **Goal:** Route jobs to the lowest carbon data center
- **Steps:** 10 per episode
- **What makes it easy:** No server failures, single objective
- **Baseline score:** 0.3892

### Task 2 — Medium: Cost + Carbon Balancer
- **Goal:** Balance carbon emissions AND running cost AND job deadlines
- **Steps:** 15 per episode
- **What makes it harder:** Three competing objectives to optimize simultaneously
- **Baseline score:** 0.4058

### Task 3 — Hard: Dynamic SLA Scheduler
- **Goal:** Route jobs with random server failures, carbon spikes, and priority jobs
- **Steps:** 20 per episode
- **What makes it hard:** Servers randomly go offline, carbon values spike unpredictably, high-priority jobs must not be missed
- **Baseline score:** 0.3394

---

## Reward Function

The agent receives feedback every single step — not just at the end:

| Situation | Reward |
|-----------|--------|
| Route to low carbon datacenter | up to +0.5 |
| Route cheaply (medium + hard) | up to +0.3 |
| Meet job deadline | +0.2 |
| Job expires / deadline missed | -0.2 |
| Send to offline server | -0.3 |
| Invalid command format | -0.2 |
| Overload a server (load > 80%) | -0.3 |

---

## Action Space

Text command in this exact format:
assign <job_id> to <DatacenterName>

Valid datacenter names:
- `Oregon`
- `Virginia`
- `Singapore`
- `Frankfurt`
- `Mumbai`

Example:
assign job_2_1 to Frankfurt

---

## Observation Space

Text description containing:
- Current step number and max steps
- All 5 data centers with carbon intensity (gCO2/kWh), server load (%), cost per hour
- Pending job queue with compute units, deadline countdown, priority level
- Running stats — completed jobs, failed jobs, total reward so far
- Result of last action taken

---

## Project Structure
greengrid/
├── models.py                      
├── server/
│   ├── init.py                # Package init
│   ├── app.py                     # FastAPI web server
│   └── greengrid_environment.py  
├── grader.py                      # Automated scoring (0.0 to 1.0)
├── inference.py                   # LLM agent baseline script
├── openenv.yaml                   
├── pyproject.toml                 # Project dependencies
└── README.md                      

---

## Setup and Usage

### Option 1 — Use Live HuggingFace Space (Easiest)

No setup needed! Just visit:
https://huggingface.co/spaces/smdaniyalhf/greengrid

Or send API requests directly:
```python
import httpx

# Reset environment
response = httpx.post("https://smdaniyalhf-greengrid.hf.space/reset")
print(response.json())

# Take a step
response = httpx.post(
    "https://smdaniyalhf-greengrid.hf.space/step",
    json={"message": "assign job_0_0 to Oregon"}
)
print(response.json())
```

### Option 2 — Run Locally

```bash
# Step 1 - Clone the repo
git clone https://huggingface.co/spaces/smdaniyalhf/greengrid
cd greengrid

# Step 2 - Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Step 3 - Install dependencies
pip install openenv-core uvicorn fastapi pydantic

# Step 4 - Start server
uv run server

# Step 5 - Open in browser
# http://127.0.0.1:8000/docs
```

### Option 3 - Run Grader

```bash
python grader.py
```

Expected output:
GreenGrid Grader Results:
easy     → 0.3892
medium   → 0.4058
hard     → 0.3394
Done!

### Option 4 - Run Inference Script

```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start new episode |
| `/step` | POST | Take an action |
| `/state` | GET | Get current state |
| `/docs` | GET | Interactive API docs |
| `/health` | GET | Check if server is running |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | HuggingFace router |
| `MODEL_NAME` | Model to use for inference | Qwen/Qwen2.5-72B-Instruct |
| `HF_TOKEN` | HuggingFace API token | Required for inference |

---

## Technical Stack

| Technology | Purpose |
|-----------|---------|
| OpenEnv | RL environment framework by Meta + HuggingFace |
| FastAPI | High performance Python web framework |
| Pydantic | Data validation and typed models |
| uvicorn | ASGI server for production |
| Docker | Containerized deployment |
| HuggingFace Spaces | cloud hosting |

---


GreenGrid provides a standardized, open-source RL environment so researchers can train and benchmark agents that tackle this challenge — contributing to a more sustainable internet.

---

## Data Centers

| Name     | Base Carbon | Cost/hr | Region       |
|------    |------------ |---------|------------- |
| Oregon   | 120 gCO2/kWh| $0.08   | US West      |
| Virginia | 380 gCO2/kWh| $0.06   | US East      |
| Singapore| 450 gCO2/kWh| $0.10   | Asia Pacific |
| Frankfurt| 280 gCO2/kWh| $0.09   | Europe       |
| Mumbai   | 500 gCO2/kWh| $0.05   | South Asia   |

Carbon values fluctuate each step simulating real-world renewable energy availability.

---

## Contributing

Contributions welcome! To improve this environment:

1. Fork the space on HuggingFace
2. Make your changes
3. Submit a pull request


*Built with ❤️ for the Meta x Scaler OpenEnv Hackathon 2026*
*Deployed on HuggingFace Spaces*
*Repo available on github too*
