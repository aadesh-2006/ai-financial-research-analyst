import json
from typing import Any, List, Optional, Union
from pydantic import field_validator
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
    
    # LLM & Research Synthesis Configuration (Google Gemini)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.2
    gemini_timeout: int = 45
    
    # CORS Configuration (configurable for React/Vite dev servers, Vercel deployments, and Docker networks)
    cors_allowed_origins: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://localhost:80",
    ]
    
    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v_trimmed.split(",") if origin.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return v
    
    # Database Configuration (PostgreSQL / SQLite fallback for tests)
    database_url: str = "sqlite:///./data_cache/financial_analyst.db"
    database_echo: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
