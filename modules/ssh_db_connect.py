from sshtunnel import SSHTunnelForwarder, create_logger
import logging
import pymysql
import socket
import pandas as pd

from etc.ssh_creds import *

logger = create_logger(loglevel=logging.INFO)


class MysqlSSHConnector:
    def __init__(self):
        self.tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USERNAME,
            ssh_pkey=SSH_PKEY,
            remote_bind_address=(DB_HOST, DB_PORT),
            logger=logger)
        self.tunnel.start()

        logger.info("SSH tunnel is ready")
        logger.info("SSH tunnel is ready at port {}".format(self.tunnel.local_bind_port))
        sock = socket.socket()
        sock.settimeout(5)
        try:
            sock.connect(('127.0.0.1', self.tunnel.local_bind_port))
            logger.info("Socket connected to MySQL port through tunnel!")
        except Exception as e:
            logger.info("Socket connection error:", e)
        finally:
            sock.close()

        logger.info("Starting MySql connection")
        self.conn = pymysql.connect(
            host='127.0.0.1',
            port=self.tunnel.local_bind_port,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        self.cursor = self.conn.cursor()

    def close(self):
        self.tunnel.close()

        try:
            self.conn.close()
        except:
            logger.warning("Connection was closed")

        try:
            self.cursor.close()
        except:
            logger.warning("Cursor was closed")

    def connection_and_cursor(self):
        return self.conn, self.cursor


if __name__ == '__main__':
    ssh_sql = MysqlSSHConnector()
    conn, cursor = ssh_sql.connection_and_cursor()

    query = "select * from html_documents limit 10"
    with conn:
        with cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            logger.info("Columns in table: {}".format(len(results[0])))
            field_names = [i[0] for i in cursor.description]

            pd.DataFrame(results, columns=field_names).to_csv("../examples/raw_storage/html_documents.csv")

    ssh_sql.close()
    logger.info("Example ends with SUCCESS")
