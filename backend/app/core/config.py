from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, EmailStr


class Settings(BaseSettings):
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    database_url: str = Field(alias="DATABASE_URL")
    alembic_ini_path: str = Field(default="alembic.ini", alias="ALEMBIC_INI_PATH")
    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_expires_seconds: int = Field(default=3600, alias="JWT_EXPIRES")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")
    costing_method: str = Field(default="LAST_PURCHASE", alias="COSTING_METHOD")
    discount_max_percent_line: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_LINE")
    discount_max_percent_receipt: float = Field(default=0, alias="DISCOUNT_MAX_PERCENT_RECEIPT")
    discount_max_amount_line: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_LINE")
    discount_max_amount_receipt: float = Field(default=0, alias="DISCOUNT_MAX_AMOUNT_RECEIPT")
    allow_negative_stock: bool = Field(default=False, alias="ALLOW_NEGATIVE_STOCK")
    first_owner_email: EmailStr | None = Field(
        default=None, alias="FIRST_OWNER_EMAIL", validation_alias="OWNER_EMAIL"
    )
    first_owner_password: str | None = Field(
        default=None, alias="FIRST_OWNER_PASSWORD", validation_alias="OWNER_PASSWORD"
    )
    bootstrap_token: str | None = Field(default=None, alias="BOOTSTRAP_TOKEN")
    auto_migrate_on_startup: bool = Field(default=False, alias="AUTO_MIGRATE_ON_STARTUP")
    auto_bootstrap_on_startup: bool = Field(default=False, alias="AUTO_BOOTSTRAP_ON_STARTUP")
    cash_register_provider: str = Field(default="mock", alias="CASH_REGISTER_PROVIDER")
    default_cash_register_id: str | None = Field(default=None, alias="DEFAULT_CASH_REGISTER_ID")
    root_domain: str = Field(default="", alias="ROOT_DOMAIN")
    platform_hosts: str = Field(default="", alias="PLATFORM_HOSTS")
    reserved_subdomains: str = Field(default="", alias="RESERVED_SUBDOMAINS")
    default_tenant_slug: str | None = Field(default=None, alias="DEFAULT_TENANT_SLUG")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def ALEMBIC_INI_PATH(self) -> str:
        return self.alembic_ini_path


settings = Settings()
