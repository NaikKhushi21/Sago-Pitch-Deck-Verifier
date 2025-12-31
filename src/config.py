"""
Configuration management for Sago Pitch Verifier
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment variables"""
    
    # LLM Configuration (Gemini)
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gemini-2.5-flash"))
    
    # Gmail Configuration
    gmail_address: Optional[str] = field(default_factory=lambda: os.getenv("GMAIL_ADDRESS"))
    gmail_app_password: Optional[str] = field(default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD"))
    report_recipient: Optional[str] = field(default_factory=lambda: os.getenv("REPORT_RECIPIENT"))
    
    # Investor Profile (for personalization)
    investor_name: str = field(default_factory=lambda: os.getenv("INVESTOR_NAME", "Investor"))
    investor_focus_areas: str = field(default_factory=lambda: os.getenv("INVESTOR_FOCUS_AREAS", "B2B SaaS, FinTech, AI/ML"))
    investment_stage: str = field(default_factory=lambda: os.getenv("INVESTMENT_STAGE", "Series A"))
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY must be set in .env file")
        return True


# Global config instance
config = Config()
