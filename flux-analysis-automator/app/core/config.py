from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Flux Analysis Automator"
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    database_url: str = "postgresql+psycopg2://flux:flux@localhost:5432/flux_analysis"

    materiality_pct_threshold: float = 10.0
    materiality_absolute_threshold: float = 100_000_000.0

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    gemini_api_key: str = ""

    sec_user_agent: str = "FluxAnalysisAutomator contact@example.com"

    def materiality_metric_overrides(self) -> dict[str, dict[str, float]]:
        """Optional per-metric thresholds (extend via env JSON in future)."""
        return {
            "Net Income": {"pct": 10.0, "absolute": 50_000_000},
            "Total Assets": {"pct": 5.0, "absolute": 500_000_000},
        }

    def resolved_llm_api_key(self) -> str:
        return self.llm_api_key or self.openai_api_key or self.gemini_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
