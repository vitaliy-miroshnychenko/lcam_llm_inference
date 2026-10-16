from .claude_adapter import ClaudeAdapter
from .openai_adapter import OpenaiAdapter
from .gemini_adapter import GeminiAdapter
from .ollama_adapter import OllamaAdapter


class AdapterFactory:
    @staticmethod
    def get_adapter(model_name, api_key=None, api_key_env=None, api_key_file=None):
        if model_name.startswith("claude"):
            return ClaudeAdapter(model_name, api_key, api_key_env, api_key_file)
        elif model_name.startswith('openai'):
            model = model_name.replace('openai-', '')
            return OpenaiAdapter(model, api_key, api_key_env, api_key_file)
        elif model_name.startswith('gemini'):
            model = model_name  # .replace('gemini-', '')
            return GeminiAdapter(model, api_key, api_key_env, api_key_file)
        elif (model_name.startswith('gemma3') or
              model_name.startswith('gemma4') or
              model_name.startswith('qwen3') or
              model_name.startswith('llama3.') or model_name.startswith('deepseek')): # Ollama case
            model = model_name  # .replace('gemini-', '')
            return OllamaAdapter(model, api_key, api_key_env, api_key_file)
        else:
            raise ValueError(f"No adapter available for model: {model_name}")
