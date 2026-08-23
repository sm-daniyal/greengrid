"""
FastAPI application for the GreenGrid Environment & Infrastructure Console.

Exposes the OpenEnv WebSocket/HTTP interfaces, REST telemetry endpoints,
and the interactive web console.
"""

import os
import sys
from fastapi.responses import HTMLResponse, RedirectResponse

# Ensure root package is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv-core is required. Install with pip install -e .") from e

from models import GreengridAction, GreengridObservation
from server.greengrid_environment import GreengridEnvironment
from server.dashboard_html import DASHBOARD_HTML
from grid_data import GridTelemetryService
from dispatch import WorkloadDispatcher, DispatchRequest, DispatchDecision

# Create OpenEnv server app
app = create_app(
    GreengridEnvironment,
    GreengridAction,
    GreengridObservation,
    env_name="greengrid",
    max_concurrent_envs=4,
)

telemetry_service = GridTelemetryService()
dispatcher = WorkloadDispatcher()


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Serve the interactive GreenGrid Infrastructure Console."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/v1/grid-telemetry", tags=["Telemetry"])
def get_grid_telemetry(hour: float = 14.0):
    """Retrieve real-time carbon intensity and cost across all data center regions."""
    return telemetry_service.get_all_nodes_telemetry(hour_of_day=hour)


@app.post("/api/v1/dispatch", response_model=DispatchDecision, tags=["Dispatcher"])
def dispatch_workload(request: DispatchRequest):
    """Compute carbon-optimal workload routing for submitted compute jobs."""
    return dispatcher.route_workload(request)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for direct local execution."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)

    
    
