"""App configuration module."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    # SEC EDGAR Configuration
    # SEC mandates a specific User-Agent format: SampleCompany AdminContact@<sample company domain>.com
    sec_user_agent: str = "FinancialResearchAnalyst aadeshgund.2006@gmail.com"
    sec_request_timeout: int = 15
    
    # Optional News APIs
    finnhub_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    
    # LLM & Research Synthesis Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2
    openai_timeout: int = 45
    
    # Future Milestones
    database_url: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
