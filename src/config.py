"""
config
"""
import os
from dotenv import load_dotenv
from typing import Optional

# load .env file
load_dotenv()


class Config:
    """base settings"""
    
    # LLM configuration
    # provider: OpenAI or Papyrus
    PROVIDER: str = os.getenv("PROVIDER", "papyrus").lower()
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5-chat-shortco-2025-08-07-eval")
    BASE_URL_OR_ENDPOINT = os.getenv("BASE_URL_OR_ENDPOINT", "https://westus2.papyrus.binginternal.com/chat/completions")
    # openai settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    # papyrus settings
    PAPYRUS_QUOTA_ID: Optional[str] = os.getenv("PAPYRUS_QUOTA_ID", "CoreSearch/BGM")
    PAPYRUS_TIMEOUT_MS = os.getenv("PAPYRUS_TIMEOUT_MS", "100000")
    PAPYRUS_VERIFY_SCOPE = os.getenv("PAPYRUS_VERIFY_SCOPE", "api://5fe538a8-15d5-4a84-961e-be66cd036687/.default")

    # retrieval settings
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    ARXIV_BASE_URL = "https://arxiv.org/api/query"
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # Web configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///research.db")
    
    # retrieval parameters
    SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", 10))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
    
    # storage configuration
    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    
    @classmethod
    def validate(cls) -> bool:
        """validate necessary configurations"""
        if not cls.OPENAI_API_KEY:
            print("warning: OPENAI_API_KEY not set")
            return False
        return True


class DevelopmentConfig(Config):
    """development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """testing configuration"""
    DEBUG = True
    DATABASE_URL = "sqlite:///:memory:"


def get_config() -> Config:
    """get configuration based on ENV variable"""
    env = os.getenv("ENV", "development")
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    return config_map.get(env, DevelopmentConfig)()
