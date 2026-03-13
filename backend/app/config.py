"""
Configuration management for the translation application.
"""
from pydantic_settings import BaseSettings
from typing import Dict, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./translation_app.db"
    
    # API Configuration
    api_title: str = "Real-Time Translation API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Admin Authentication
    admin_username: str = "admin"
    admin_password: str = "changeme123"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Model Paths
    vosk_model_path: str = "./models/vosk"
    piper_voice_path: str = "./models/piper"
    hf_cache_dir: str = "./models/huggingface"
    
    # Performance Settings
    max_concurrent_sessions: int = 20
    audio_chunk_duration_ms: int = 200
    stt_sample_rate: int = 16000
    
    # Cloud API Keys (optional)
    google_api_key: str = ""
    azure_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Language configuration with model mappings
LANGUAGE_CONFIG = {
    "en": {
        "name": "English",
        "vosk_model": "vosk-model-small-en-us-0.15",
        "tts_voices": {
            "female": "en_US-lessac-medium",
            "male": "en_US-ryan-medium"
        }
    },
    "hi": {
        "name": "Hindi",
        "vosk_model": "vosk-model-small-hi-0.22",
        "tts_voices": {
            "female": "hi_IN-female-medium",
            "male": "hi_IN-male-medium"
        }
    },
    "es": {
        "name": "Spanish",
        "vosk_model": "vosk-model-small-es-0.42",
        "tts_voices": {
            "female": "es_ES-female-medium",
            "male": "es_ES-male-medium"
        }
    },
    "fr": {
        "name": "French",
        "vosk_model": "vosk-model-small-fr-0.22",
        "tts_voices": {
            "female": "fr_FR-siwis-medium",
            "male": "fr_FR-tom-medium"
        }
    },
    "de": {
        "name": "German",
        "vosk_model": "vosk-model-small-de-0.15",
        "tts_voices": {
            "female": "de_DE-thorsten-medium",
            "male": "de_DE-thorsten-medium"
        }
    },
    "zh": {
        "name": "Chinese",
        "vosk_model": "vosk-model-small-cn-0.22",
        "tts_voices": {
            "female": "zh_CN-female-medium",
            "male": "zh_CN-male-medium"
        }
    },
    "ja": {
        "name": "Japanese",
        "vosk_model": "vosk-model-small-ja-0.22",
        "tts_voices": {
            "female": "ja_JP-female-medium",
            "male": "ja_JP-male-medium"
        }
    }
}

# Translation model mappings (Hugging Face)
TRANSLATION_MODELS = {
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
    ("en", "ja"): "Helsinki-NLP/opus-mt-en-jap",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("ja", "en"): "Helsinki-NLP/opus-mt-jap-en",
    # For unsupported pairs, we'll use M2M100
    ("fallback", "fallback"): "facebook/m2m100_418M"
}

# Get settings instance
settings = Settings()


def get_supported_language_pairs() -> List[Dict[str, str]]:
    """Get list of supported language pairs."""
    pairs = []
    for (source, target), model in TRANSLATION_MODELS.items():
        if source != "fallback" and target != "fallback":
            pairs.append({
                "source": source,
                "target": target,
                "source_name": LANGUAGE_CONFIG.get(source, {}).get("name", source),
                "target_name": LANGUAGE_CONFIG.get(target, {}).get("name", target),
                "model": model
            })
    return pairs


def get_translation_model(source_lang: str, target_lang: str) -> str:
    """Get the appropriate translation model for a language pair."""
    model = TRANSLATION_MODELS.get((source_lang, target_lang))
    if model:
        return model
    # Try reverse direction
    model = TRANSLATION_MODELS.get((target_lang, source_lang))
    if model:
        return model
    # Fallback to multilingual model
    return TRANSLATION_MODELS[("fallback", "fallback")]


def get_vosk_model_path(lang: str) -> str:
    """Get Vosk model path for a language."""
    lang_config = LANGUAGE_CONFIG.get(lang, {})
    model_name = lang_config.get("vosk_model", "vosk-model-small-en-us-0.15")
    return os.path.join(settings.vosk_model_path, model_name)


def get_tts_voice_path(lang: str, gender: str = "female") -> str:
    """Get Piper TTS voice path for a language."""
    lang_config = LANGUAGE_CONFIG.get(lang, {})
    voices = lang_config.get("tts_voices", {})
    voice_name = voices.get(gender, voices.get("female", "en_US-lessac-medium"))
    return os.path.join(settings.piper_voice_path, f"{voice_name}.onnx")
