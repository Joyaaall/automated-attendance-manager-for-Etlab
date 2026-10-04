import os
import secrets


class Config:
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    BASE_URL = os.environ.get("ETLAB_BASE_URL", "https://asiet.etlab.app").rstrip("/")
    COOKIE_KEY = os.environ.get("ETLAB_COOKIE_KEY", "ASIETSESSIONID")
    REQUEST_TIMEOUT = 20
    TOKEN_SECRET = os.environ.get("ETLAB_TOKEN_SECRET") or secrets.token_urlsafe(48)
    TOKEN_MAX_AGE = int(os.environ.get("ETLAB_TOKEN_MAX_AGE", "43200"))
