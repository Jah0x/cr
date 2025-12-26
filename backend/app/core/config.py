from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_access_ttl_seconds: int = Field(default=3600, alias="JWT_ACCESS_TTL_SECONDS")
    jwt_refresh_ttl_seconds: int = Field(default=86400, alias="JWT_REFRESH_TTL_SECONDS")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    costing_method: str = Field(default="LAST_PURCHASE", alias="COSTING_METHOD")
    discount_max_percent_line: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_LINE")
    discount_max_percent_receipt: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_RECEIPT")
    discount_max_amount_line: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_LINE")
    discount_max_amount_receipt: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_RECEIPT")
    allow_negative_stock: bool = Field(default=False, alias="ALLOW_NEGATIVE_STOCK")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
