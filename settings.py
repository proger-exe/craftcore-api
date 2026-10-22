from dataclasses import dataclass
from simpleconfig import SimpleConfig

config = SimpleConfig()
config.parse(".env")


def _get_optional(key: str, default: str = "") -> str:
    """SimpleConfig.get() raises KeyError for unset keys; new optional settings
    shouldn't crash the app on import just because .env predates them."""
    try:
        return config.get(key)
    except KeyError:
        return default


@dataclass
class Settings:
    DB_USER: str = config.get("DB_USER")
    DB_HOST: str = config.get("DB_HOST")
    DB_NAME: str = config.get("DB_NAME")
    DB_PASS: str = config.get("DB_PASS")
    DEV_ID: int = config.int("DEV_ID") or 0

    # JWT service auth: proves *which backend service* is calling the API
    # (Telegram bot, Discord bot, admin panel, ...), independent of X-Player-ID.
    JWT_SECRET: str = _get_optional("JWT_SECRET")
    JWT_ALGORITHM: str = _get_optional("JWT_ALGORITHM") or "HS256"
    JWT_SERVICE_TOKEN_TTL_MINUTES: int = int(
        _get_optional("JWT_SERVICE_TOKEN_TTL_MINUTES") or 60
    )
    # "client_id:client_secret,client_id2:client_secret2" — one pair per trusted service.
    SERVICE_CREDENTIALS_RAW: str = _get_optional("SERVICE_CREDENTIALS")

    @property
    def service_credentials(self) -> dict:
        """Parse SERVICE_CREDENTIALS_RAW into {client_id: client_secret}."""
        creds = {}
        for pair in self.SERVICE_CREDENTIALS_RAW.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            client_id, secret = pair.split(":", 1)
            client_id, secret = client_id.strip(), secret.strip()
            if client_id and secret:
                creds[client_id] = secret
        return creds


settings = Settings()
