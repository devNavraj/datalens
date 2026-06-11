from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATALENS_", env_file=".env", extra="ignore")

    environment: str = "dev"

    # Object storage (MinIO locally, S3 in AWS — endpoint_url=None means real S3)
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_region: str = "ap-southeast-2"
    s3_bucket: str = "datalens"

    # Adzuna connector
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "au"
    adzuna_category: str = "it-jobs"
    adzuna_results_per_page: int = 50
    adzuna_max_pages: int = 5
