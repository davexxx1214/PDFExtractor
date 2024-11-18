from openai import OpenAI
import json
from pathlib import Path

class OpenAIClient:
    def __init__(self):
        """
        Initialize OpenAI client with default config.json and prompt.txt
        """
        self.config = self._load_config()
        self.system_prompt = self._load_prompt()
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["api_base"]
        )
        
    def _load_config(self) -> dict:
        """Load configuration from config.json"""
        config_path = "config.json"
        try:
            if not Path(config_path).exists():
                raise FileNotFoundError("config.json not found. Please create it from config.json.example")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in config.json")
        except Exception as e:
            raise Exception(f"Configuration loading error: {str(e)}")

    def _load_prompt(self) -> str:
        """Load system prompt from prompt.txt"""
        prompt_path = "prompt.txt"
        try:
            if not Path(prompt_path).exists():
                raise FileNotFoundError("prompt.txt not found")
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Prompt loading error: {str(e)}")
    
    def process_text(self, text: str) -> str:
        """
        Process text content with OpenAI API
        
        Args:
            text (str): Text to process
            
        Returns:
            str: OpenAI API response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
