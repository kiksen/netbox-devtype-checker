from pathlib import Path

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

type FilterValue = str | int | bool


class Settings(BaseSettings):
    """NetBox credentials from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    netbox_api: str
    netbox_token: SecretStr


class FilterConfig(BaseModel):
    device_types: dict[str, FilterValue] = Field(default_factory=dict)
    devices: dict[str, FilterValue] = Field(default_factory=dict)
    interface_filter: list[str] = Field(default_factory=list)


def load_filter(path: Path) -> FilterConfig:
    data = yaml.safe_load(path.read_text()) or {}
    return FilterConfig.model_validate(data)
