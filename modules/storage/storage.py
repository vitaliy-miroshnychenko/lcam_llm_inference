from abc import ABC, abstractmethod

class Storage(ABC):

    def __init__(self, config):
        self.config = config
        self.configure(config)

    def set_experiment_id(self, experiment_id):
        """Set the experiment ID for the storage instance."""
        self.experiment_id = experiment_id

    def set_data_loading_mode(self, mode):
        """Set the data loading mode"""
        self.data_loading_mode = mode

    @abstractmethod
    def load_experiment_record(self, experiment_id):
        """Load experiment record"""
        pass

    @abstractmethod
    def load_experiment_data(self, experiment_id):
        """Load experiment data"""
        pass
    
    @abstractmethod
    def update_experiment_accuracy(self):
        """Update the accuracy of the experiment in the storage."""
        pass

    @abstractmethod
    def update_experiment_record(self, experiment_id, record):
        pass

    @abstractmethod
    def configure(self, config):
        """Configure storage from config dict."""
        pass

    @abstractmethod
    def write_record(self, table, record):
        """Write a single record to the storage."""
        pass

    @abstractmethod
    def load_data(self, experiment_id = None):
        """Load data from storage. Should be implemented by subclasses."""
        pass

    @abstractmethod
    def load_taxonomy(self, parent_id = None):
        """Configure storage from config dict."""
        pass

    @abstractmethod
    def save_metrics(self, metrics, experiment_id):
        """Save metrics"""
        pass

    @abstractmethod
    def cleanup_metrics(self, experiment_id):
        """Cleanup metrics"""
        pass
    

    
