from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    fmcsa_api_key: str = ""
    api_key: str = "changeme"
    database_url: str = "sqlite:///./data/carrier_sales.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
