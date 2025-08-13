import os
from typing import Any, Dict

from dotenv import dotenv_values
from pydantic import BaseModel


class SettingsConfigDict(dict):
    """Minimal placeholder for settings configuration."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class BaseSettings(BaseModel):
    """Simplified replacement for pydantic-settings BaseSettings."""

    model_config = SettingsConfigDict()

    def __init__(self, **data: Any) -> None:
        env: Dict[str, Any] = {}
        env_file = self.model_config.get("env_file")
        if env_file:
            env.update(dotenv_values(env_file, encoding=self.model_config.get("env_file_encoding", "utf-8")))
        env.update(os.environ)
        env.update(data)
        super().__init__(**env)
