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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
