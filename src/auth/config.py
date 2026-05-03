from src.config import settings

SECRET = settings.SECRET
REFRESH_SECRET = settings.SECRET_REFRESH
ACCESS_TOKEN_EXPIRE = 3600*24*7  # 7 days instead of 365