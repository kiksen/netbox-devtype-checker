from pathlib import Path

import yaml
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# NetBox REST API filter syntax; a list sends the parameter repeatedly (OR, or NOR with __n).
type FilterValue = str | int | bool | list[str | int]
type Filters = dict[str, FilterValue]


class Settings(BaseSettings):
    """NetBox credentials from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # NETBOX_API and NETBOX_URL are accepted interchangeably (NETBOX_API wins if both are set).
    netbox_api: str = Field(validation_alias=AliasChoices("netbox_api", "netbox_url"))
    netbox_token: SecretStr


class FilterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_types: Filters = Field(default_factory=dict)
    devices: Filters = Field(default_factory=dict)
    interface_filter: Filters = Field(default_factory=dict)


def load_filter(path: Path) -> FilterConfig:
    data = yaml.safe_load(path.read_text()) or {}
    return FilterConfig.model_validate(data)
