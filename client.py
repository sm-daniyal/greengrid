"""
GreenGrid Environment Client SDK.

Provides synchronous and asynchronous interfaces for AI agents to interact with
the GreenGrid carbon-aware data center scheduling environment over WebSockets/HTTP.
"""

from typing import Dict
from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import GreengridAction, GreengridObservation


class GreengridEnv(
    EnvClient[GreengridAction, GreengridObservation, State]
):
    """
    Client for interacting with the GreenGrid Infrastructure Simulation.

    Maintains a persistent session over WebSocket/HTTP with the environment
    server, providing low-latency execution of compute job routing actions.

    Example:
        >>> with GreengridEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.echoed_message)
        ...     action = GreengridAction(message="assign job_0_0 to Oregon")
        ...     result = client.step(action)
        ...     print(result.observation.last_status)
    """

    def _step_payload(self, action: GreengridAction) -> Dict:
        """
        Serialize GreengridAction to standard JSON payload.

        Args:
            action: GreengridAction instance containing scheduling directive.

        Returns:
            Dictionary payload for server ingestion.
        """
        return {
            "message": action.message,
        }

    def _parse_result(self, payload: Dict) -> StepResult[GreengridObservation]:
        """
        Parse server response into a typed StepResult containing GreengridObservation.

        Args:
            payload: JSON response data from server.

        Returns:
            StepResult wrapping the parsed GreengridObservation.
        """
        obs_data = payload.get("observation", {})
        observation = GreengridObservation(
            echoed_message=obs_data.get("echoed_message", ""),
            message_length=obs_data.get("message_length", 0),
            step=obs_data.get("step", 0),
            max_steps=obs_data.get("max_steps", 10),
            datacenters=obs_data.get("datacenters"),
            job_queue=obs_data.get("job_queue"),
            metrics=obs_data.get("metrics"),
            last_status=obs_data.get("last_status", ""),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request.

        Returns:
            State object with episode_id and step_count.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )

