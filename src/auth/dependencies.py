from src.auth.service import fastapi_users

current_user = fastapi_users.current_user
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)