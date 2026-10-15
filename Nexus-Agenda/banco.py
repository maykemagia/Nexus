import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def conectar_banco():

    conexao = mysql.connector.connect(
        host="localhost",
        port=3306,
        user="nexus_app",
        password=os.getenv("DB_PASSWORD"),
        database="Nexus_Agenda"
    )

    return conexao