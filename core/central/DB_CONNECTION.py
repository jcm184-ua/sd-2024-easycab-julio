import sqlite3
from contextlib import closing
import mariadb

DATABASE_USER = 'ec_central'
DATABASE_PASSWORD = 'sd2024_central'
DATABASE_IP = '127.0.0.1'
DATABASE_PORT = 3306
DATABASE = 'easycab'

def connDB():
    """
    Devuelve una conexión a la base de datos.
    """
    conexion = mariadb.connect(
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            host=DATABASE_IP,
            port=DATABASE_PORT,
            database=DATABASE)
    return conexion

def init_db():
    """
    Inicializa la base de datos con la tabla de taxis si no existe.
    """
    with closing(connDB()) as conn:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS taxis (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL
                )
            """)
