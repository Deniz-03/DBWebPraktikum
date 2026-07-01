#Author Peer Schulze (410246)
import db

# Auslesen aller Dozierenden für das Dropdown menü zum wechseln des verantwortlichen Dozierenden
def get_dozierenden():
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT d_id, vorname, nachname FROM dozierende ORDER BY nachname")
            return cur.fetchall()

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

# Bearbeiten von Themen. Wird so umgesetzt das alle nicht geänderten Werte automatisch durch das Template
# weitergegeben werden
def thema_bearbeiten(themen_id, titel, d_id, oberbegriff, beschreibung, semester, pdf_pfad):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET titel=%s, d_id=%s, oberbegriff=%s, beschreibung=%s, "
                        "semester=%s, pdf_pfad=%s WHERE themen_id=%s",
                        (titel, d_id, oberbegriff, beschreibung,semester, pdf_pfad, themen_id)
            )
        conn.commit()

# Anzeigen des Studenten der sich für das Seminarthema entschieden hat
def student_hinzufuegen(themen_id, s_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE seminarthema SET s_id=%s WHERE themen_id=%s",
                        (s_id, themen_id)
            )
        conn.commit()

# Namen und Link des Studierenden der später im Seminarthema angezeigt wird
def get_student_by_id(s_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s_id, vorname, nachname FROM studierende WHERE s_id=%s",
                        (s_id,))
            return cur.fetchone()




