from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centrais da aplicação.
    Lê automaticamente do arquivo .env na raiz do backend.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "books"
    postgres_host: str = "localhost"
    postgres_port: int = 5433

    secret_key: str = "secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    google_books_api_key: str | None = None
    google_books_base_url: str = "https://www.googleapis.com/books/v1/volumes" 

    ollama_base_url: str = "http://localhost:11434"
    gemma_model: str = "gemma3:4b" # escolhido após teste A/B: 11x mais rápido que qwen3.5:4b
    # cabe 100% na GPU, com qualidade de justificativa equivalente
    
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

settings = Settings()

