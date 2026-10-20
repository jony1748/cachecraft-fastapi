from app.core.config import get_settings


def transform(value: str) -> str:
    """Simulated external transformer. Replace this adapter without changing persistence logic."""
    import time

    delay = get_settings().transformer_delay_seconds
    if delay:
        time.sleep(delay)
    return value.upper()
