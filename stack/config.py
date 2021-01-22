"""STACK Configs."""

from typing import Dict, List, Optional

import pydantic


class StackSettings(pydantic.BaseSettings):
    """Application settings"""

    name: str = "titiler-mvt"
    stage: str = "production"

    owner: Optional[str]
    client: Optional[str]
    project: Optional[str]

    additional_env: Dict = {}

    timeout: int = 30
    memory: int = 3009

    # The maximum of concurrent executions you want to reserve for the function.
    # Default: - No specific limit - account limit.
    max_concurrent: Optional[int]

    buckets: List = ["*"]

    class Config:
        """model config"""

        env_file = "stack/.env"
        env_prefix = "STACK_"
