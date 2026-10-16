import mysql.connector

from modules.storage.mysql_data_loader import MySQLDataLoader
from modules.ssh_db_connect import MysqlSSHConnector
from .storage import Storage
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MySQLStorage(Storage):
    def __init__(self, config):
        super().__init__(config)

    def configure(self, config):
        required_keys = ["host", "database", "results_table", "experiment_table"]
        missing = [key for key in required_keys if key not in config]
        if missing:
            raise ValueError(f"Missing required config keys: {', '.join(missing)}")
        host = config["host"]
        database = config["database"]
        user = config.get("user")
        password = config.get("password")
        # Fallback to environment variables if not provided
        if not user:
            user = os.environ.get("DB_USER")
        if password is None:
            password = os.environ.get("DB_PASSWORD")
        # Allow empty password if DB_PASSWORD exists but is empty
        if not user or password is None:
            raise ValueError(
                "MySQL user and password must be provided in config or as environment variables DB_USER and DB_PASSWORD.")
        self.results_table = config["results_table"]
        self.experiment_table = config["experiment_table"]
        self.request_log_table = config.get("request_log_table", "request_log")
        self.metric_table = "experiment_metric"

        self.establish_connection(host, user, password, database)

        # TODO: add here SSH

    def establish_connection(self, host, user, password, database):
        logger.info("Establishing connection with host {}".format(host))
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database, connect_timeout=5
            )
            self.cursor = self.conn.cursor()
        except mysql.connector.errors.DatabaseError:
            logger.info("Connection timeout error. Starting SSH tunnel")
            self.ssh_connector = MysqlSSHConnector()
            self.conn, self.cursor = self.ssh_connector.connection_and_cursor()

    def write_record(self, table, record):
        set_clauses = []
        values = []
        if table == "result":
            table = self.results_table
        elif table == "experiment":
            table = self.experiment_table
        elif table == "request_log":
            table = self.request_log_table
            record["experiment_id"] = self.experiment_id if hasattr(self, 'experiment_id') else None
        for key, value in record.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        set_str = ', '.join(set_clauses)
        sql = f"INSERT INTO {table} SET {set_str}"

        self.cursor.execute(sql, values)
        self.conn.commit()
        return self.cursor.lastrowid

    def update_experiment_record(self, experiment_id, record):
        set_clauses = []
        values = []
        for key, value in record.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        set_str = ', '.join(set_clauses)
        sql = f"UPDATE {self.experiment_table} SET {set_str} WHERE id = %s"
        values.append(experiment_id)

        self.cursor.execute(sql, values)
        self.conn.commit()

    def update_experiment_accuracy(self):
        """
        Update the accuracy of the experiment in the storage.
        This method should be called after all documents have been classified.
        """
        sql = "SELECT SUM(IF(INSTR(predicted_category, true_category), 1, 0))/COUNT(*) as full_accuracy, SUM(IF(INSTR(predicted_category, SUBSTR(true_category, 1,6)), 1, 0))/COUNT(*) as three_digits_accuracy FROM classification_result WHERE experiment_id=%s"
        print("Calculating experiment accuracy for experiment_id:", self.experiment_id, sql)
        self.cursor.execute(sql, (self.experiment_id,))
        result = self.cursor.fetchone()
        print("Experiment accuracy result:", result)
        if result:
            full_accuracy = result[0]
            three_digits_accuracy = result[1]
            sql = f"UPDATE {self.experiment_table} SET full_accuracy = %s, three_digits_accuracy = %s WHERE id = %s"
            print("Updating experiment accuracy:", full_accuracy, three_digits_accuracy, self.experiment_id)
            self.cursor.execute(sql, (full_accuracy, three_digits_accuracy, self.experiment_id))
        self.conn.commit()

    def load_experiment_record(self, experiment_id):
        """
        Load a single record from the experiment table by experiment_id, without using pandas.
        Returns a dict or None if not found.
        """
        sql = f"SELECT * FROM {self.experiment_table} WHERE id = %s LIMIT 1"
        self.cursor.execute(sql, (experiment_id,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))

    def load_experiment_data(self, experiment_id):
        """
        Load a single record from the experiment table by experiment_id, without using pandas.
        Returns a dict or None if not found.
        """
        sql = f"SELECT * FROM {self.results_table} WHERE experiment_id = %s"
        self.cursor.execute(sql, (experiment_id,))
        rows = self.cursor.fetchall()
        if rows is None:
            return None
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def save_metrics(self, metrics, experiment_id):
        """
        Save metrics into database
        """
        sql = f"INSERT INTO {self.metric_table} (experiment_id, name, value) VALUES "
        value_strings = []
        values = []
        for key in metrics.keys():
            value_strings.append("(%s, %s, %s)")
            values.extend([experiment_id, key, metrics[key]])

        sql += ",".join(value_strings)
        self.cursor.execute(sql, tuple(values))
        self.conn.commit()
        return True

    def cleanup_metrics(self, experiment_id):
        self.cursor.execute(f"DELETE FROM experiment_metric WHERE experiment_id='{int(experiment_id)}'")
        self.conn.commit()

    def load_data(self):
        # Load all documents
        experiment = self.load_experiment_record(self.experiment_id)
        dataLoader = MySQLDataLoader(self.cursor)
        return dataLoader.load_data(experiment, self.results_table, self.data_loading_mode)

    def load_taxonomy(self, parent_code=None):
        # Load root node(s)
        if parent_code is None:
            sql = "SELECT * FROM taxonomy WHERE title != '' AND parent_id IS NULL"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        else:
            # Find parent node by code
            sql = "SELECT id FROM taxonomy WHERE code = %s LIMIT 1"
            self.cursor.execute(sql, (parent_code,))
            parent_row = self.cursor.fetchone()
            if parent_row is None:
                return None
            parent_id = parent_row[0] if isinstance(parent_row, tuple) else parent_row['id']
            # Load children
            sql = "SELECT * FROM taxonomy WHERE parent_id = %s"
            self.cursor.execute(sql, (parent_id,))
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
