from abc import ABC, abstractmethod
import os


class Adapter(ABC):
    DEFAULT_API_KEY_NAME = None  # Should be specified in implementation
    AVAILABLE_MODELS = []  # Should be specified in implementation
    MAX_TOKENS = 1000  # Default max tokens, can be overridden in execute method

    def __init__(self, model_name, api_key=None, api_key_env=None, api_key_file=None):
        self.set_model(model_name)
        # self.api_key = None
        if api_key:
            self.api_key = api_key
        elif api_key_env and os.getenv(api_key_env):
            self.api_key = os.getenv(api_key_env)
        elif api_key_file and os.path.exists(api_key_file):
            with open(api_key_file, 'r') as f:
                self.api_key = f.readline().strip()
        elif self.DEFAULT_API_KEY_NAME and os.getenv(self.DEFAULT_API_KEY_NAME):
            self.api_key = os.getenv(self.DEFAULT_API_KEY_NAME)
        else:
            raise ValueError(
                "API key not provided or found. Set it via argument, environment variable, file, or specify DEFAULT_API_KEY_NAME in implementation.")
        self.context = []
        self.messages = []

    def is_model_exist(self, model_name):
        """Check if the model exists in AVAILABLE_MODELS."""
        return model_name in self.AVAILABLE_MODELS

    def set_storage(self, storage):
        """Set the storage instance for the adapter."""
        self.storage = storage

    def set_model(self, model_name):
        """Set the model if it exists, otherwise raise an exception."""
        if not self.is_model_exist(model_name):
            raise ValueError(f"Model '{model_name}' does not exist in AVAILABLE_MODELS.")
        self.model_name = model_name

    def add_context(self, context):
        self.context.append(context)

    def add_message(self, message):
        self.messages.append(message)

    def set_max_tokens(self, max_tokens):
        """Set the maximum number of tokens for the model response."""
        self.MAX_TOKENS = max_tokens

    def reset(self):
        """Clear the context and messages."""
        self.context = []
        self.messages = []

    @abstractmethod
    def execute(self, document_id=None):
        """Execute a single call with the current messages and context."""
        pass

    @abstractmethod
    def execute_batch(self, messages):
        """Execute a batch of calls with a list of messages."""
        pass
