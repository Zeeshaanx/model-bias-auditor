import re

_TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def normalize(text: str | None) -> str:
    return (text or "").strip().lower()


def tokenize(text: str | None) -> list[str]:
    return _TOKEN_PATTERN.findall(normalize(text))


def token_count(text: str | None) -> int:
    return len(tokenize(text))


def term_frequency(text: str | None, terms: list[str]) -> int:
    """Count how often any term from `terms` occurs. Multi-word terms are matched as substrings."""
    haystack = normalize(text)
    tokens = tokenize(text)
    counter = 0
    for term in terms:
        cleaned = normalize(term)
        if " " in cleaned:
            counter += haystack.count(cleaned)
        else:
            counter += tokens.count(cleaned)
    return counter


def rate_per_hundred_tokens(count: int, text: str | None) -> float:
    total = token_count(text)
    if total == 0:
        return 0.0
    return (count / total) * 100.0


def excerpt(text: str | None, limit: int = 400) -> str:
    cleaned = (text or "").strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3] + "..."
