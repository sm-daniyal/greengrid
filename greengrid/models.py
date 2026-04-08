from openenv.core.env_server.types import Action, Observation
from pydantic import Field

class GreengridAction(Action):
    """Agent sends a job assignment command."""
    message: str = Field(..., description="Command: assign <job_id> to <datacenter>")

class GreengridObservation(Observation):
    """Current state of the data centers and job queue."""
    echoed_message: str = Field(default="", description="Current environment state as text")
    message_length: int = Field(default=0, description="Length of last message")