import os
import json
from modules.logger import Logger


class Config:
    model_name = None
    strategy_name = None
    api_key_env = None
    enable_citations = False
    storage_name = "mysql"
    storage_config = None

    MYSQL_CONFIG = "etc/mysql-config-local.json"

    def __init__(self):
        self.logger = Logger()

    def load_experiment_config(self, storage, experiment_id):
        experiment = storage.load_experiment_record(experiment_id)
        self.model_name = experiment['model']
        self.strategy_name = experiment['strategy']

        try:
            json_config = json.loads(experiment['config'])
            self.api_key_env = json_config.get('api_key_env', None)
            self.enable_citations = json_config.get('enable_citations', False)
        except:
            pass

    def get_api_key(self):
        if self.model_name is None:
            raise ValueError("Model is not set, can not obtain API key")

        if self.model_name.startswith('claude') or self.model_name.startswith('openai'):
            return

        if self.model_name.startswith("gemini"):
            with open('creds/gemini.txt', 'r') as f:
                api_key = f.read()[:-1]
            return api_key

        if (self.model_name.startswith("gemma3") or
                self.model_name.startswith("gemma4") or
                self.model_name.startswith("qwen3") or
                self.model_name.startswith("llama3.") or
                self.model_name.startswith("deepseek")):
            return 'ollama_api_key'

        raise ValueError("Incorrect model: " + self.model_name)

    def __getitem__(self, key):
        return getattr(self, key)
