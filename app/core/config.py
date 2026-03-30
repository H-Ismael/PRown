import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PR Comprehension Gate"
    environment: str = "dev"
    api_base_url: str = "http://localhost:8000"

    database_url: str = "postgresql+psycopg2://prgate:prgate@postgres:5432/prgate"

    github_webhook_secret: str = ""
    github_token: str = ""

    llm_provider: str = "stub"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    llm_api_base: str = os.getenv("LLM_API_BASE", "")

    policy_dir: str = "policies"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
