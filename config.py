#Author Deniz Rahnefeld (409637)


#Hier werden einmal alle Umgebungsvariablen geladen.
#Der Zugriff auf diese erfolgt nur innerhalb dieser Datei.
import os

class Config:
    try:
        DB_HOST = os.environ.get('DB_HOST', 'localhost')
        DB_NAME = os.environ.get('DB_NAME', 'postgres')
        DB_USER = os.environ['DB_USER']
        DB_PASSWORD = os.environ['DB_PASSWORD']

        SECRET_KEY = os.environ.get('SECRET_KEY', 'extremly_secret_key')
    except Exception as e:
        print("Probleme beim Laden der Umgegbungvariablen")