import sqlite3
from contextlib import closing

DATABASE = './resources/database.db'

def connDB():
    """
    Devuelve una conexión a la base de datos. En el futuro, cambiar a MariaDB.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Para obtener resultados como diccionarios
    return conn

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
