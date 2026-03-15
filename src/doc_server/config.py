from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://docserver:docserver@localhost:5438/docserver"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    upload_dir: str = "./storage"
    chunk_size: int = 512
    chunk_overlap: int = 50
    search_similarity_threshold: float = 0.3
    search_max_results: int = 20

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
