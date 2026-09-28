from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings:
    AUDIO_DIR = BASE_DIR / "data" / "audio"
    RESULTS_DIR = BASE_DIR / "results"
    PROMPTS_DIR = BASE_DIR / "prompts"
    SCHEMAS_DIR = BASE_DIR / "schemas"
    
    AUDIO_FILE = "conversation.wav"
    
    WHISPER_MODEL = "large-v3"
    WHISPER_DEVICE = "cpu"
    WHISPER_LANGUAGE = "ru"
    
    LLAMA_API_URL = "http://127.0.0.1:10000/v1/chat/completions"
    API_KEY = "8005"

settings = Settings()