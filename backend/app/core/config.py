from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, EmailStr


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_expires_seconds: int = Field(default=3600, alias="JWT_EXPIRES")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    costing_method: str = Field(default="LAST_PURCHASE", alias="COSTING_METHOD")
    discount_max_percent_line: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_LINE")
    discount_max_percent_receipt: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_RECEIPT")
    discount_max_amount_line: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_LINE")
    discount_max_amount_receipt: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_RECEIPT")
    allow_negative_stock: bool = Field(default=False, alias="ALLOW_NEGATIVE_STOCK")
    first_owner_email: EmailStr | None = Field(default=None, alias="FIRST_OWNER_EMAIL")
    first_owner_password: str | None = Field(default=None, alias="FIRST_OWNER_PASSWORD")
    bootstrap_token: str | None = Field(default=None, alias="BOOTSTRAP_TOKEN")
    cash_register_provider: str = Field(default="mock", alias="CASH_REGISTER_PROVIDER")
    default_cash_register_id: str | None = Field(default=None, alias="DEFAULT_CASH_REGISTER_ID")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
