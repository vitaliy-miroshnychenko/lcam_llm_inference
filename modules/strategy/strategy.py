from abc import ABC, abstractmethod


class Strategy(ABC):
    STRATEGY_NAME = None  # Should be specified in implementation
    TYPES_TO_CLASSIFY = ["рішення", "постанова", "окрема ухвала", "судовий наказ", "ухвала"]

    def set_config(self, config):
        self.config = config

    def set_classification_config(self, config):
        self.classification_config = config

    def set_documents(self, documents):
        self.documents = documents

    def set_categories(self, categories):
        self.categories = categories

    def set_storage(self, storage):
        self.storage = storage

    @abstractmethod
    def execute(self):
        """Execute the strategy."""
        pass
