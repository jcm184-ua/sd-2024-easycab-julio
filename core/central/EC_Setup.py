
import sys
sys.path.append('../../shared')
from EC_Shared import *
import sqlite3

DATABASE = './resources/database.db'
SCRIPT = './resources/iniciarBBDD.sql'

def iniciarBBDD():
    conexionBBDD = sqlite3.connect(DATABASE)
    cursor = conexionBBDD.cursor()

    fd = open(SCRIPT, 'r')
    sqlFile = fd.read()
    fd.close()

    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        try:
            cursor.execute(command)
        except sqlite3.OperationalError as msg:
            printInfo("Command skipped: ")
            printInfo(msg)

    conexionBBDD.commit()
    conexionBBDD.close()

    printInfo("Base de datos preparada.")

def main():
    iniciarBBDD()

if __name__ == "__main__":
    main()