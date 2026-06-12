from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # The local demo's explicit config must not inherit unrelated machine-wide
        # provider endpoints, such as an Anthropic-compatible localhost proxy.
        return init_settings, dotenv_settings, env_settings, file_secret_settings

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_base_url: str = "https://api.anthropic.com"

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_project_url: str = ""

    clickhouse_host: str = ""
    clickhouse_port: int = 8443
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"
    clickhouse_secure: bool = True

    composio_api_key: str = ""
    composio_user_id: str = "margin-demo"
    slack_verification_channel_id: str = ""
    slack_finance_channel_id: str = ""

    demo_actions_enabled: bool = False
    audit_step_delay_ms: int = 180

    @property
    def slack_channel_id(self) -> str:
        return self.slack_verification_channel_id or self.slack_finance_channel_id


@lru_cache
def get_settings() -> Settings:
    return Settings()
