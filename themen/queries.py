#Author Peer Schulze (410246)
import db

# Auslesen aller Dozierenden für das Dropdown menü zum wechseln des verantwortlichen Dozierenden
def get_dozierenden():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id, vorname, nachname FROM dozierende ORDER BY nachname")
            return cur.fetchall()

# Dozent mittels ID ermitteln
def get_dozent_by_id(d_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id, vorname, nachname FROM dozierende WHERE d_id=%s",
                        (d_id,))
            return cur.fetchone()

# Datenbank eintrag für ein neues Seminarthema
# Mit None sind alle Felder markiert die nicht verpflichtend sind
def thema_anlegen(titel, d_id, oberbegriff, beschreibung, s_id=None, semester=None, pdf_pfad=None):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO seminarthema (titel, d_id, oberbegriff, beschreibung, s_id,"
                        " semester, pdf_pfad) "
                        "VALUES(%s, %s, %s, %s, %s, %s, %s)",
                        (titel, d_id, oberbegriff, beschreibung, s_id, semester, pdf_pfad)
            )
        conn.commit()

# Holt das Seminarthema und alle dazugehörigen Attribute zu einer bestimmten Themen_id
def get_seminarthema(themen_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM seminarthema WHERE themen_id=%s",
                        (themen_id,))
            return cur.fetchone()

# Abfrage um alle seminarthemen für die Übersicht zu bekommen
def get_alle_seminarthemen():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT sem.themen_id, sem.titel, sem.semester, sem.status, "
                        "d.vorname AS doz_vorname, d.nachname AS doz_nachname "
                        "FROM seminarthema sem "
                        "JOIN dozierende d ON sem.d_id = d.d_id "
                        "ORDER BY sem.semester, sem.titel")
            return cur.fetchall()

# Bearbeiten von Themen. Wird so umgesetzt das alle nicht geänderten Werte automatisch durch das Template
# weitergegeben werden
def thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad, vorgetragen):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET titel=%s, d_id=%s, oberbegriff=%s, beschreibung=%s, "
                        "semester=%s, pdf_pfad=%s, vorgetragen=%s WHERE themen_id=%s",
                        (titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad, vorgetragen, themen_id)
            )
        conn.commit()

# Anzeigen des Studenten der sich für das Seminarthema entschieden hat
def student_hinzufuegen(themen_id, s_id, status):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET s_id=%s, status=%s WHERE themen_id=%s",
                        (s_id, status, themen_id)
            )
        conn.commit()

# Namen und Link des Studierenden der später im Seminarthema angezeigt wird
def get_student_by_id(s_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id, vorname, nachname FROM studierende WHERE s_id=%s",
                        (s_id,))
            return cur.fetchone()

# Alle eingetragenen s_ids die es in den Seminarthemen gibt
def get_sid_aus_themen():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id FROM seminarthema")
            return cur.fetchall()






# Abfrage für Test Seminarthema. Es wird eine d_id aus der Datenbank mittels LIMIT 1 gezogen
def get_test_dozent_id():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id FROM dozierende LIMIT 1")
            # fetchone speichert ein dictionary {'d_id', 3}
            result = cur.fetchone()
    # Rückgabe des Wertes der Dozierenden id
    return result['d_id']



