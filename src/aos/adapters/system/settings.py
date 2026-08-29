"""Configuration: a TOML file on disk, overridable by AOS_ environment variables.

The assistant's name lives here as configuration and nowhere in source (AD-9).
Secrets are deliberately absent — those come from the credential store.
"""

from __future__ import annotations

from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from aos.common import paths

Environment = Literal["dev", "live"]


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_file: bool = True


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8420

    @field_validator("host")
    @classmethod
    def loopback_only(cls, value: str) -> str:
        """AD-5: the local host never accepts an inbound connection."""
        if value not in {"127.0.0.1", "localhost", "::1"}:
            msg = f"server.host must be loopback, got {value!r} (AD-5)"
            raise ValueError(msg)
        return value


class TelegramSettings(BaseModel):
    enabled: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AOS_",
        env_nested_delimiter="__",
        toml_file=paths.config_file(),
        extra="ignore",
    )

    # Neutral fallback only. The real default ships in config.example.toml so that
    # no source file contains the name.
    agent_name: str = "Assistant"
    environment: Environment = "dev"
    timezone: str = "UTC"

    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)

    @field_validator("timezone")
    @classmethod
    def known_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            # ZoneInfoNotFoundError subclasses KeyError, which pydantic will not wrap,
            # so a bad zone would otherwise crash raw instead of reporting as config.
            msg = f"unknown timezone {value!r}"
            raise ValueError(msg) from exc
        return value

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def is_live(self) -> bool:
        return self.environment == "live"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Environment wins over the file, so a service definition can override
        # without editing machine state.
        return (init_settings, env_settings, TomlConfigSettingsSource(settings_cls))


def load_settings() -> Settings:
    return Settings()
