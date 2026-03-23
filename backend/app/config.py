from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/colorfit"
    redis_url: str = "redis://localhost:6379"
    naver_client_id: str = ""
    naver_client_secret: str = ""
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
