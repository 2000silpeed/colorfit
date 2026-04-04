from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ColorFit API"
    debug: bool = False

    database_url: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""

    naver_client_id: str = ""
    naver_client_secret: str = ""

    gemini_api_key: str = ""
    fashn_api_key: str = ""

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7일

    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""

    frontend_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _validate_jwt_secret(self) -> "Settings":
        if self.jwt_secret_key == "":
            import warnings
            warnings.warn("JWT_SECRET_KEY is not set. Auth endpoints will not work.", stacklevel=2)
        return self

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
