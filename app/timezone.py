from datetime import datetime
from zoneinfo import ZoneInfo

ROME_TZ = ZoneInfo('Europe/Rome')
UTC = ZoneInfo('UTC')
_DATETIME_FORMATS = (
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
)


def _parse_db_datetime(value: str) -> datetime:
    cleaned = value.strip()
    if cleaned.endswith('Z'):
        cleaned = cleaned[:-1]
    try:
        parsed = datetime.fromisoformat(cleaned.replace(' ', 'T'))
    except ValueError:
        parsed = None
        for fmt in _DATETIME_FORMATS:
            try:
                parsed = datetime.strptime(cleaned, fmt)
                break
            except ValueError:
                continue
        if parsed is None:
            return value
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def format_rome_datetime(value: str | datetime | None, *, fmt: str = '%d/%m %H:%M') -> str:
    if value is None:
        return ''
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
    else:
        parsed = _parse_db_datetime(str(value))
        if isinstance(parsed, str):
            return parsed
        dt = parsed
    return dt.astimezone(ROME_TZ).strftime(fmt)


def now_rome() -> datetime:
    return datetime.now(ROME_TZ)
