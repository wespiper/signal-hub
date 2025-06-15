"""Configuration settings for Signal Hub."""

from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from pydantic import BaseSettings, Field, validator
from pydantic_settings import SettingsConfigDict

from signal_hub.core.features import Edition


class VectorStoreType(str, Enum):
    """Supported vector store types."""
    CHROMADB = "chromadb"
    PGVECTOR = "pgvector"


class ServerSettings(BaseSettings):
    """Server configuration settings."""
    
    host: str = Field("localhost", description="Server host")
    port: int = Field(3333, description="Server port")
    name: str = Field("Signal Hub", description="Server name")
    description: str = Field(
        "Intelligent MCP server for RAG-enhanced development",
        description="Server description"
    )
    
    # Health check endpoint
    health_check_enabled: bool = Field(True, description="Enable health check endpoint")
    health_check_path: str = Field("/health", description="Health check path")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(True, description="Enable rate limiting")
    requests_per_minute: int = Field(60, description="Max requests per minute per client")
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_SERVER_",
        env_file=".env",
        extra="ignore"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    level: str = Field("INFO", description="Logging level")
    format: str = Field("text", description="Log format (text or json)")
    file: Optional[Path] = Field(None, description="Log file path")
    rich_console: bool = Field(True, description="Use rich console for output")
    
    @validator("level")
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_LOG_",
        env_file=".env",
        extra="ignore"
    )


class VectorStoreSettings(BaseSettings):
    """Vector store configuration settings."""
    
    type: VectorStoreType = Field(
        VectorStoreType.CHROMADB,
        description="Vector store type"
    )
    
    # ChromaDB settings
    chroma_path: Path = Field(
        Path("./chroma_db"),
        description="ChromaDB storage path"
    )
    chroma_host: Optional[str] = Field(None, description="ChromaDB server host")
    chroma_port: Optional[int] = Field(None, description="ChromaDB server port")
    
    # PostgreSQL settings
    database_url: Optional[str] = Field(
        None,
        description="PostgreSQL connection URL"
    )
    
    # Common settings
    collection_name: str = Field("signal_hub", description="Collection name")
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_VECTOR_",
        env_file=".env",
        extra="ignore"
    )


class EmbeddingSettings(BaseSettings):
    """Embedding configuration settings."""
    
    provider: str = Field("openai", description="Embedding provider")
    model: str = Field("text-embedding-3-small", description="Embedding model")
    dimension: int = Field(1536, description="Embedding dimension")
    batch_size: int = Field(100, description="Batch size for embedding")
    
    # API keys (loaded from environment)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_EMBEDDING_",
        env_file=".env",
        extra="ignore"
    )


class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    enabled: bool = Field(True, description="Enable caching")
    ttl: int = Field(3600, description="Cache TTL in seconds")
    max_size_mb: int = Field(500, description="Maximum cache size in MB")
    similarity_threshold: float = Field(
        0.95,
        description="Similarity threshold for cache hits"
    )
    
    @validator("similarity_threshold")
    def validate_threshold(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_CACHE_",
        env_file=".env",
        extra="ignore"
    )


class ModelSettings(BaseSettings):
    """Model routing configuration settings."""
    
    default_model: str = Field(
        "claude-3-haiku-20240307",
        description="Default model for queries"
    )
    
    # Model thresholds for routing
    haiku_threshold: float = Field(0.3, description="Complexity threshold for Haiku")
    sonnet_threshold: float = Field(0.7, description="Complexity threshold for Sonnet")
    
    # API configuration
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    @validator("haiku_threshold", "sonnet_threshold")
    def validate_thresholds(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Thresholds must be between 0 and 1")
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_MODEL_",
        env_file=".env",
        extra="ignore"
    )


class Settings(BaseSettings):
    """Main Signal Hub configuration."""
    
    # Edition configuration
    edition: Edition = Field(Edition.BASIC, description="Signal Hub edition")
    early_access: bool = Field(False, description="Enable early access mode")
    license_key: Optional[str] = Field(None, description="License key for Pro/Enterprise")
    
    # Environment
    env: str = Field("development", description="Environment name")
    debug: bool = Field(False, description="Debug mode")
    
    # Sub-configurations
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    embeddings: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    
    # Plugin configuration
    plugins_enabled: List[str] = Field(
        default_factory=list,
        description="List of enabled plugins"
    )
    
    # Cost tracking
    track_costs: bool = Field(True, description="Track API costs")
    cost_alert_threshold: float = Field(
        100.0,
        description="Cost alert threshold in USD"
    )
    
    @validator("edition", pre=True)
    def parse_edition(cls, v: Any) -> Edition:
        if isinstance(v, str):
            return Edition(v.lower())
        return v
    
    @validator("early_access", pre=True)
    def parse_bool(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    def get_server_name(self) -> str:
        """Get server name with edition."""
        edition_str = "Basic" if self.edition == Edition.BASIC else self.edition.value.title()
        base_name = self.server.name
        
        if self.early_access:
            return f"{base_name} (Early Access)"
        else:
            return f"{base_name} {edition_str}"
    
    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_HUB_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )