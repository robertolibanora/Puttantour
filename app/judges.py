import os


def parse_admin_judges(raw: str | None) -> dict[str, str]:
    judges: dict[str, str] = {}
    if not raw:
        return judges
    for entry in raw.split(','):
        entry = entry.strip()
        if not entry or ':' not in entry:
            continue
        username, password = entry.split(':', 1)
        username = username.strip().lower()
        password = password.strip()
        if username and password:
            judges[username] = password
    return judges


def load_admin_judges() -> dict[str, str]:
    judges = parse_admin_judges(os.getenv('ADMIN_JUDGES'))
    if judges:
        return judges
    legacy_user = os.getenv('ADMIN_USERNAME', '').strip().lower()
    legacy_pass = os.getenv('ADMIN_PASSWORD', '')
    if legacy_user and legacy_pass:
        return {legacy_user: legacy_pass}
    return {'admin': 'admin123'}
