---
title: GreenGrid Infrastructure Benchmark
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - sustainability
  - reinforcement-learning
  - carbon-aware-computing
  - agent-benchmarks
---

# GreenGrid: Carbon-Aware Compute Workload Scheduling Benchmark

[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Live%20Console-blue?logo=huggingface)](https://huggingface.co/spaces/smdaniyalhf/greengrid)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-black?logo=github)](https://github.com/sm-daniyal/greengrid)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-green.svg)](LICENSE)

**[Live Interactive Console](https://huggingface.co/spaces/smdaniyalhf/greengrid)** | **[API Documentation](https://huggingface.co/spaces/smdaniyalhf/greengrid/docs)** | **[GitHub Repository](https://github.com/sm-daniyal/greengrid)**

GreenGrid is an open-source evaluation benchmark and simulation environment for autonomous AI agents and reinforcement learning policies tasked with dynamic, carbon-aware data center compute scheduling.

The environment simulates geo-distributed data centers subject to real-time grid carbon intensity fluctuations, capacity constraints, operating cost variations, and strict workload SLA deadlines.

---

## Key Highlights

- **Dynamic Grid Emissions Simulation**: Real-time modeling of regional carbon intensity profiles (gCO2/kWh) combining diurnal solar/wind generation curves with stochastic volatility across five global regions.
- **Multi-Objective Optimization**: Evaluates agent capability in minimizing carbon footprint while balancing operating expenditures ($/hour), server load thresholds, and SLA breach penalties.
- **OpenEnv & Gymnasium Compatible**: Built on the OpenEnv protocol, supporting persistent low-latency WebSocket connections and standard HTTP/REST endpoints.
- **Standardized Baseline Suite**: Includes algorithmic reference policies (Random, Greedy Carbon Minimization, Balanced Multi-Objective) alongside open-weights LLM evaluations.

---

## System Architecture & Topology

![GreenGrid System Architecture](https://raw.githubusercontent.com/sm-daniyal/greengrid/main/assets/architecture.png)

---

## Mathematical Formulation

At step $t$, for an incoming compute workload $j$ assigned to data center $d \in \mathcal{D}_{\text{online}}$, the environment calculates step reward $R_t$:

$$R_t = \alpha \cdot \left(\frac{C_{\max}(t) - C_d(t)}{C_{\max}(t) - C_{\min}(t)}\right) + \beta \cdot \left(\frac{\text{Cost}_{\max} - \text{Cost}_d}{\text{Cost}_{\max}}\right) - \gamma \cdot \mathbb{I}(\text{Load}_d > 80\%) - \lambda \cdot N_{\text{expired}}$$

Where:
- $C_d(t)$: Instantaneous carbon intensity of data center $d$ at step $t$ in $\text{gCO}_2/\text{kWh}$.
- $\alpha = 0.55$: Weighting coefficient for carbon minimization.
- $\beta = 0.25$: Weighting coefficient for cost optimization.
- $\gamma = 0.20$: Overload capacity threshold penalty.
- $\lambda = 0.25$: SLA deadline expiration penalty per unserviced workload.

---

## Benchmark Results

Evaluation across $N=100$ simulation episodes comparing algorithmic heuristics and open-weights reasoning models:

| Policy / Model | Difficulty | Normalized Score | Workload Completion Rate | Avg Carbon Emitted (kg CO2e) | Carbon Reduction vs Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Baseline** | Easy | 0.1589 | 100% | 1.5915 | 0.0% (Ref) |
| **Random Baseline** | Medium | 0.3418 | 100% | 1.1013 | 0.0% (Ref) |
| **Random Baseline** | Hard | 0.1946 | 100% | 1.3282 | 0.0% (Ref) |
| **Greedy Carbon Min** | Easy | 0.5500 | 100% | 0.4816 | **69.7%** |
| **Greedy Carbon Min** | Medium | 0.4688 | 100% | 0.4719 | **57.1%** |
| **Greedy Carbon Min** | Hard | 0.3850 | 100% | 0.4179 | **68.5%** |
| **Balanced Heuristic**| Easy | 0.5500 | 100% | 0.4770 | **70.0%** |
| **Balanced Heuristic**| Medium | 0.4688 | 100% | 0.4707 | **57.3%** |
| **Balanced Heuristic**| Hard | 0.3850 | 100% | 0.4158 | **68.7%** |

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sm-daniyal/greengrid.git
cd greengrid

# Install dependencies in an isolated virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -e .
```

### Running the Python Client

```python
from greengrid.client import GreengridEnv
from greengrid.models import GreengridAction

# Connect to local or remote GreenGrid instance
with GreengridEnv(base_url="http://localhost:8000") as client:
    # Reset environment to initial state
    result = client.reset()
    print(result.observation.echoed_message)

    # Submit carbon-optimized workload allocation
    action = GreengridAction(message="assign job_0_0 to Oregon")
    step_result = client.step(action)

    print("Status:", step_result.observation.last_status)
    print("Step Reward:", step_result.reward)
    print("Telemetry Metrics:", step_result.observation.metrics)
```

### Running the Workload Dispatcher CLI

```bash
# View real-time regional grid carbon metrics
python dispatch.py status

# Compute carbon-optimal routing for an AI training or batch job
python dispatch.py dispatch --job-id "finetune-qwen" --compute-units 16 --deadline 4
```

### Running Algorithmic Baselines

```bash
python grader.py
```

### Running LLM Agent Inference

```bash
export HF_TOKEN="your_huggingface_token"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
python inference.py
```

### Interactive Web Dashboard

Launch the local server to access the live web console and REST API:

```bash
python -m server.app
```

- **Interactive Dashboard**: `http://localhost:8000/dashboard`
- **Swagger REST API**: `http://localhost:8000/docs`
- **OpenEnv Client**: `http://localhost:8000/web`

---

## Project Structure

```
greengrid/
├── client.py              # Strongly-typed OpenEnv client SDK
├── dispatch.py            # Production CLI workload dispatcher
├── grader.py              # Algorithmic benchmark baseline suite
├── grid_data.py           # Real regional grid telemetry & emission factors
├── inference.py           # LLM agent evaluation harness
├── models.py              # Pydantic v2 schemas for actions, observations, and telemetry
├── openenv.yaml           # OpenEnv manifest configuration
├── pyproject.toml         # Package specification and dependencies
├── server/
│   ├── app.py             # FastAPI server (HTTP, WebSocket, and REST endpoints)
│   ├── dashboard_html.py  # Interactive dark-themed web console
│   ├── Dockerfile         # Production container definition
│   └── greengrid_environment.py  # Core simulation engine and reward mechanics
└── README.md              # Technical specification and documentation
```

---

## Supported Deployment Targets

GreenGrid is packaged as a standard OCI container and can be deployed across multiple environments:

- **Hugging Face Spaces**: Live on Docker CPU basic tier ([Live Space](https://huggingface.co/spaces/smdaniyalhf/greengrid))
- **Render / Railway / Fly.io**: One-click deployment directly from the GitHub repository using the included `Dockerfile`.
- **AWS ECS / GCP Cloud Run**: Production cloud container runtime for high-throughput enterprise scheduling pipelines.

---

## License

This project is licensed under the BSD-style license.

