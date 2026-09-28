import json
import httpx
from config import settings

class Analyzer:
    def __init__(self):
        self.api_url = settings.LLAMA_API_URL
        self.api_key = settings.API_KEY
    
    def analyze(self, text: str) -> dict:
        prompt = self._load_prompt()
        schema = self._load_schema()
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Текст разговора:\n\n{text}"}
        ]
        
        payload = {
            "model": "llama",
            "messages": messages,
            "temperature": 0.1,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": schema
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        with httpx.Client(timeout=180.0) as client:
            response = client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_output": content}
    
    def _load_prompt(self) -> str:
        path = settings.PROMPTS_DIR / "analysis_prompt.txt"
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_schema(self) -> dict:
        path = settings.SCHEMAS_DIR / "analysis_schema.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)