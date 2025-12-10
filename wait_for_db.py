import time
import psycopg2
from psycopg2 import OperationalError

while True:
    try:
        conn = psycopg2.connect(
            dbname="backendsti",
            user="backendsti",
            password="backendsti",
            host="db",
            port="5432"
        )
        conn.close()
        break
    except OperationalError:
        print("Waiting for database...")
        time.sleep(1)
