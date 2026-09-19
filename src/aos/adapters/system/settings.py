"""Configuration: a TOML file on disk, overridable by AOS_ environment variables.

The assistant's name lives here as configuration and nowhere in source (AD-9).
Secrets are deliberately absent — those come from the credential store.
"""

from __future__ import annotations

from datetime import date, time, timedelta
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
from aos.domain.finance.money import Money
from aos.domain.notification.policy import NotificationPolicy, TimeWindow

Environment = Literal["dev", "live"]


class LoggingSettings(BaseModel):
    level: str = "INFO"
    json_file: bool = True


class NotificationSettings(BaseModel):
    daily_budget: int = Field(default=12, ge=1)
    quiet_hours: str = ""
    blackouts: list[str] = Field(default_factory=list)

    def as_policy(self) -> NotificationPolicy:
        return NotificationPolicy(
            daily_budget=self.daily_budget,
            quiet_hours=TimeWindow.parse(self.quiet_hours) if self.quiet_hours else None,
            blackouts=tuple(TimeWindow.parse(w) for w in self.blackouts),
        )

    @field_validator("quiet_hours")
    @classmethod
    def parseable_window(cls, value: str) -> str:
        if value:
            TimeWindow.parse(value)  # fail at startup, not at 06:00
        return value

    @field_validator("blackouts")
    @classmethod
    def parseable_windows(cls, value: list[str]) -> list[str]:
        for window in value:
            TimeWindow.parse(window)
        return value


class GoalSettings(BaseModel):
    """The headline target, as configuration. Nothing in source names it."""

    target: str = ""
    start: str = ""
    deadline: str = ""

    @property
    def target_money(self) -> Money | None:
        return Money.of(self.target) if self.target else None

    @property
    def start_date(self) -> date:
        return date.fromisoformat(self.start) if self.start else date.today()

    @property
    def deadline_date(self) -> date:
        if self.deadline:
            return date.fromisoformat(self.deadline)
        return self.start_date + timedelta(days=180)


class ContentSettings(BaseModel):
    check_at: str = "10:00"
    horizon_days: int = Field(default=2, ge=1)

    @property
    def check_time(self) -> time:
        return time.fromisoformat(self.check_at)

    @field_validator("check_at")
    @classmethod
    def parseable_time(cls, value: str) -> str:
        try:
            time.fromisoformat(value)
        except ValueError as exc:
            msg = f"expected a time like '10:00', got {value!r}"
            raise ValueError(msg) from exc
        return value


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
    chat_id: str = ""

    @property
    def usable(self) -> bool:
        """Enabled is an intent; usable is whether it can actually deliver."""
        return self.enabled and bool(self.chat_id)


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
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    content: ContentSettings = Field(default_factory=ContentSettings)
    goals: GoalSettings = Field(default_factory=GoalSettings)
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
