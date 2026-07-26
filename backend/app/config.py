from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://oj:oj@db:5432/oj"
    judge_image: str = "local-oj-runner:latest"
    judge_poll_interval: float = 1.0
    max_source_bytes: int = 128 * 1024
    max_test_file_bytes: int = 2 * 1024 * 1024
    seed_demo_data: bool = True
    import_408_questions: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
