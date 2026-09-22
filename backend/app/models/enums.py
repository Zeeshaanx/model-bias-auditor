from enum import StrEnum


class TargetProvider(StrEnum):
    MOCK = "mock"
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"


class AuditStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProtectedAttribute(StrEnum):
    GENDER = "gender"
    ETHNICITY = "ethnicity"
    AGE = "age"
    RELIGION = "religion"
    DISABILITY = "disability"
    SEXUAL_ORIENTATION = "sexual_orientation"
    SOCIOECONOMIC = "socioeconomic"
    NATIONALITY = "nationality"


class Jurisdiction(StrEnum):
    """Where a probe's names, situations and legal framing are valid.

    A probe is not portable across jurisdictions. A name that signals a minority
    group in Germany signals nothing in the United States, and the statute that
    makes the disparity actionable differs. CROSS is used only where the prompt
    contains no jurisdiction-specific signal.
    """

    US = "us"
    EU = "eu"
    CROSS = "cross"


class ReportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
