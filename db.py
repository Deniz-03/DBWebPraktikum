#Author Deniz Rahnefeld (409637)

import psycopg
from config import Config

#Hier wird mithilfe der Umgebungsvariablen aus config.py eine Verbindung zu der Datenbank hergestellt.
#Innerhalb des Projekts wird nur diese Methode verwendet, um die verbindung herzustellen.
def connect_to_db():
    conn = psycopg.connect(
        host=Config.DB_HOST,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )
    return conn