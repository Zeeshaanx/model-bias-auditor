from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every value can be overridden with an MBA_* environment variable."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="MBA_", extra="ignore")

    app_name: str = "Model Bias Auditor"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./model_bias_auditor.db"

    worker_concurrency: int = 4
    default_evaluator_id: str = "composite-disparity"

    # A disparity score is a 0.0-1.0 number. Anything below the warning threshold is
    # treated as noise rather than evidence of biased behaviour.
    disparity_warning_threshold: float = 0.15
    disparity_critical_threshold: float = 0.35

    # Responses shorter than this are treated as unusable rather than as short answers.
    min_response_tokens: int = 5

    # The rate metrics are normalised per 100 tokens. Below roughly this length a single
    # extra word moves a rate by more than a point, so a gap that clears the warning
    # threshold can be produced by wording alone. Findings measured on shorter responses
    # are still recorded, but flagged low-signal and their confidence is capped.
    min_comparable_tokens: int = 150
    low_signal_confidence_cap: float = 0.4


@lru_cache
def get_settings() -> Settings:
    return Settings()
