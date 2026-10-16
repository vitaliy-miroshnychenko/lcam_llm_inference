import os
import json

from .mysql_storage import MySQLStorage
from modules.logger import Logger


class StorageFactory:
    DEFAULT_CONFIG = "etc/mysql-config.json"

    def get_storage(self, name="mysql", config=None):
        if name == "mysql" and config is None:

            logger = Logger()
            if not os.path.exists(StorageFactory.DEFAULT_CONFIG):
                logger.log(f"Config file '{self.DEFAULT_CONFIG}' does not exist.")
                raise FileNotFoundError("Can not find default mysql config")
            with open(StorageFactory.DEFAULT_CONFIG, 'r') as f:
                config = json.load(f)

        if name == "mysql":

            return MySQLStorage(config)
        else:
            raise ValueError(f"No storage available for name: {name}")
