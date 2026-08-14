from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db: str = "ferry"
    postgres_user: str = "ferry"
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_password: str
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    secret_key: str

    public_url: str = "https://localhost"
    admin_email: str = "admin@ferry.local"
    admin_password: str = "admin"
    session_ttl_seconds: int = 86400
    max_session_ttl_seconds: int = 604800
    secure_cookie: bool = False
    rate_limit_max_attempts: int = 10
    rate_limit_window_seconds: int = 300

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: openssl rand -base64 32"
            )
        return v

    @field_validator("public_url")
    @classmethod
    def validate_public_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("PUBLIC_URL must start with http:// or https://")
        return v.rstrip("/")

    auto_register_resources: bool = True
    resource_manifest_dir: str = ""
    auto_register_environments: bool = True
    environment_manifest_dir: str = ""
    example_analysis_dir: str = ""
    template_dir: str = ""
    output_dir: str = "/var/lib/ferry/outputs"
    analysis_bundle_root: str = ""
    bundle_store_dir: str = "/var/lib/ferry/bundles"
    data_root: str = "/read-only-data"
    host_data_root: str = ""
    host_resource_manifest_dir: str = ""

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 120

    image_registry_prefix: str = "ferry/builds"

    release_dir: str = "/var/lib/ferry/releases"
    log_level: str = "INFO"

    execution_mem_limit: str = "4g"
    execution_cpu_limit: float = 2.0
    execution_pids_limit: int = 256
    max_output_size_mb: int = 1024

    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    smtp_from: str = "noreply@example.org"
    smtp_from_name: str = "FERRY"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
