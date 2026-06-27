#Author Deniz Rahnefeld (409637)

import psycopg
from psycopg import rows
from config import Config

#Hier wird mithilfe der Umgebungsvariablen aus config.py eine Verbindung zu der Datenbank hergestellt.
#Innerhalb des Projekts wird nur diese Methode verwendet, um die verbindung herzustellen.
def connect_to_db():
    conn = psycopg.connect(
        host=Config.DB_HOST,
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        row_factory=psycopg.rows.dict_row
        # Diese Zeile sorgt dafür, dass fetchall/fetchone Listen von Dictionaries ausgibt statt Tupeln.
        # Das verbessert die Lesbarkeit und auch die Wartbarkeit des Projekts
        # Bspw. [{"id" : 1, "email": "althoff@uni-hildesheim.de", "passwort": "Passwort!123"}
        #      {"id" : 2, "email": "reusspa@uni-hildesheim.de", "passwort": "Passwort!123"]
        #
        #Zugriff funktioniert hier dann z.B. so:
        #result = cur.fetchone()
        #if result:  # Erst prüfen, ob es ein passendes Ergebnis gab.
        #   print(result['id']]) -> 1
        #
        #result = cur.fetchall()
        #if result:
        #   email = result[0]['email']
        #   print(email) -> althoff@uni-hildesheim.de
    )
    return conn